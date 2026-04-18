from sqlalchemy.orm import Session
from app.models.income import Income
from app.schemas.income import IncomeCreate, IncomeUpdate


class IncomeService:
    def __init__(self, db: Session):
        self.db = db

    def list(self) -> list[Income]:
        return self.db.query(Income).order_by(Income.date.desc(), Income.id.desc()).all()

    def get(self, income_id: int) -> Income | None:
        return self.db.get(Income, income_id)

    def create(self, payload: IncomeCreate) -> Income:
        obj = Income(**payload.model_dump())
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(self, obj: Income, payload: IncomeUpdate) -> Income:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(obj, field, value)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, obj: Income) -> None:
        self.db.delete(obj)
        self.db.commit()