from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate
from app.services.category_service import CategoryService


def register_category_routes(app: FastAPI) -> None:
    @app.get("/categories", response_model=list[CategoryRead], tags=["Categories"])
    def list_categories(db: Session = Depends(get_db)):
        return CategoryService(db).list()

    @app.get("/categories/{category_id}", response_model=CategoryRead, tags=["Categories"])
    def get_category(category_id: int, db: Session = Depends(get_db)):
        obj = CategoryService(db).get(category_id)
        if not obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        return obj

    @app.post("/categories", response_model=CategoryRead, status_code=status.HTTP_201_CREATED, tags=["Categories"])
    def create_category(payload: CategoryCreate, db: Session = Depends(get_db)):
        return CategoryService(db).create(payload)

    @app.patch("/categories/{category_id}", response_model=CategoryRead, tags=["Categories"])
    def update_category(category_id: int, payload: CategoryUpdate, db: Session = Depends(get_db)):
        service = CategoryService(db)
        obj = service.get(category_id)
        if not obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        return service.update(obj, payload)

    @app.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Categories"])
    def delete_category(category_id: int, db: Session = Depends(get_db)):
        service = CategoryService(db)
        obj = service.get(category_id)
        if not obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        service.delete(obj)