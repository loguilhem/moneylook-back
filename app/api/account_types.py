from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.account_type import (
    AccountTypeCreate,
    AccountTypeRead,
    AccountTypeUpdate,
)
from app.services.account_type_service import AccountTypeService, SystemAccountTypeError


def register_account_type_routes(app: FastAPI) -> None:
    @app.get("/account-types", response_model=list[AccountTypeRead], tags=["Account Types"])
    def list_account_types(db: Session = Depends(get_db)):
        return AccountTypeService(db).list()

    @app.get("/account-types/{account_type_id}", response_model=AccountTypeRead, tags=["Account Types"])
    def get_account_type(account_type_id: int, db: Session = Depends(get_db)):
        obj = AccountTypeService(db).get(account_type_id)
        if not obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account type not found")
        return obj

    @app.post("/account-types", response_model=AccountTypeRead, status_code=status.HTTP_201_CREATED, tags=["Account Types"])
    def create_account_type(payload: AccountTypeCreate, db: Session = Depends(get_db)):
        return AccountTypeService(db).create(payload)

    @app.patch("/account-types/{account_type_id}", response_model=AccountTypeRead, tags=["Account Types"])
    def update_account_type(account_type_id: int, payload: AccountTypeUpdate, db: Session = Depends(get_db)):
        service = AccountTypeService(db)
        obj = service.get(account_type_id)
        if not obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account type not found")
        try:
            return service.update(obj, payload)
        except SystemAccountTypeError as error:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error)) from error

    @app.delete("/account-types/{account_type_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Account Types"])
    def delete_account_type(account_type_id: int, db: Session = Depends(get_db)):
        service = AccountTypeService(db)
        obj = service.get(account_type_id)
        if not obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account type not found")
        try:
            service.delete(obj)
        except SystemAccountTypeError as error:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error)) from error
