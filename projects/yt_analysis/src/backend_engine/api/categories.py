from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..persistence.database import get_db
from ..persistence.repositories.category_repository import CategoryRepository
from ..persistence.repositories.channel_repository import (
    ChannelRepository,
    VideoRepository,
)
from ..services.channel_service import ChannelService
from .schemas import (
    Category,
    CategoryCreate,
    CategoryUpdate,
    Channel,
)

router = APIRouter()


# Dependency to get ChannelService
def get_channel_service(db: Session = Depends(get_db)) -> ChannelService:
    channel_repo = ChannelRepository(db)
    video_repo = VideoRepository(db)
    category_repo = CategoryRepository(db)
    return ChannelService(channel_repo, video_repo, category_repo)


# --- Category Endpoints ---


@router.post(
    "/categories/", response_model=Category, status_code=status.HTTP_201_CREATED
)
def create_category(
    category: CategoryCreate,
    channel_service: ChannelService = Depends(get_channel_service),
):
    try:
        new_category = channel_service.create_category(category)
        return new_category
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/categories/", response_model=list[Category])
def get_all_categories(channel_service: ChannelService = Depends(get_channel_service)):
    return channel_service.get_all_categories()


@router.get("/categories/{category_name}", response_model=Category)
def get_category_by_name(
    category_name: str, channel_service: ChannelService = Depends(get_channel_service)
):
    category = channel_service.get_category_by_name(category_name)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )
    return category


@router.put("/categories/{category_id}", response_model=Category)
def update_category(
    category_id: int,
    category_update: CategoryUpdate,
    channel_service: ChannelService = Depends(get_channel_service),
):
    updated_category = channel_service.update_category(category_id, category_update)
    if not updated_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )
    return updated_category


@router.delete("/categories/{category_id}", status_code=status.HTTP_200_OK)
def delete_category(
    category_id: int, channel_service: ChannelService = Depends(get_channel_service)
):
    if not channel_service.delete_category(category_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )
    return {"message": "Category deleted successfully"}


# --- Channel-Category Assignment Endpoints ---


@router.post(
    "/channels/{channel_id}/assign_category/{category_id}", response_model=Channel
)
def assign_channel_to_category(
    channel_id: str,
    category_id: int,
    channel_service: ChannelService = Depends(get_channel_service),
):
    try:
        updated_channel = channel_service.assign_channel_to_category(
            channel_id, category_id
        )
        return updated_channel
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/channels/{channel_id}/remove_category", response_model=Channel)
def remove_channel_from_category(
    channel_id: str, channel_service: ChannelService = Depends(get_channel_service)
):
    try:
        updated_channel = channel_service.remove_channel_from_category(channel_id)
        return updated_channel
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
