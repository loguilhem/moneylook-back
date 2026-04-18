from sqlalchemy.orm import Session
from app.models.recurring_expense import RecurringExpense
from app.schemas.recurring_expense import (
    RecurringExpenseCreate,
    RecurringExpenseUpdate,
)


class RecurringExpenseService:
    def __init__(self, db: Session):
        self.db = db

    def list(self) -> list[RecurringExpense]:
        return self.db.query(RecurringExpense).order_by(RecurringExpense.id).all()

    def get(self, recurring_expense_id: int) -> RecurringExpense | None:
        return self.db.get(RecurringExpense, recurring_expense_id)

    def create(self, payload: RecurringExpenseCreate) -> RecurringExpense:
        obj = RecurringExpense(**payload.model_dump())
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(
        self,
        obj: RecurringExpense,
        payload: RecurringExpenseUpdate,
    ) -> RecurringExpense:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(obj, field, value)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, obj: RecurringExpense) -> None:
        self.db.delete(obj)
        self.db.commit()