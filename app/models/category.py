from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String
from app.core.database import Base

class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    icon_html: Mapped[str] = mapped_column(String(255), nullable=False)
    color: Mapped[str] = mapped_column(String(20), nullable=False)
    parent: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)

    expenses = relationship("Expense", back_populates="category")
    incomes = relationship("Income", back_populates="category")
    recurring_expenses = relationship("RecurringExpense", back_populates="category")
    recurring_incomes = relationship("RecurringIncome", back_populates="category")
