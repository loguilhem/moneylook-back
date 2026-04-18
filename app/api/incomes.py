from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.income import IncomeCreate, IncomeRead, IncomeUpdate
from app.services.income_service import IncomeService


def register_income_routes(app: FastAPI) -> None:
    @app.get("/incomes", response_model=list[IncomeRead], tags=["Incomes"])
    def list_incomes(db: Session = Depends(get_db)):
        return IncomeService(db).list()

    @app.get("/incomes/{income_id}", response_model=IncomeRead, tags=["Incomes"])
    def get_income(income_id: int, db: Session = Depends(get_db)):
        obj = IncomeService(db).get(income_id)
        if not obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Income not found")
        return obj

    @app.post("/incomes", response_model=IncomeRead, status_code=status.HTTP_201_CREATED, tags=["Incomes"])
    def create_income(payload: IncomeCreate, db: Session = Depends(get_db)):
        return IncomeService(db).create(payload)

    @app.patch("/incomes/{income_id}", response_model=IncomeRead, tags=["Incomes"])
    def update_income(income_id: int, payload: IncomeUpdate, db: Session = Depends(get_db)):
        service = IncomeService(db)
        obj = service.get(income_id)
        if not obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Income not found")
        return service.update(obj, payload)

    @app.delete("/incomes/{income_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Incomes"])
    def delete_income(income_id: int, db: Session = Depends(get_db)):
        service = IncomeService(db)
        obj = service.get(income_id)
        if not obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Income not found")
        service.delete(obj)