from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.bank_account import (
    BankAccountCreate,
    BankAccountRead,
    BankAccountUpdate,
)
from app.services.bank_account_service import BankAccountService


def register_bank_account_routes(app: FastAPI) -> None:
    @app.get("/bank-accounts", response_model=list[BankAccountRead], tags=["Bank Accounts"])
    def list_bank_accounts(db: Session = Depends(get_db)):
        return BankAccountService(db).list()

    @app.get("/bank-accounts/{bank_account_id}", response_model=BankAccountRead, tags=["Bank Accounts"])
    def get_bank_account(bank_account_id: int, db: Session = Depends(get_db)):
        obj = BankAccountService(db).get(bank_account_id)
        if not obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bank account not found")
        return obj

    @app.post("/bank-accounts", response_model=BankAccountRead, status_code=status.HTTP_201_CREATED, tags=["Bank Accounts"])
    def create_bank_account(payload: BankAccountCreate, db: Session = Depends(get_db)):
        return BankAccountService(db).create(payload)

    @app.patch("/bank-accounts/{bank_account_id}", response_model=BankAccountRead, tags=["Bank Accounts"])
    def update_bank_account(bank_account_id: int, payload: BankAccountUpdate, db: Session = Depends(get_db)):
        service = BankAccountService(db)
        obj = service.get(bank_account_id)
        if not obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bank account not found")
        return service.update(obj, payload)

    @app.delete("/bank-accounts/{bank_account_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Bank Accounts"])
    def delete_bank_account(bank_account_id: int, db: Session = Depends(get_db)):
        service = BankAccountService(db)
        obj = service.get(bank_account_id)
        if not obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bank account not found")
        service.delete(obj)