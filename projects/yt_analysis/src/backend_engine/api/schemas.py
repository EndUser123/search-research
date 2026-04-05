from datetime import datetime

from pydantic import BaseModel, HttpUrl


class CategoryBase(BaseModel):
    name: str


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(CategoryBase):
    pass


class Category(CategoryBase):
    id: int
    date_created: datetime

    class Config:
        from_attributes = True


class ChannelBase(BaseModel):
    channel_id: str
    channel_name: str | None = None
    channel_url: HttpUrl
    assigned_categories: list[str] = []
    upload_playlist_id: str | None = None
    last_scanned_date: datetime | None = None


class ChannelCreate(BaseModel):
    channel_url: HttpUrl
    assigned_categories: list[str] = []


class ChannelUpdate(BaseModel):
    channel_name: str | None = None
    channel_url: HttpUrl | None = None
    assigned_categories: list[str] | None = None
    upload_playlist_id: str | None = None
    last_scanned_date: datetime | None = None


class Channel(ChannelBase):
    date_added_to_ytap: datetime
    last_scanned_date: datetime | None = None

    class Config:
        from_attributes = True


class VideoBase(BaseModel):
    video_id: str
    channel_id: str
    video_title: str
    video_url: HttpUrl
    publication_date: datetime | None = None
    duration: str | None = None
    view_count: int | None = None
    transcript_status: str
    transcript_source: str | None = None
    transcript_file_path: str | None = None
    automated_quality_indicators: list[str] | None = None
    manual_quality_flag: str | None = None
    manual_quality_note: str | None = None
    assigned_categories: list[int] = []  # Stored as JSON string of category IDs


class VideoCreate(VideoBase):
    pass


class VideoUpdate(BaseModel):
    video_title: str | None = None
    video_url: HttpUrl | None = None
    publication_date: datetime | None = None
    duration: str | None = None
    view_count: int | None = None
    transcript_status: str | None = None
    transcript_source: str | None = None
    transcript_file_path: str | None = None
    automated_quality_indicators: list[str] | None = None
    manual_quality_flag: str | None = None
    manual_quality_note: str | None = None
    assigned_categories: list[int] | None = None


class Video(VideoBase):
    date_added_to_ytap: datetime
    last_processed_date: datetime

    class Config:
        from_attributes = True
