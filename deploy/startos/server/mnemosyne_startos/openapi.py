"""Hand-built OpenAPI 3.1 document for the REST API.

Request bodies come from the MCP tool definitions so the REST contract can
never drift from what the tools actually accept.
"""

from __future__ import annotations

import copy
from typing import Any

_ERROR = {"$ref": "#/components/schemas/Error"}
_RESULT = {"$ref": "#/components/schemas/ToolResult"}


def _schema_of(tool: dict[str, Any]) -> dict[str, Any]:
    # get_tool_definitions() emits ``input_schema``; the MCP wire name is
    # ``inputSchema``. Accept both so a rename upstream cannot silently
    # produce empty request bodies.
    return tool.get("input_schema") or tool.get("inputSchema") or {"type": "object"}


def _without(schema: dict[str, Any], prop: str) -> dict[str, Any]:
    """Copy of ``schema`` minus one property (used for path-supplied ids)."""
    out = copy.deepcopy(schema)
    out.get("properties", {}).pop(prop, None)
    if "required" in out:
        out["required"] = [r for r in out["required"] if r != prop]
        if not out["required"]:
            del out["required"]
    return out


def _responses(*codes: str) -> dict[str, Any]:
    descriptions = {
        "400": "Invalid or missing arguments",
        "401": "Missing or invalid bearer token",
        "404": "Unknown tool or memory not found",
        "500": "Tool failed",
    }
    out: dict[str, Any] = {
        "200": {
            "description": "Tool result, passed through unchanged",
            "content": {"application/json": {"schema": _RESULT}},
        }
    }
    for code in codes:
        out[code] = {
            "description": descriptions[code],
            "content": {"application/json": {"schema": _ERROR}},
        }
    return out


def _body(ref: str) -> dict[str, Any]:
    return {
        "required": True,
        "content": {"application/json": {"schema": {"$ref": ref}}},
    }


def _bank_param() -> dict[str, Any]:
    return {
        "name": "bank",
        "in": "query",
        "required": False,
        "schema": {"type": "string"},
        "description": "Memory bank (defaults to the server's default bank)",
    }


def _id_param() -> dict[str, Any]:
    return {
        "name": "memory_id",
        "in": "path",
        "required": True,
        "schema": {"type": "string"},
    }


def build_openapi(tools: list[dict[str, Any]], version: str) -> dict[str, Any]:
    schemas: dict[str, Any] = {
        "Error": {
            "type": "object",
            "properties": {"error": {"type": "string"}},
            "required": ["error"],
        },
        "ToolResult": {
            "type": "object",
            "additionalProperties": True,
            "description": "JSON object returned by the Mnemosyne tool.",
        },
    }
    names: list[str] = []
    for tool in tools:
        names.append(tool["name"])
        schemas[f"Args_{tool['name']}"] = _schema_of(tool)
    if "mnemosyne_update" in names:
        schemas["UpdateBody"] = _without(
            schemas["Args_mnemosyne_update"], "memory_id"
        )

    def has(name: str) -> bool:
        return name in names

    paths: dict[str, Any] = {
        "/healthz": {
            "get": {
                "summary": "Health check",
                "security": [],
                "responses": {
                    "200": {"description": "Default bank opens"},
                    "503": {"description": "Default bank cannot be opened"},
                },
            }
        },
        "/openapi.json": {
            "get": {
                "summary": "This document",
                "security": [],
                "responses": {"200": {"description": "OpenAPI 3.1 document"}},
            }
        },
        "/api/v1/tools": {
            "get": {
                "summary": "List MCP tool definitions",
                "responses": _responses("401"),
            }
        },
        "/api/v1/tools/{name}": {
            "post": {
                "summary": "Call any MCP tool; the JSON body is the tool arguments",
                "parameters": [
                    {
                        "name": "name",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string", "enum": names},
                    }
                ],
                "requestBody": {
                    "required": False,
                    "content": {
                        "application/json": {
                            "schema": {
                                "anyOf": [
                                    {"$ref": f"#/components/schemas/Args_{n}"}
                                    for n in names
                                ]
                            }
                        }
                    },
                },
                "responses": _responses("400", "401", "404", "500"),
            }
        },
    }

    # Convenience routes are only emitted for tools that exist, so the document
    # stays valid if a future Mnemosyne drops one.
    if has("mnemosyne_remember"):
        paths["/api/v1/memories"] = {
            "post": {
                "summary": "Remember (mnemosyne_remember)",
                "requestBody": _body("#/components/schemas/Args_mnemosyne_remember"),
                "responses": _responses("400", "401", "500"),
            }
        }
    if has("mnemosyne_recall"):
        paths["/api/v1/recall"] = {
            "post": {
                "summary": "Recall (mnemosyne_recall)",
                "requestBody": _body("#/components/schemas/Args_mnemosyne_recall"),
                "responses": _responses("400", "401", "500"),
            }
        }
    item: dict[str, Any] = {}
    if has("mnemosyne_get"):
        item["get"] = {
            "summary": "Get one memory (mnemosyne_get)",
            "parameters": [_id_param(), _bank_param()],
            "responses": _responses("401", "404", "500"),
        }
    if has("mnemosyne_update"):
        item["patch"] = {
            "summary": "Update a memory (mnemosyne_update)",
            "parameters": [_id_param()],
            "requestBody": _body("#/components/schemas/UpdateBody"),
            "responses": _responses("400", "401", "404", "500"),
        }
    if has("mnemosyne_forget"):
        item["delete"] = {
            "summary": "Forget a memory (mnemosyne_forget)",
            "parameters": [_id_param(), _bank_param()],
            "responses": _responses("401", "404", "500"),
        }
    if item:
        paths["/api/v1/memories/{memory_id}"] = item
    if has("mnemosyne_stats"):
        paths["/api/v1/stats"] = {
            "get": {
                "summary": "Stats (mnemosyne_stats)",
                "parameters": [_bank_param()],
                "responses": _responses("401", "500"),
            }
        }
    if has("mnemosyne_batch"):
        paths["/api/v1/batch"] = {
            "post": {
                "summary": "Atomic batch (mnemosyne_batch)",
                "requestBody": _body("#/components/schemas/Args_mnemosyne_batch"),
                "responses": _responses("400", "401", "500"),
            }
        }

    return {
        "openapi": "3.1.0",
        "info": {
            "title": "Mnemosyne REST API",
            "version": version,
            "description": (
                "REST access to the same tools the /mcp endpoint serves. "
                "Memories are attributed to the name of the bearer token used."
            ),
        },
        "security": [{"bearerAuth": []}],
        "paths": paths,
        "components": {
            "securitySchemes": {"bearerAuth": {"type": "http", "scheme": "bearer"}},
            "schemas": schemas,
        },
    }
