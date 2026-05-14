from datetime import date, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.bank_account import BankAccount
from app.models.category import Category
from app.models.expense import Expense
from app.models.income import Income
from app.models.recurring_expense import RecurringExpense
from app.models.recurring_income import RecurringIncome


def cents_to_amount(value: int) -> float:
    return round(value / 100, 2)


def start_of_month(value: date) -> date:
    return value.replace(day=1)


def end_of_month(value: date) -> date:
    if value.month == 12:
        next_month = date(value.year + 1, 1, 1)
    else:
        next_month = date(value.year, value.month + 1, 1)

    return next_month - timedelta(days=1)


def previous_month(value: date) -> date:
    first_day = start_of_month(value)
    return first_day - timedelta(days=1)


class LlmContextService:
    def __init__(self, db: Session):
        self.db = db

    def build_context(self) -> dict:
        today = date.today()
        current_start = start_of_month(today)
        current_end = end_of_month(today)
        previous_month_day = previous_month(today)
        previous_start = start_of_month(previous_month_day)
        previous_end = end_of_month(previous_month_day)

        return {
            "currency_note": "Amounts are decimal values converted from cents. Bank accounts may use different currencies.",
            "available_data": {
                "current_month": {"start_date": current_start.isoformat(), "end_date": current_end.isoformat()},
                "previous_month": {"start_date": previous_start.isoformat(), "end_date": previous_end.isoformat()},
            },
            "current_month": self.build_period_summary(current_start, current_end),
            "previous_month": self.build_period_summary(previous_start, previous_end),
            "bank_accounts": self.build_bank_accounts(),
            "recent_transactions": self.build_recent_transactions(),
            "active_recurring_items": self.build_active_recurring_items(),
        }

    def build_period_summary(self, start_date: date, end_date: date) -> dict:
        total_income_cents = self.sum_incomes(start_date, end_date)
        total_expense_cents = self.sum_expenses(start_date, end_date)

        return {
            "total_income": cents_to_amount(total_income_cents),
            "total_expense": cents_to_amount(total_expense_cents),
            "net_balance": cents_to_amount(total_income_cents - total_expense_cents),
            "top_expense_categories": self.top_expense_categories(start_date, end_date),
            "top_expense_accounts": self.top_expense_accounts(start_date, end_date),
        }

    def sum_expenses(self, start_date: date, end_date: date) -> int:
        total = (
            self.db.query(func.coalesce(func.sum(Expense.amount_cents), 0))
            .filter(Expense.date >= start_date, Expense.date <= end_date)
            .scalar()
        )
        return int(total or 0)

    def sum_incomes(self, start_date: date, end_date: date) -> int:
        total = (
            self.db.query(func.coalesce(func.sum(Income.amount_cents), 0))
            .filter(Income.date >= start_date, Income.date <= end_date)
            .scalar()
        )
        return int(total or 0)

    def top_expense_categories(self, start_date: date, end_date: date, limit: int = 5) -> list[dict]:
        rows = (
            self.db.query(
                Category.name.label("category_name"),
                func.coalesce(func.sum(Expense.amount_cents), 0).label("total_cents"),
            )
            .join(Expense, Expense.category_id == Category.id)
            .filter(Expense.date >= start_date, Expense.date <= end_date)
            .group_by(Category.name)
            .order_by(func.sum(Expense.amount_cents).desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "category": row.category_name,
                "amount": cents_to_amount(int(row.total_cents or 0)),
            }
            for row in rows
        ]

    def top_expense_accounts(self, start_date: date, end_date: date, limit: int = 4) -> list[dict]:
        rows = (
            self.db.query(
                BankAccount.label.label("account_label"),
                BankAccount.currency.label("currency"),
                func.coalesce(func.sum(Expense.amount_cents), 0).label("total_cents"),
            )
            .join(Expense, Expense.bank_account_id == BankAccount.id)
            .filter(Expense.date >= start_date, Expense.date <= end_date)
            .group_by(BankAccount.label, BankAccount.currency)
            .order_by(func.sum(Expense.amount_cents).desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "account": row.account_label,
                "currency": row.currency,
                "amount": cents_to_amount(int(row.total_cents or 0)),
            }
            for row in rows
        ]

    def build_bank_accounts(self) -> list[dict]:
        accounts = (
            self.db.query(BankAccount)
            .options(joinedload(BankAccount.account_type))
            .order_by(BankAccount.id)
            .all()
        )
        account_items = []

        for account in accounts:
            income_total = (
                self.db.query(func.coalesce(func.sum(Income.amount_cents), 0))
                .filter(Income.bank_account_id == account.id)
                .scalar()
            )
            expense_total = (
                self.db.query(func.coalesce(func.sum(Expense.amount_cents), 0))
                .filter(Expense.bank_account_id == account.id)
                .scalar()
            )
            balance_cents = int(account.initial_balance_cents or 0) + int(income_total or 0) - int(expense_total or 0)

            account_items.append(
                {
                    "label": account.label,
                    "currency": account.currency,
                    "type": account.account_type.name if account.account_type else None,
                    "is_default": account.is_default,
                    "estimated_balance": cents_to_amount(balance_cents),
                }
            )

        return account_items

    def build_recent_transactions(self, limit: int = 10) -> list[dict]:
        expenses = (
            self.db.query(Expense)
            .options(joinedload(Expense.category), joinedload(Expense.bank_account))
            .order_by(Expense.date.desc(), Expense.id.desc())
            .limit(limit)
            .all()
        )
        incomes = (
            self.db.query(Income)
            .options(joinedload(Income.category), joinedload(Income.bank_account))
            .order_by(Income.date.desc(), Income.id.desc())
            .limit(limit)
            .all()
        )

        transactions = [
            {
                "type": "expense",
                "date": expense.date.isoformat(),
                "label": expense.label,
                "amount": cents_to_amount(expense.amount_cents),
                "category": expense.category.name if expense.category else None,
                "account": expense.bank_account.label if expense.bank_account else None,
            }
            for expense in expenses
        ]
        transactions.extend(
            {
                "type": "income",
                "date": income.date.isoformat(),
                "label": income.label,
                "amount": cents_to_amount(income.amount_cents),
                "category": income.category.name if income.category else None,
                "account": income.bank_account.label if income.bank_account else None,
            }
            for income in incomes
        )

        return sorted(transactions, key=lambda item: item["date"], reverse=True)[:limit]

    def build_active_recurring_items(self, limit: int = 12) -> list[dict]:
        recurring_expenses = (
            self.db.query(RecurringExpense)
            .options(joinedload(RecurringExpense.category), joinedload(RecurringExpense.bank_account))
            .filter(RecurringExpense.is_active.is_(True))
            .order_by(RecurringExpense.id)
            .limit(limit)
            .all()
        )
        recurring_incomes = (
            self.db.query(RecurringIncome)
            .options(joinedload(RecurringIncome.category), joinedload(RecurringIncome.bank_account))
            .filter(RecurringIncome.is_active.is_(True))
            .order_by(RecurringIncome.id)
            .limit(limit)
            .all()
        )

        items = [
            {
                "type": "expense",
                "label": item.label,
                "amount": cents_to_amount(item.amount_cents),
                "frequency": item.frequency,
                "category": item.category.name if item.category else None,
                "account": item.bank_account.label if item.bank_account else None,
            }
            for item in recurring_expenses
        ]
        items.extend(
            {
                "type": "income",
                "label": item.label,
                "amount": cents_to_amount(item.amount_cents),
                "frequency": item.frequency,
                "category": item.category.name if item.category else None,
                "account": item.bank_account.label if item.bank_account else None,
            }
            for item in recurring_incomes
        )

        return items[:limit]
