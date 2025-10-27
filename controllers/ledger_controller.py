# ============================================================================
# controllers/ledger_controller.py - FastAPI route handlers
# ============================================================================

from fastapi import APIRouter, HTTPException, Query, Path
from services.ledger_service import LedgerService
from models import (
    LedgerBalanceResponse,
    LedgerTransactionResponse,
    LedgerSubTotalsResponse,
    BudgetResponse,
    )
from typing import Optional
from datetime import date

router = APIRouter(prefix="/api", tags=["ledger"])


def create_ledger_router(ledger_service: LedgerService) -> APIRouter:
    """Factory function to create router with injected service"""
    
    @router.get("/balance", response_model=LedgerBalanceResponse)
    async def get_balance(
            before: Optional[date] = Query(None, description="Format: YYYY-MM-DD"),
            after: Optional[date] = Query(None, description="Format: YYYY-MM-DD"),
    ):
        """Get balance for all accounts"""
        return ledger_service.get_balance(after, before)

    # @router.get("/balance/{account}", response_model=LedgerBalanceResponse)
    # async def get_account_balance(
    #     account: str = Path(..., description="Account name"),
    #     period: Optional[str] = Query(None, description="Period filter")
    # ):
    #     """Get balance for specific account"""
    #     if not account or not account.strip():
    #         raise HTTPException(status_code=400, detail="Account parameter is required")
    #     return ledger_service.get_account_balance(account, period)

    # @router.get("/transactions/{account}", response_model=LedgerTransactionResponse)
    # async def get_account_transactions(
    #     account: str = Path(..., description="Account name"),
    #     period: Optional[str] = Query(None, description="Period filter")
    # ):
    #     """Get transactions for specific account"""
    #     return ledger_service.get_account_transactions(account, period)

    # @router.get("/cash-flow", response_model=LedgerSubTotalsResponse)
    # async def get_cash_flow(
    #     period: Optional[str] = Query(None, description="Period filter")
    # ):
    #     """Get cash flow for all accounts"""
    #     return ledger_service.get_cash_flow(period)

    # @router.get("/cash-flow/{account}", response_model=LedgerSubTotalsResponse)
    # async def get_account_cash_flow(
    #     account: str = Path(..., description="Account name"),
    #     period: Optional[str] = Query(None, description="Period filter")
    # ):
    #     """Get cash flow for specific account"""
    #     if not account or not account.strip():
    #         raise HTTPException(status_code=400, detail="Account parameter is required")
    #     return ledger_service.get_cash_flow(period)

    # @router.get("/budget", response_model=BudgetResponse)
    # async def get_budget_report(
    #     period: Optional[str] = Query(None, description="Period for the budget report")
    # ):
    #     """Get budget vs actual spending report"""
    #     return ledger_service.get_budget_report(period)

    @router.get("/health")
    async def get_health():
        """Health check endpoint"""
        return {
            "status": "OK",
            "timestamp": datetime.now().isoformat(),
            "service": "ledger-api"
        }
    
    return router
