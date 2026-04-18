from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.expense import ExpenseCreate, ExpenseRead, ExpenseUpdate
from app.services.expense_service import ExpenseService


def register_expense_routes(app: FastAPI) -> None:
    @app.get("/expenses", response_model=list[ExpenseRead], tags=["Expenses"])
    def list_expenses(db: Session = Depends(get_db)):
        return ExpenseService(db).list()

    @app.get("/expenses/{expense_id}", response_model=ExpenseRead, tags=["Expenses"])
    def get_expense(expense_id: int, db: Session = Depends(get_db)):
        obj = ExpenseService(db).get(expense_id)
        if not obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
        return obj

    @app.post("/expenses", response_model=ExpenseRead, status_code=status.HTTP_201_CREATED, tags=["Expenses"])
    def create_expense(payload: ExpenseCreate, db: Session = Depends(get_db)):
        return ExpenseService(db).create(payload)

    @app.patch("/expenses/{expense_id}", response_model=ExpenseRead, tags=["Expenses"])
    def update_expense(expense_id: int, payload: ExpenseUpdate, db: Session = Depends(get_db)):
        service = ExpenseService(db)
        obj = service.get(expense_id)
        if not obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
        return service.update(obj, payload)

    @app.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Expenses"])
    def delete_expense(expense_id: int, db: Session = Depends(get_db)):
        service = ExpenseService(db)
        obj = service.get(expense_id)
        if not obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
        service.delete(obj)