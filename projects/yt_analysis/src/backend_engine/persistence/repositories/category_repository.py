from sqlalchemy.orm import Session

from ..models.category import Category


class CategoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_category(self, name: str) -> Category:
        db_category = Category(name=name)
        self.db.add(db_category)
        self.db.commit()
        self.db.refresh(db_category)
        return db_category

    def get_category_by_id(self, category_id: int) -> Category | None:
        return self.db.query(Category).filter(Category.id == category_id).first()

    def get_category_by_name(self, name: str) -> Category | None:
        return self.db.query(Category).filter(Category.name == name).first()

    def get_all_categories(self) -> list[Category]:
        return self.db.query(Category).all()

    def update_category(self, category_id: int, new_name: str) -> Category | None:
        db_category = self.get_category_by_id(category_id)
        if db_category:
            db_category.name = new_name
            self.db.commit()
            self.db.refresh(db_category)
            return db_category
        return None

    def delete_category(self, category_id: int) -> bool:
        db_category = self.get_category_by_id(category_id)
        if db_category:
            self.db.delete(db_category)
            self.db.commit()
            return True
        return False

    def initialize_default_categories(self, default_categories: list[str]):
        for category_name in default_categories:
            if not self.get_category_by_name(category_name):
                self.create_category(category_name)
