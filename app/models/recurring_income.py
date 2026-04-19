from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class RecurringIncome(Base):
    __tablename__ = "recurring_incomes"
    __table_args__ = (
        CheckConstraint(
            "frequency IN ('weekly', 'monthly', 'yearly')",
            name="ck_recurring_incomes_frequency",
        ),
        CheckConstraint(
            "date_policy IN ('same_day', 'last_day_of_month', 'first_business_day', 'last_business_day')",
            name="ck_recurring_incomes_date_policy",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    label: Mapped[str] = mapped_column(String(255), nullable=False)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    date_policy: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="same_day",
    )

    frequency: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="monthly",
    )

    bank_account_id: Mapped[int] = mapped_column(
        ForeignKey("bank_accounts.id"),
        nullable=False,
    )

    bank_account = relationship("BankAccount", back_populates="recurring_incomes")
