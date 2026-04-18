from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.recurring_income import (
    RecurringIncomeCreate,
    RecurringIncomeRead,
    RecurringIncomeUpdate,
)
from app.services.recurring_income_service import RecurringIncomeService


def register_recurring_income_routes(app: FastAPI) -> None:
    @app.get("/recurring-incomes", response_model=list[RecurringIncomeRead], tags=["Recurring Incomes"])
    def list_recurring_incomes(db: Session = Depends(get_db)):
        return RecurringIncomeService(db).list()

    @app.get("/recurring-incomes/{recurring_income_id}", response_model=RecurringIncomeRead, tags=["Recurring Incomes"])
    def get_recurring_income(recurring_income_id: int, db: Session = Depends(get_db)):
        obj = RecurringIncomeService(db).get(recurring_income_id)
        if not obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurring income not found")
        return obj

    @app.post(
        "/recurring-incomes",
        response_model=RecurringIncomeRead,
        status_code=status.HTTP_201_CREATED,
        tags=["Recurring Incomes"],
    )
    def create_recurring_income(payload: RecurringIncomeCreate, db: Session = Depends(get_db)):
        return RecurringIncomeService(db).create(payload)

    @app.patch("/recurring-incomes/{recurring_income_id}", response_model=RecurringIncomeRead, tags=["Recurring Incomes"])
    def update_recurring_income(
        recurring_income_id: int,
        payload: RecurringIncomeUpdate,
        db: Session = Depends(get_db),
    ):
        service = RecurringIncomeService(db)
        obj = service.get(recurring_income_id)
        if not obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurring income not found")
        return service.update(obj, payload)

    @app.delete("/recurring-incomes/{recurring_income_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Recurring Incomes"])
    def delete_recurring_income(recurring_income_id: int, db: Session = Depends(get_db)):
        service = RecurringIncomeService(db)
        obj = service.get(recurring_income_id)
        if not obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurring income not found")
        service.delete(obj)
