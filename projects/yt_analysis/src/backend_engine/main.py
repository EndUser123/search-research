from contextlib import asynccontextmanager

from fastapi import FastAPI

from .api import categories, channels
from .persistence.database import get_db, init_db
from .persistence.repositories.category_repository import CategoryRepository


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the database
    init_db()
    # Initialize default categories
    db = next(get_db())
    category_repo = CategoryRepository(db)
    default_categories = ["Health", "Wealth", "Fitness", "Learning"]
    category_repo.initialize_default_categories(default_categories)
    db.close()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(channels.router, prefix="/api/v1", tags=["channels"])
app.include_router(categories.router, prefix="/api/v1", tags=["categories"])


@app.get("/")
async def root():
    return {"message": "YTAP Backend Engine is running!"}
