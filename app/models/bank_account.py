from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Boolean, ForeignKey, Index, Integer, String
from app.core.database import Base

class BankAccount(Base):
    __tablename__ = "bank_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="CHF")
    initial_balance_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    account_type_id: Mapped[int] = mapped_column(
        ForeignKey("account_types.id"),
        nullable=False
    )

    account_type = relationship("AccountType", back_populates="bank_accounts")

    expenses = relationship("Expense", back_populates="bank_account")
    recurring_expenses = relationship("RecurringExpense", back_populates="bank_account")
    incomes = relationship("Income", back_populates="bank_account")
    recurring_incomes = relationship("RecurringIncome", back_populates="bank_account")


Index(
    "uq_bank_accounts_single_default",
    BankAccount.is_default,
    unique=True,
    postgresql_where=BankAccount.is_default.is_(True),
)
