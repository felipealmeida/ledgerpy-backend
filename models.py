# ============================================================================
# models.py - Pydantic models for request/response types
# ============================================================================

from pydantic import BaseModel, Field, PrivateAttr
from typing import Optional, List, Dict
import ledger

class LedgerAccount(BaseModel):
    account: str
    full_path: str = Field(alias="fullPath")
    amounts: Dict[str, str]
    cleared_amounts: Dict[str, str] = Field(alias="clearedAmounts")
    last_cleared_date: Optional[str] = Field(None, alias="lastClearedDate")
    _amount_values: Dict[str, ledger.Value] = PrivateAttr(default = [])
    _cleared_amount_values: Dict[str, ledger.Value] = PrivateAttr(default = [])

    def get_amount_values(self) -> Dict[str, ledger.Value]:
        return self._amount_values
    def get_cleared_amount_values(self) -> Dict[str, ledger.Value]:
        return self._cleared_amount_values

    children: List['LedgerAccount'] = Field(default_factory=list)

    class Config:
        populate_by_name = True

    @classmethod
    def with_amount_values(
        cls,
        *,
        amount_values: Dict[str, ledger.Value],
        cleared_amount_values: Dict[str, ledger.Value],
        **data
    ) -> "LedgerAccount":
        obj = cls(**data)
        obj._amount_values = amount_values
        obj._cleared_amount_values = cleared_amount_values
        return obj

class LedgerPrice(BaseModel):
    what: str
    amounts: Dict[str, str]
    is_commodity: bool

class LedgerPriceResponse(BaseModel):
    prices: List[LedgerPrice]
    timestamp: str

class LedgerBalanceResponse(BaseModel):
    account: LedgerAccount
    timestamp: str

class LedgerTransactionNode(BaseModel):
    date: str
    description: str
    amount: float
    formatted_amount: str = Field(alias="formattedAmount")
    running_balance: float = Field(alias="runningBalance")
    formatted_running_balance: str = Field(alias="formattedRunningBalance")

    class Config:
        populate_by_name = True


class LedgerTransactionResponse(BaseModel):
    transactions: List[LedgerTransactionNode]
    account: str
    period: Optional[str]
    timestamp: str


class LedgerSubTotalNode(BaseModel):
    description: str
    inflow_amount: float = Field(alias="inflowAmount")
    outflow_amount: float = Field(alias="outflowAmount")
    running_balance: float = Field(alias="runningBalance")

    class Config:
        populate_by_name = True


class LedgerSubTotalsResponse(BaseModel):
    subtotals: List[LedgerSubTotalNode]
    period: Optional[str]
    timestamp: str


class BudgetItem(BaseModel):
    account: str
    full_path: str = Field(alias="fullPath")
    actual_amount: float = Field(alias="actualAmount")
    budget_amount: float = Field(alias="budgetAmount")
    variance: float
    variance_percentage: float = Field(alias="variancePercentage")
    formatted_actual: str = Field(alias="formattedActual")
    formatted_budget: str = Field(alias="formattedBudget")
    formatted_variance: str = Field(alias="formattedVariance")
    is_over_budget: bool = Field(alias="isOverBudget")

    class Config:
        populate_by_name = True


class BudgetResponse(BaseModel):
    budget_items: List[BudgetItem] = Field(alias="budgetItems")
    total_actual: float = Field(alias="totalActual")
    total_budget: float = Field(alias="totalBudget")
    total_variance: float = Field(alias="totalVariance")
    period: str
    timestamp: str

    class Config:
        populate_by_name = True

