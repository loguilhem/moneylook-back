from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey
from app.core.database import Base

class BankAccount(Base):
    __tablename__ = "bank_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="CHF")

    account_type_id: Mapped[int] = mapped_column(
        ForeignKey("account_types.id"),
        nullable=False
    )

    account_type = relationship("AccountType", back_populates="bank_accounts")

    expenses = relationship("Expense", back_populates="bank_account")
    recurring_expenses = relationship("RecurringExpense", back_populates="bank_account")
    incomes = relationship("Income", back_populates="bank_account")
    recurring_incomes = relationship("RecurringIncome", back_populates="bank_account")
