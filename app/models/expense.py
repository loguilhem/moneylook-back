from datetime import date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Date, Integer, String, ForeignKey
from app.core.database import Base

class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(primary_key=True)

    date: Mapped[date] = mapped_column(Date, nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)

    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)

    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id"),
        nullable=False
    )

    bank_account_id: Mapped[int] = mapped_column(
        ForeignKey("bank_accounts.id"),
        nullable=False
    )

    recurring_expense_id: Mapped[int | None] = mapped_column(
        ForeignKey("recurring_expenses.id"),
        nullable=True
    )

    category = relationship("Category", back_populates="expenses")
    bank_account = relationship("BankAccount", back_populates="expenses")
    recurring_expense = relationship("RecurringExpense", back_populates="generated_expenses")