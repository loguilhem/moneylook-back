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

    def clear_default_accounts(self, except_id: int | None = None) -> None:
        query = self.db.query(BankAccount).filter(BankAccount.is_default.is_(True))
        if except_id is not None:
            query = query.filter(BankAccount.id != except_id)
        query.update({BankAccount.is_default: False}, synchronize_session=False)

    def create(self, payload: BankAccountCreate) -> BankAccount:
        values = payload.model_dump()
        if values.get("is_default"):
            self.clear_default_accounts()
        obj = BankAccount(**values)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(self, obj: BankAccount, payload: BankAccountUpdate) -> BankAccount:
        values = payload.model_dump(exclude_unset=True)
        if values.get("is_default"):
            self.clear_default_accounts(except_id=obj.id)
        for field, value in values.items():
            setattr(obj, field, value)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, obj: BankAccount) -> None:
        self.db.delete(obj)
        self.db.commit()
