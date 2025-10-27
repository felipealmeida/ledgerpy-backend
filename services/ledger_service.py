# ============================================================================
# services/ledger_service.py - Core ledger business logic
# ============================================================================

from fastapi import HTTPException
from typing import Optional, List
import datetime
from models import (
    LedgerAccount,
    LedgerBalanceResponse,
    LedgerTransactionResponse,
    LedgerTransactionNode,
    LedgerSubTotalNode,
    LedgerSubTotalsResponse,
    BudgetItem,
    BudgetResponse,
    )
import ledger
import logging
import traceback
from typing import Dict

logger = logging.getLogger(__name__)


class LedgerService:
    def __init__(self, ledger_file_path: str = "/home/felipe/ledger-data/main.ledger"):
        self.ledger_file_path = ledger_file_path
        self.session = None
        self._initialize_session()

    def _initialize_session(self):
        """Initialize ledger session"""
        try:
            self.session = ledger.Session()
            #journal = self.session.read_journal_from_string("")
            self.journal = ledger.read_journal(self.ledger_file_path)
            logger.info(f"Successfully initialized ledger session with {self.ledger_file_path}")
        except Exception as e:
            logger.error(f"Failed to initialize ledger session: {e}")
            raise

    def _get_journal(self):
        """Get or create journal instance"""
        if not self.session:
            self._initialize_session()
        return self.journal

    def _format_amount(self, amount) -> tuple[float, str]:
        """Format ledger amount to float and string"""
        if hasattr(amount, 'to_double'):
            value = float(amount.to_double())
        else:
            value = float(amount)
        
        formatted = f"BRL {value:,.2f}"
        return value, formatted

    # def _build_account_tree(self, flat_accounts: List[LedgerAccount]) -> List[LedgerAccount]:
    #     """Build hierarchical tree from flat account list"""
    #     tree = []
    #     node_map = {}
        
    #     # Create all nodes
    #     for account in flat_accounts:
    #         node = LedgerAccount(
    #             account=account.account,
    #             fullPath=account.full_path,
    #             amountStr=account.amountStr,
    #             #formattedAmount=account.formatted_amount,
    #             #clearedAmount=account.cleared_amount,
    #             #formattedClearedAmount=account.formatted_cleared_amount,
    #             lastClearedDate=account.last_cleared_date,
    #             children=[],
    #             hasChildren=False
    #         )
    #         node_map[account.full_path] = node
        
    #     # Build tree structure
    #     for account in flat_accounts:
    #         node = node_map[account.full_path]
    #         path_parts = account.full_path.split(':')
            
    #         if len(path_parts) == 1:
    #             tree.append(node)
    #         else:
    #             parent_path = ':'.join(path_parts[:-1])
    #             parent_node = node_map.get(parent_path)
                
    #             if parent_node:
    #                 parent_node.children.append(node)
    #                 parent_node.has_children = True
    #             else:
    #                 tree.append(node)
        
    #     return tree

    def _read_budget_from_file(self) -> dict:
        """
        Read budget entries directly from the ledger file.
        Parses automated transactions (~ or =) and periodic transactions marked with tags.
        """
        budgets = {}
        
        try:
            with open(self.ledger_file_path, 'r', encoding='utf-8') as f:
                in_automated_transaction = False
                current_predicate = None
                
                for line in f:
                    stripped = line.strip()
                    
                    # Detect automated transactions
                    if stripped.startswith('~') or stripped.startswith('='):
                        in_automated_transaction = True
                        current_predicate = stripped
                        continue
                    
                    # Empty line ends automated transaction block
                    if in_automated_transaction and not stripped:
                        in_automated_transaction = False
                        current_predicate = None
                        continue
                    
                    # Parse posting lines in automated transactions
                    if in_automated_transaction and stripped and not stripped.startswith(';'):
                        # Match account and amount
                        parts = stripped.split()
                        if len(parts) >= 2:
                            account = parts[0].strip('[]')
                            
                            # Find amount
                            amount_str = None
                            for i, part in enumerate(parts[1:], 1):
                                if part.upper() == 'BRL' and i + 1 < len(parts):
                                    amount_str = parts[i + 1]
                                    break
                                elif part.replace(',', '').replace('.', '').replace('-', '').isdigit():
                                    amount_str = part
                                    break
                            
                            if amount_str:
                                try:
                                    amount = abs(float(amount_str.replace(',', '')))
                                    if account not in budgets:
                                        budgets[account] = 0.0
                                    budgets[account] += amount
                                    logger.info(f"Found budget: {account} = {amount}")
                                except ValueError:
                                    continue
                
        except FileNotFoundError:
            logger.warning(f"Ledger file not found: {self.ledger_file_path}")
        except Exception as e:
            logger.error(f"Error reading budget from file: {e}")
        
        return budgets

    def get_account_balance(self, account: ledger.Account,
                            before: Optional[datetime.date], after: Optional[datetime.date]) -> LedgerAccount:
        print(f'account name {account.fullname()}')
        amounts : Dict[str, Value] = {}
        cleared_amounts : Dict[str, Value] = {}
        children : [LedgerAccount] = []

        for a in account.accounts():
            child = self.get_account_balance(a, before, after)
            print(child.get_amount_values())
            for c,amount in child.get_amount_values().items():
                if amount.number().is_nonzero():
                    if str(amount.to_amount().commodity) not in amounts:
                        print(f'setting map to cur {amount.to_amount().commodity} to value {ledger.Value(f'{str(amount.to_amount().commodity)} 0')}')
                        amounts[str(amount.to_amount().commodity)] = ledger.Value(f'{str(amount.to_amount().commodity)} 0')
                    print(f'adding to {account.fullname()} the amount {amount}')
                    amounts[str(amount.to_amount().commodity)] += amount
            for c,amount in child.get_cleared_amount_values().items():
                if amount.number().is_nonzero():
                    if str(amount.to_amount().commodity) not in cleared_amounts:
                        print(f'setting map to cur {amount.to_amount().commodity} to value {ledger.Value(f'{str(amount.to_amount().commodity)} 0')}')
                        cleared_amounts[str(amount.to_amount().commodity)] = ledger.Value(f'{str(amount.to_amount().commodity)} 0')
                    print(f'(cleared) adding to {account.fullname()} the amount {amount}')
                    cleared_amounts[str(amount.to_amount().commodity)] += amount
            children += [child]

        for post in account.posts():
            if post.amount.number().is_nonzero():
                if (not before or post.date >= before) and (
                    not after or post.date < after):
                    if str(post.amount.commodity) not in amounts:
                        amounts[str(post.amount.commodity)] = ledger.Value(f'{str(post.amount.commodity)} 0')
                    amounts[str(post.amount.commodity)] += post.amount
                    if str(post.state) == 'Cleared':
                        if str(post.amount.commodity) not in cleared_amounts:
                            cleared_amounts[str(post.amount.commodity)] = ledger.Value(f'{str(post.amount.commodity)} 0')

                        cleared_amounts[str(post.amount.commodity)] += post.amount

        amountStrs : Dict[str, str] = {}
        for c,t in amounts.items():
            print(f'totals {str(t.number())}')
            amountStrs[c] = '0' if t.number().is_zero() else str(t.number())

        cleared_amount_strs : Dict[str, str] = {}
        for c,t in cleared_amounts.items():
            print(f'totals {str(t.number())}')
            cleared_amount_strs[c] = '0' if t.number().is_zero() else str(t.number())

        full_path = account.fullname()
        account_name = full_path.split(':')[-1] if ':' in full_path else full_path

        print(f'amounts calculated for {account.fullname()} is {amounts}')
        print(f'amounts (string) calculated for {account.fullname()} is {amountStrs}')
        
        return LedgerAccount.with_amount_values(
            account=account_name,
            full_path=full_path,
            amounts=amountStrs,
            cleared_amounts=cleared_amount_strs,
            amount_values=amounts,
            cleared_amount_values=cleared_amounts,
            last_cleared_date=None,
            children = children
        )

    def get_balance(self, before: Optional[datetime.date], after: Optional[datetime.date]) -> LedgerBalanceResponse:
        """Get balance for all accounts"""
        try:
            assert self._get_journal().valid()
            journal = self._get_journal()

            root = self.get_account_balance(journal.master, before, after)
            
            return LedgerBalanceResponse(
                account=root,
                timestamp=datetime.datetime.now().isoformat(),
                #total=sum(acc.amount for acc in accounts_data)
            )
            
        except Exception as e:
            tb_str = traceback.format_exc()
            logging.error("Something went wrong:\n%s", tb_str)
            logging.error(f"Failed to get balance: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # def get_account_balance(self, account_name: str, period: Optional[str] = None) -> LedgerBalanceResponse:
    #     """Get balance for specific account"""
    #     try:
    #         journal = self._get_journal()
    #         accounts_data = []
            
    #         for account in journal.accounts():
    #             if not account:
    #                 continue
                    
    #             full_path = account.fullname()
    #             if account_name.lower() in full_path.lower():
    #                 amount_val, amount_str = self._format_amount(account.amount)
    #                 cleared_val, cleared_str = self._format_amount(account.amount)
                    
    #                 account_simple = full_path.split(':')[-1] if ':' in full_path else full_path
                    
    #                 accounts_data.append(LedgerAccount(
    #                     account=account_simple,
    #                     fullPath=full_path,
    #                     amount=amount_val,
    #                     formattedAmount=amount_str,
    #                     clearedAmount=cleared_val,
    #                     formattedClearedAmount=cleared_str,
    #                     lastClearedDate=None
    #                 ))
            
    #         account_tree = self._build_account_tree(accounts_data)
            
    #         return LedgerBalanceResponse(
    #             accounts=account_tree,
    #             currency='BRL',
    #             timestamp=datetime.now().isoformat(),
    #             total=sum(acc.amount for acc in accounts_data)
    #         )
            
    #     except Exception as e:
    #         logger.error(f"Failed to get account balance: {e}")
    #         raise HTTPException(status_code=500, detail=str(e))

    # def get_account_transactions(self, account_name: str, period: Optional[str] = None) -> LedgerTransactionResponse:
    #     """Get transactions for specific account"""
    #     try:
    #         journal = self._get_journal()
    #         transactions = []
    #         running_balance = 0.0
            
    #         for xact in journal.xacts():
    #             if not xact:
    #                 continue
                
    #             for post in xact.posts():
    #                 if not post or not post.account:
    #                     continue
                    
    #                 full_path = post.account.fullname()
    #                 if account_name.lower() in full_path.lower():
    #                     amount_val, amount_str = self._format_amount(post.amount)
    #                     running_balance += amount_val
                        
    #                     transactions.append(LedgerTransactionNode(
    #                         date=xact.date.strftime('%Y/%m/%d'),
    #                         description=xact.payee or '',
    #                         amount=amount_val,
    #                         formattedAmount=amount_str,
    #                         runningBalance=running_balance,
    #                         formattedRunningBalance=f"BRL {running_balance:,.2f}"
    #                     ))
            
    #         transactions.sort(key=lambda x: x.date)
            
    #         return LedgerTransactionResponse(
    #             transactions=transactions,
    #             account=account_name,
    #             period=period,
    #             timestamp=datetime.now().isoformat()
    #         )
            
    #     except Exception as e:
    #         logger.error(f"Failed to get account transactions: {e}")
    #         raise HTTPException(status_code=500, detail=str(e))

    # def get_cash_flow(self, period: Optional[str] = None) -> LedgerSubTotalsResponse:
    #     """Get cash flow (inflows and outflows)"""
    #     try:
    #         journal = self._get_journal()
    #         cash_flow_map = {}
            
    #         for xact in journal.xacts():
    #             if not xact:
    #                 continue
                
    #             for post in xact.posts():
    #                 if not post or not post.account:
    #                     continue
                    
    #                 amount_val, _ = self._format_amount(post.amount)
    #                 account_name = post.account.fullname()
                    
    #                 if account_name not in cash_flow_map:
    #                     cash_flow_map[account_name] = {
    #                         'inflow': 0.0,
    #                         'outflow': 0.0,
    #                         'balance': 0.0
    #                     }
                    
    #                 if amount_val > 0:
    #                     cash_flow_map[account_name]['inflow'] += amount_val
    #                 else:
    #                     cash_flow_map[account_name]['outflow'] += amount_val
                    
    #                 cash_flow_map[account_name]['balance'] += amount_val
            
    #         subtotals = [
    #             LedgerSubTotalNode(
    #                 description=account,
    #                 inflowAmount=data['inflow'],
    #                 outflowAmount=data['outflow'],
    #                 runningBalance=data['balance']
    #             )
    #             for account, data in cash_flow_map.items()
    #         ]
            
    #         return LedgerSubTotalsResponse(
    #             subtotals=subtotals,
    #             period=period,
    #             timestamp=datetime.now().isoformat()
    #         )
            
    #     except Exception as e:
    #         logger.error(f"Failed to get cash flow: {e}")
    #         raise HTTPException(status_code=500, detail=str(e))

    # def get_budget_report(self, period: Optional[str] = None) -> BudgetResponse:
    #     """Get budget vs actual spending report"""
    #     try:
    #         journal = self._get_journal()
            
    #         budget_data = self._read_budget_from_file()
    #         logger.info(f"Found {len(budget_data)} budget entries")
            
    #         actual_data = {}
            
    #         for xact in journal.xacts():
    #             if not xact:
    #                 continue
                
    #             payee = (xact.payee or '').lower()
    #             if 'budget' in payee and not xact.posts():
    #                 continue
                
    #             for post in xact.posts():
    #                 if not post or not post.account:
    #                     continue
                    
    #                 account_name = post.account.fullname()
    #                 amount_val, _ = self._format_amount(post.amount)
                    
    #                 if account_name not in actual_data:
    #                     actual_data[account_name] = 0.0
    #                 actual_data[account_name] += abs(amount_val)
            
    #         budgeted_accounts = set(budget_data.keys())
            
    #         budget_items = []
    #         total_actual = 0.0
    #         total_budget = 0.0
    #         total_variance = 0.0
            
    #         for account_path in sorted(budgeted_accounts):
    #             actual_amount = actual_data.get(account_path, 0.0)
    #             budget_amount = budget_data.get(account_path, 0.0)
    #             variance = actual_amount - budget_amount
                
    #             if budget_amount != 0:
    #                 variance_percentage = (variance / budget_amount) * 100
    #             else:
    #                 variance_percentage = 0.0
                
    #             account_parts = account_path.split(':')
    #             account_name = account_parts[-1]
                
    #             is_over_budget = actual_amount > budget_amount
                
    #             budget_items.append(BudgetItem(
    #                 account=account_name,
    #                 fullPath=account_path,
    #                 actualAmount=actual_amount,
    #                 budgetAmount=budget_amount,
    #                 variance=variance,
    #                 variancePercentage=variance_percentage,
    #                 formattedActual=f"BRL {actual_amount:,.2f}",
    #                 formattedBudget=f"BRL {budget_amount:,.2f}",
    #                 formattedVariance=f"BRL {variance:,.2f}",
    #                 isOverBudget=is_over_budget
    #             ))
                
    #             total_actual += actual_amount
    #             total_budget += budget_amount
    #             total_variance += variance
            
    #         logger.info(f"Generated budget report with {len(budget_items)} items")
            
    #         return BudgetResponse(
    #             budgetItems=budget_items,
    #             totalActual=total_actual,
    #             totalBudget=total_budget,
    #             totalVariance=total_variance,
    #             period=period or 'this month',
    #             timestamp=datetime.now().isoformat()
    #         )
            
    #     except Exception as e:
    #         logger.error(f"Failed to generate budget report: {e}")
    #         raise HTTPException(status_code=500, detail=str(e))

