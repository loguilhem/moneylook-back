from sqlalchemy.orm import Session
from app.models.account_type import AccountType
from app.schemas.account_type import AccountTypeCreate, AccountTypeUpdate


class AccountTypeService:
    def __init__(self, db: Session):
        self.db = db

    def list(self) -> list[AccountType]:
        return self.db.query(AccountType).order_by(AccountType.id).all()

    def get(self, account_type_id: int) -> AccountType | None:
        return self.db.get(AccountType, account_type_id)

    def create(self, payload: AccountTypeCreate) -> AccountType:
        obj = AccountType(**payload.model_dump())
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(self, obj: AccountType, payload: AccountTypeUpdate) -> AccountType:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(obj, field, value)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, obj: AccountType) -> None:
        self.db.delete(obj)
        self.db.commit()