"""One ASGI app: /healthz, /openapi.json, /api/v1/* (REST) and /mcp (MCP)."""

from __future__ import annotations

import asyncio
import contextvars
import json
import logging
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Optional

import anyio
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

import mnemosyne
from mnemosyne.mcp_server import (
    _BearerTokenMiddleware,
    _build_streamable_http_app,
    _resolve_multi_tokens,
)
from mnemosyne.mcp_tools import get_tool_definitions, handle_tool_call

from .openapi import build_openapi

logger = logging.getLogger(__name__)

_REST_PREFIX = "/api/v1"
_PUBLIC_PATHS = frozenset({"/healthz", "/openapi.json"})
# Batch failures are the only structured ``status: error`` results the MCP
# handler treats as errors; map them the same way.
_BATCH_CLIENT_ERROR = "batch_validation_failed"


def _json(content: Any, status: int = 200) -> Response:
    # default=str matches the MCP handler's serialisation of datetimes etc.
    return Response(
        json.dumps(content, default=str),
        status_code=status,
        media_type="application/json",
    )


def _error(message: str, status: int) -> Response:
    return _json({"error": message}, status)


def _status_for(result: Any) -> int:
    """HTTP status implied by a tool result (handlers never raise for these)."""
    if not isinstance(result, dict):
        return 200
    status = result.get("status")
    if status == "not_found":
        return 404
    if status == "error":
        return 400 if result.get("error") == _BATCH_CLIENT_ERROR else 500
    if status is None and isinstance(result.get("error"), str):
        return 400
    return 200


class _Rest:
    """REST routes; every one is a thin wrapper over ``handle_tool_call``."""

    def __init__(self) -> None:
        self._tools = get_tool_definitions()
        self._names = {t["name"] for t in self._tools}
        # A single worker thread keeps tool calls serialised like the MCP
        # handler (which runs them inline on the event loop) and keeps one
        # cached SQLite connection per database, while freeing the loop so
        # /healthz and MCP traffic stay responsive during slow recalls.
        self._pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="rest-tool")

    async def _invoke(self, name: str, args: dict[str, Any]) -> Response:
        if name not in self._names:
            return _error(f"unknown tool: {name}", 404)
        # The bearer middleware set the author contextvar in this task; run the
        # call in a copy of the context so the worker thread sees it.
        ctx = contextvars.copy_context()
        loop = asyncio.get_running_loop()
        try:
            result = await loop.run_in_executor(
                self._pool, ctx.run, handle_tool_call, name, args
            )
        except KeyError as exc:
            return _error(f"missing required argument: {exc.args[0]}", 400)
        except (ValueError, TypeError) as exc:
            return _error(str(exc), 400)
        except Exception as exc:  # noqa: BLE001 — mirror the MCP handler's catch-all
            logger.exception("tool %s failed", name)
            return _error(str(exc), 500)
        return _json(result, _status_for(result))

    @staticmethod
    async def _args(request: Request) -> Optional[dict[str, Any]]:
        raw = await request.body()
        if not raw.strip():
            return {}
        try:
            body = json.loads(raw)
        except ValueError:
            return None
        return body if isinstance(body, dict) else None

    async def _call_with_body(self, request: Request, name: str) -> Response:
        args = await self._args(request)
        if args is None:
            return _error("request body must be a JSON object", 400)
        return await self._invoke(name, args)

    @staticmethod
    def _bank(request: Request) -> dict[str, Any]:
        bank = request.query_params.get("bank")
        return {"bank": bank} if bank else {}

    async def list_tools(self, request: Request) -> Response:
        return _json({"tools": self._tools})

    async def call_tool(self, request: Request) -> Response:
        return await self._call_with_body(request, request.path_params["name"])

    async def remember(self, request: Request) -> Response:
        return await self._call_with_body(request, "mnemosyne_remember")

    async def recall(self, request: Request) -> Response:
        return await self._call_with_body(request, "mnemosyne_recall")

    async def batch(self, request: Request) -> Response:
        return await self._call_with_body(request, "mnemosyne_batch")

    async def get(self, request: Request) -> Response:
        args = {"memory_id": request.path_params["memory_id"], **self._bank(request)}
        return await self._invoke("mnemosyne_get", args)

    async def update(self, request: Request) -> Response:
        args = await self._args(request)
        if args is None:
            return _error("request body must be a JSON object", 400)
        # The path id wins over any memory_id in the body.
        args["memory_id"] = request.path_params["memory_id"]
        return await self._invoke("mnemosyne_update", args)

    async def forget(self, request: Request) -> Response:
        args = {"memory_id": request.path_params["memory_id"], **self._bank(request)}
        return await self._invoke("mnemosyne_forget", args)

    async def stats(self, request: Request) -> Response:
        return await self._invoke("mnemosyne_stats", self._bank(request))

    def app(self) -> Starlette:
        p = _REST_PREFIX
        return Starlette(
            routes=[
                Route(f"{p}/tools", self.list_tools, methods=["GET"]),
                Route(f"{p}/tools/{{name}}", self.call_tool, methods=["POST"]),
                Route(f"{p}/memories", self.remember, methods=["POST"]),
                Route(f"{p}/recall", self.recall, methods=["POST"]),
                Route(f"{p}/memories/{{memory_id}}", self.get, methods=["GET"]),
                Route(f"{p}/memories/{{memory_id}}", self.update, methods=["PATCH"]),
                Route(f"{p}/memories/{{memory_id}}", self.forget, methods=["DELETE"]),
                Route(f"{p}/stats", self.stats, methods=["GET"]),
                Route(f"{p}/batch", self.batch, methods=["POST"]),
            ],
            exception_handlers={HTTPException: _http_exception},
        )


