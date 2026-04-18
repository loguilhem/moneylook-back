from sqlalchemy.orm import Session

from app.models.recurring_income import RecurringIncome
from app.schemas.recurring_income import (
    RecurringIncomeCreate,
    RecurringIncomeUpdate,
)


class RecurringIncomeService:
    def __init__(self, db: Session):
        self.db = db

    def list(self) -> list[RecurringIncome]:
        return self.db.query(RecurringIncome).order_by(RecurringIncome.id).all()

    def get(self, recurring_income_id: int) -> RecurringIncome | None:
        return self.db.get(RecurringIncome, recurring_income_id)

    def create(self, payload: RecurringIncomeCreate) -> RecurringIncome:
        obj = RecurringIncome(**payload.model_dump())
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(
        self,
        obj: RecurringIncome,
        payload: RecurringIncomeUpdate,
    ) -> RecurringIncome:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(obj, field, value)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, obj: RecurringIncome) -> None:
        self.db.delete(obj)
        self.db.commit()
