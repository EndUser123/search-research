from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..persistence.database import get_db
from ..services.channel_service import Channel as APIChannel
from ..services.channel_service import ChannelService
from .schemas import (
    ChannelCreate,
    ChannelUpdate,
    VideoCreate,  # Alias Video as APIVideo
    VideoUpdate,
)
from .schemas import Video as APIVideo

router = APIRouter()


# Dependency to get ChannelService
def get_channel_service(db: Session = Depends(get_db)) -> ChannelService:
    return ChannelService(db)


# --- Channel Endpoints ---


@router.post(
    "/channels/", response_model=APIChannel, status_code=status.HTTP_201_CREATED
)
def create_channel(
    channel: ChannelCreate,
    channel_service: ChannelService = Depends(get_channel_service),
):
    try:
        new_channel = channel_service.add_channel(
            channel_url=str(channel.channel_url), categories=channel.assigned_categories
        )
        return new_channel
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/channels/", response_model=list[APIChannel])
def get_all_channels(channel_service: ChannelService = Depends(get_channel_service)):
    return channel_service.get_all_channels()


@router.get("/channels/{channel_id}", response_model=APIChannel)
def get_channel(
    channel_id: str, channel_service: ChannelService = Depends(get_channel_service)
):
    channel = channel_service.get_channel(channel_id)
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found"
        )
    return channel


@router.put("/channels/{channel_id}", response_model=APIChannel)
def update_channel(
    channel_id: str,
    channel_update: ChannelUpdate,
    channel_service: ChannelService = Depends(get_channel_service),
):
    try:
        updated_channel = channel_service.update_channel(channel_id, channel_update)
        if not updated_channel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found"
            )
        return updated_channel
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/channels/{channel_id}", status_code=status.HTTP_200_OK)
def delete_channel(
    channel_id: str, channel_service: ChannelService = Depends(get_channel_service)
):
    if not channel_service.delete_channel(channel_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found"
        )
    return {"message": "Channel deleted successfully"}


# --- Video Endpoints ---


@router.post(
    "/channels/{channel_id}/videos",
    response_model=APIVideo,
    status_code=status.HTTP_201_CREATED,
)
def add_video_to_channel(
    channel_id: str,
    video: VideoCreate,
    channel_service: ChannelService = Depends(get_channel_service),
):
    try:
        new_video = channel_service.add_video_to_channel(channel_id, video)
        return new_video
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error: " + str(e),
        )


@router.get("/channels/{channel_id}/videos", response_model=list[APIVideo])
def get_videos_for_channel(
    channel_id: str, channel_service: ChannelService = Depends(get_channel_service)
):
    videos = channel_service.get_videos_for_channel(channel_id)
    return videos


@router.get("/videos/{video_id}", response_model=APIVideo)
def get_video(
    video_id: str, channel_service: ChannelService = Depends(get_channel_service)
):
    video = channel_service.get_video(video_id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Video not found"
        )
    return video


@router.put("/videos/{video_id}", response_model=APIVideo)
def update_video(
    video_id: str,
    video_update: VideoUpdate,
    channel_service: ChannelService = Depends(get_channel_service),
):
    try:
        updated_video = channel_service.update_video(video_id, video_update)
        if not updated_video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Video not found"
            )
        return updated_video
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/videos/{video_id}", status_code=status.HTTP_200_OK)
def delete_video(
    video_id: str, channel_service: ChannelService = Depends(get_channel_service)
):
    if not channel_service.delete_video(video_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Video not found"
        )
    return {"message": "Video deleted successfully"}
