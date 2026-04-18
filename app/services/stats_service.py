from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.expense import Expense
from app.models.income import Income
from app.models.bank_account import BankAccount


class StatsService:
    def __init__(self, db: Session):
        self.db = db

    def get_total_expenses(self, start_date: date, end_date: date) -> int:
        total = (
            self.db.query(func.coalesce(func.sum(Expense.amount_cents), 0))
            .filter(Expense.date >= start_date, Expense.date <= end_date)
            .scalar()
        )
        return int(total or 0)

    def get_total_incomes(self, start_date: date, end_date: date) -> int:
        total = (
            self.db.query(func.coalesce(func.sum(Income.amount_cents), 0))
            .filter(Income.date >= start_date, Income.date <= end_date)
            .scalar()
        )
        return int(total or 0)

    def get_expenses_by_category(self, start_date: date, end_date: date):
        rows = (
            self.db.query(
                Category.id.label("category_id"),
                Category.name.label("category_name"),
                Category.color.label("color"),
                Category.icon_html.label("icon_html"),
                func.coalesce(func.sum(Expense.amount_cents), 0).label("total_cents"),
            )
            .join(Expense, Expense.category_id == Category.id)
            .filter(Expense.date >= start_date, Expense.date <= end_date)
            .group_by(Category.id, Category.name, Category.color, Category.icon_html)
            .order_by(func.sum(Expense.amount_cents).desc())
            .all()
        )

        return [
            {
                "category_id": row.category_id,
                "category_name": row.category_name,
                "color": row.color,
                "icon_html": row.icon_html,
                "total_cents": int(row.total_cents),
            }
            for row in rows
        ]

    def get_expenses_by_category_percent(self, start_date: date, end_date: date):
        items = self.get_expenses_by_category(start_date, end_date)
        total = sum(item["total_cents"] for item in items)

        if total == 0:
            return [
                {
                    **item,
                    "percentage": 0.0,
                }
                for item in items
            ]

        return [
            {
                **item,
                "percentage": round((item["total_cents"] / total) * 100, 2),
            }
            for item in items
        ]

    def get_expenses_by_account(self, start_date: date, end_date: date):
        rows = (
            self.db.query(
                BankAccount.id.label("bank_account_id"),
                BankAccount.label.label("bank_account_label"),
                func.coalesce(func.sum(Expense.amount_cents), 0).label("total_cents"),
            )
            .join(Expense, Expense.bank_account_id == BankAccount.id)
            .filter(Expense.date >= start_date, Expense.date <= end_date)
            .group_by(BankAccount.id, BankAccount.label)
            .order_by(func.sum(Expense.amount_cents).desc())
            .all()
        )

        return [
            {
                "bank_account_id": row.bank_account_id,
                "bank_account_label": row.bank_account_label,
                "total_cents": int(row.total_cents),
            }
            for row in rows
        ]

    def get_expenses_by_month(self, start_date: date, end_date: date):
        rows = (
            self.db.query(Expense.date, Expense.amount_cents)
            .filter(Expense.date >= start_date, Expense.date <= end_date)
            .order_by(Expense.date)
            .all()
        )

        totals_by_month: dict[str, int] = {}
        for row in rows:
            month = row.date.strftime("%Y-%m")
            totals_by_month[month] = totals_by_month.get(month, 0) + int(row.amount_cents)

        return [
            {
                "month": month,
                "total_cents": total_cents,
            }
            for month, total_cents in totals_by_month.items()
        ]

    def get_balance(self, start_date: date, end_date: date):
        total_income = self.get_total_incomes(start_date, end_date)
        total_expense = self.get_total_expenses(start_date, end_date)

        return {
            "start_date": start_date,
            "end_date": end_date,
            "total_income_cents": total_income,
            "total_expense_cents": total_expense,
            "balance_cents": total_income - total_expense,
        }
