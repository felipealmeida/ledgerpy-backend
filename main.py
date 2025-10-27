# ============================================================================
# main.py - Application entry point
# ============================================================================

import os
import logging
import argparse

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.ledger_service import LedgerService
from controllers.ledger_controller import create_ledger_router

DEFAULT_JOURNAL = "/app/ledger-data/main.ledger"


def create_app(journal_path: str | None = None) -> FastAPI:
    """
    App factory. If journal_path is None, resolve from env or default.
    This is safe for uvicorn --factory usage.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    resolved = journal_path or os.getenv("LEDGER_JOURNAL_FILE", DEFAULT_JOURNAL)
    logging.info("Using journal file: %s", resolved)

    app = FastAPI(
        title="Ledger API",
        version="1.0.0",
        description="REST API for ledger-cli operations",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize service only now (after path is final)
    ledger_service = LedgerService(resolved)
    ledger_router = create_ledger_router(ledger_service)
    app.include_router(ledger_router)
    return app


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Ledger API server.")
    parser.add_argument(
        "-j", "--journal",
        dest="journal",
        metavar="PATH",
        help=f"Path to ledger journal file (default: env LEDGER_JOURNAL_FILE or {DEFAULT_JOURNAL})",
    )
    parser.add_argument(
        "--host", default="0.0.0.0",
        help="Server host (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port", type=int, default=3000,
        help="Server port (default: 3000)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    app = create_app(args.journal)

    import uvicorn
    uvicorn.run(app, host=args.host, port=args.port)