async def _http_exception(request: Request, exc: HTTPException) -> Response:
    return _error(str(exc.detail), exc.status_code)


def _probe_default_bank() -> None:
    from mnemosyne.core.banks import get_bank_db_path_read_only

    path = get_bank_db_path_read_only("default")
    conn = sqlite3.connect(str(path), timeout=2.0)
    try:
        conn.execute("SELECT 1 FROM sqlite_master LIMIT 1").fetchall()
    finally:
        conn.close()


def _public_app() -> Starlette:
    openapi = build_openapi(get_tool_definitions(), mnemosyne.__version__)

    async def healthz(request: Request) -> Response:
        try:
            await anyio.to_thread.run_sync(_probe_default_bank)
        except Exception as exc:  # noqa: BLE001 — any failure means unhealthy
            logger.warning("health check failed: %s", exc)
            return _json({"status": "unavailable", "error": str(exc)}, 503)
        return _json({"status": "ok", "version": mnemosyne.__version__})

    async def openapi_json(request: Request) -> Response:
        return _json(openapi)

    return Starlette(
        routes=[
            Route("/healthz", healthz, methods=["GET"]),
            Route("/openapi.json", openapi_json, methods=["GET"]),
        ]
    )


class _Dispatcher:
    """Plain ASGI path router.

    Everything not claimed by the public or REST apps, including the ASGI
    ``lifespan`` scope, goes to the MCP app: it owns the session manager that
    must start and stop with the server.
    """

    def __init__(self, public_app, rest_app, mcp_app) -> None:
        self._public = public_app
        self._rest = rest_app
        self._mcp = mcp_app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] == "http":
            path = scope["path"]
            if path in _PUBLIC_PATHS:
                await self._public(scope, receive, send)
                return
            if path == _REST_PREFIX or path.startswith(_REST_PREFIX + "/"):
                await self._rest(scope, receive, send)
                return
        await self._mcp(scope, receive, send)


def build_app(host: str = "0.0.0.0", mcp_path: str = "/mcp"):
    """Build the combined app. Raises RuntimeError when it must not start."""
    tokens = _resolve_multi_tokens()
    if not tokens:
        raise RuntimeError(
            "MNEMOSYNE_MCP_TOKENS is unset or empty; refusing to start without "
            'at least one agent token (a JSON object like {"agent": "secret"}).'
        )

    # Raises on a missing Host policy or auth setup: same fail-closed rules as
    # `mnemosyne mcp --transport streamable-http`.
    mcp_app = _build_streamable_http_app(host=host, path=mcp_path)

    # Fail at startup, not on the first request, if the data directory is
    # unusable; this also creates the default bank so /healthz is green.
    from mnemosyne.mcp_tools import _create_instance

    _create_instance(bank="default")

    rest_app = _BearerTokenMiddleware(_Rest().app(), tokens=tokens)
    return _Dispatcher(_public_app(), rest_app, mcp_app)
