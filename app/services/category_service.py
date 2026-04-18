from sqlalchemy.orm import Session
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate


class CategoryService:
    def __init__(self, db: Session):
        self.db = db

    def list(self) -> list[Category]:
        return self.db.query(Category).order_by(Category.id).all()

    def get(self, category_id: int) -> Category | None:
        return self.db.get(Category, category_id)

    def create(self, payload: CategoryCreate) -> Category:
        obj = Category(**payload.model_dump())
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(self, obj: Category, payload: CategoryUpdate) -> Category:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(obj, field, value)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, obj: Category) -> None:
        self.db.delete(obj)
        self.db.commit()