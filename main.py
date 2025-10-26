# ============================================================================
# main.py - Application entry point
# ============================================================================

import locale

locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

from fastapi import FastAPI
import logging
from services.ledger_service import LedgerService
from controllers.ledger_controller import create_ledger_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create FastAPI app
app = FastAPI(
    title="Ledger API",
    version="1.0.0",
    description="REST API for ledger-cli operations"
)

# Initialize service
ledger_service = LedgerService('/home/felipe/ledger-data/main.ledger')

# Create and include router
ledger_router = create_ledger_router(ledger_service)
app.include_router(ledger_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
