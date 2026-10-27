"""CLI entry point: ``mnemosyne-startos-server --host 0.0.0.0 --port 8080``."""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Optional


def main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(prog="mnemosyne-startos-server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s:     %(name)s: %(message)s"
    )

    import uvicorn

    from mnemosyne_startos.app import build_app

    try:
        app = build_app(host=args.host)
    except RuntimeError as exc:
        # Fail closed with the reason on stderr instead of a traceback.
        print(f"mnemosyne-startos-server: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    # proxy_headers off: StartOS terminates TLS in front, and trusting
    # X-Forwarded-* from a client would let it spoof its address in logs.
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="info",
        proxy_headers=False,
    )


if __name__ == "__main__":
    main()
