from sqlalchemy.orm import Session
from app.models.expense import Expense
from app.schemas.expense import ExpenseCreate, ExpenseUpdate


class ExpenseService:
    def __init__(self, db: Session):
        self.db = db

    def list(self) -> list[Expense]:
        return self.db.query(Expense).order_by(Expense.date.desc(), Expense.id.desc()).all()

    def get(self, expense_id: int) -> Expense | None:
        return self.db.get(Expense, expense_id)

    def create(self, payload: ExpenseCreate) -> Expense:
        obj = Expense(**payload.model_dump())
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(self, obj: Expense, payload: ExpenseUpdate) -> Expense:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(obj, field, value)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, obj: Expense) -> None:
        self.db.delete(obj)
        self.db.commit()