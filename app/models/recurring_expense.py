from datetime import date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import CheckConstraint, Date, Integer, String, ForeignKey
from app.core.database import Base


class RecurringExpense(Base):
    __tablename__ = "recurring_expenses"
    __table_args__ = (
        CheckConstraint(
            "frequency IN ('weekly', 'monthly', 'yearly')",
            name="ck_recurring_expenses_frequency",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    label: Mapped[str] = mapped_column(String(255), nullable=False)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)

    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    frequency: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="mensuel",
    )

    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id"),
        nullable=False
    )

    bank_account_id: Mapped[int] = mapped_column(
        ForeignKey("bank_accounts.id"),
        nullable=False
    )

    category = relationship("Category", back_populates="recurring_expenses")
    bank_account = relationship("BankAccount", back_populates="recurring_expenses")

    generated_expenses = relationship(
        "Expense",
        back_populates="recurring_expense"
    )
