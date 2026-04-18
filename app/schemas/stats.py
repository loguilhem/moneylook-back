from datetime import date
from pydantic import BaseModel


class DateRangeQuery(BaseModel):
    start_date: date
    end_date: date


class TotalAmountRead(BaseModel):
    start_date: date
    end_date: date
    total_cents: int


class ExpenseByCategoryRead(BaseModel):
    category_id: int
    category_name: str
    color: str
    icon_html: str
    total_cents: int


class ExpenseByCategoryPercentRead(BaseModel):
    category_id: int
    category_name: str
    color: str
    icon_html: str
    total_cents: int
    percentage: float


class ExpenseByAccountRead(BaseModel):
    bank_account_id: int
    bank_account_label: str
    total_cents: int


class ExpenseByMonthRead(BaseModel):
    month: str
    total_cents: int


class BalanceRead(BaseModel):
    start_date: date
    end_date: date
    total_income_cents: int
    total_expense_cents: int
    balance_cents: int