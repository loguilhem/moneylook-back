from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.recurring_expense import (
    RecurringExpenseCreate,
    RecurringExpenseRead,
    RecurringExpenseUpdate,
)
from app.services.recurring_expense_service import RecurringExpenseService


def register_recurring_expense_routes(app: FastAPI) -> None:
    @app.get("/recurring-expenses", response_model=list[RecurringExpenseRead], tags=["Recurring Expenses"])
    def list_recurring_expenses(db: Session = Depends(get_db)):
        return RecurringExpenseService(db).list()

    @app.get("/recurring-expenses/{recurring_expense_id}", response_model=RecurringExpenseRead, tags=["Recurring Expenses"])
    def get_recurring_expense(recurring_expense_id: int, db: Session = Depends(get_db)):
        obj = RecurringExpenseService(db).get(recurring_expense_id)
        if not obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurring expense not found")
        return obj

    @app.post("/recurring-expenses", response_model=RecurringExpenseRead, status_code=status.HTTP_201_CREATED, tags=["Recurring Expenses"])
    def create_recurring_expense(payload: RecurringExpenseCreate, db: Session = Depends(get_db)):
        return RecurringExpenseService(db).create(payload)

    @app.patch("/recurring-expenses/{recurring_expense_id}", response_model=RecurringExpenseRead, tags=["Recurring Expenses"])
    def update_recurring_expense(
        recurring_expense_id: int,
        payload: RecurringExpenseUpdate,
        db: Session = Depends(get_db),
    ):
        service = RecurringExpenseService(db)
        obj = service.get(recurring_expense_id)
        if not obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurring expense not found")
        return service.update(obj, payload)

    @app.delete("/recurring-expenses/{recurring_expense_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Recurring Expenses"])
    def delete_recurring_expense(recurring_expense_id: int, db: Session = Depends(get_db)):
        service = RecurringExpenseService(db)
        obj = service.get(recurring_expense_id)
        if not obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurring expense not found")
        service.delete(obj)