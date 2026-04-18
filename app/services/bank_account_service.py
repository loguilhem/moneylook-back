from sqlalchemy.orm import Session
from app.models.bank_account import BankAccount
from app.schemas.bank_account import BankAccountCreate, BankAccountUpdate


class BankAccountService:
    def __init__(self, db: Session):
        self.db = db

    def list(self) -> list[BankAccount]:
        return self.db.query(BankAccount).order_by(BankAccount.id).all()

    def get(self, bank_account_id: int) -> BankAccount | None:
        return self.db.get(BankAccount, bank_account_id)

    def create(self, payload: BankAccountCreate) -> BankAccount:
        obj = BankAccount(**payload.model_dump())
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(self, obj: BankAccount, payload: BankAccountUpdate) -> BankAccount:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(obj, field, value)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, obj: BankAccount) -> None:
        self.db.delete(obj)
        self.db.commit()