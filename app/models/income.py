from datetime import date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Date, Integer, String, ForeignKey
from app.core.database import Base

class Income(Base):
    __tablename__ = "incomes"

    id: Mapped[int] = mapped_column(primary_key=True)

    date: Mapped[date] = mapped_column(Date, nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)

    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)

    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id"),
        nullable=True
    )

    bank_account_id: Mapped[int] = mapped_column(
        ForeignKey("bank_accounts.id"),
        nullable=False
    )

    recurring_income_id: Mapped[int | None] = mapped_column(
        ForeignKey("recurring_incomes.id"),
        nullable=True
    )

    category = relationship("Category", back_populates="incomes")
    bank_account = relationship("BankAccount", back_populates="incomes")
    recurring_income = relationship("RecurringIncome", back_populates="generated_incomes")
