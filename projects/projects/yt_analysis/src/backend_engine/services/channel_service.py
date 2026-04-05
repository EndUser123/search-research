import json
import re
from datetime import UTC, datetime

from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session
from src.backend_engine.api.schemas import Channel as APIChannel
from src.backend_engine.api.schemas import (  # Import Pydantic schemas
    ChannelUpdate,
    VideoCreate,
    VideoUpdate,
)
from src.backend_engine.api.schemas import Video as APIVideo
from src.backend_engine.persistence.models.channel import (  # Alias to avoid name collision
    Channel as DBChannel,
)
from src.backend_engine.persistence.models.channel import Video as DBVideo
from src.backend_engine.persistence.repositories.category_repository import (
    CategoryRepository,
)
from src.backend_engine.persistence.repositories.channel_repository import (
    ChannelRepository,
    VideoRepository,
)


class Category(BaseModel):
    category_name: str
    date_created: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Channel(BaseModel):
    channel_id: str
    channel_name: str | None = None
    channel_url: str
    assigned_categories: list[str]
    upload_playlist_id: str | None = None
    last_scanned_date: datetime | None = None
    date_added_to_ytap: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @validator("channel_url")
    def validate_channel_url(cls, url):
        # Basic YouTube channel URL validation
        # This regex is a simplified example. A more robust validation might involve API calls.
        if not re.match(
            r"^(https?://)?(www\.)?(youtube\.com/(channel/|c/|user/)|youtu\.be/)[a-zA-Z0-9_-]+/?$",
            url,
        ):
            raise ValueError("Invalid YouTube channel URL format.")
        return url


class ChannelService:
    def __init__(self, db: Session):
        self.channel_repo = ChannelRepository(db)
        self.category_repo = CategoryRepository(db)
        self.video_repo = VideoRepository(db)  # Initialize VideoRepository

    def add_channel(self, channel_url: str, categories: list[str]) -> Channel:
        # 1. Validate URL format
        if not self.validate_url(channel_url):
            raise ValueError("Invalid YouTube channel URL provided.")

        # 2. Check if channel already exists (by URL or ID if fetched)
        # For simplicity, let's assume we can derive a channel_id from the URL or fetch it.
        # In a real scenario, this would involve a YouTube Data API call.
        # Placeholder for fetching channel_id and channel_name
        # For now, let's mock a channel_id from the URL for demonstration
        mock_channel_id_match = re.search(
            r"(channel/|c/|user/)([a-zA-Z0-9_-]+)", channel_url
        )
        if not mock_channel_id_match:
            raise ValueError("Could not extract channel ID from URL.")
        mock_channel_id = mock_channel_id_match.group(2)
        mock_channel_name = f"Mock Channel Name for {mock_channel_id}"  # Placeholder

        existing_channel = self.channel_repo.get_channel_by_id(mock_channel_id)
        if existing_channel:
            raise ValueError(f"Channel with ID '{mock_channel_id}' already exists.")

        # 3. Validate categories exist (assuming category_repository can do this)
        for category_name in categories:
            if not self.category_repo.get_category_by_name(category_name):
                raise ValueError(f"Category '{category_name}' does not exist.")

        # 4. Create a new Channel instance (Pydantic model)
        new_channel_data = Channel(
            channel_id=mock_channel_id,
            channel_name=mock_channel_name,
            channel_url=channel_url,
            assigned_categories=categories,
            date_added_to_ytap=datetime.now(UTC),
        )

        # 5. Convert Pydantic model to SQLAlchemy model for persistence
        db_channel = DBChannel(
            channel_id=new_channel_data.channel_id,
            channel_name=new_channel_data.channel_name,
            channel_url=new_channel_data.channel_url,
            assigned_categories=json.dumps(
                new_channel_data.assigned_categories
            ),  # Store as JSON string
            upload_playlist_id=new_channel_data.upload_playlist_id,
            last_scanned_date=new_channel_data.last_scanned_date,
            date_added_to_ytap=new_channel_data.date_added_to_ytap,
        )

        # 6. Use the ChannelRepository to save the new channel
        created_db_channel = self.channel_repo.create_channel(db_channel)

        # 7. Convert SQLAlchemy model back to Pydantic model for return
        return Channel(
            channel_id=created_db_channel.channel_id,
            channel_name=created_db_channel.channel_name,
            channel_url=created_db_channel.channel_url,
            assigned_categories=json.loads(
                created_db_channel.assigned_categories
            ),  # Load from JSON string
            upload_playlist_id=created_db_channel.upload_playlist_id,
            last_scanned_date=created_db_channel.last_scanned_date,
            date_added_to_ytap=created_db_channel.date_added_to_ytap,
        )

    def validate_url(self, url: str) -> bool:
        # Basic YouTube channel URL validation
        return bool(
            re.match(
                r"^(https?://)?(www\.)?(youtube\.com/(channel/|c/|user/)|youtu\.be/)[a-zA-Z0-9_-]+/?$",
                url,
            )
        )

    def get_channel(self, channel_id: str) -> APIChannel | None:
        db_channel = self.channel_repo.get_channel_by_id(channel_id)
        if db_channel:
            return APIChannel(
                channel_id=db_channel.channel_id,
                channel_name=db_channel.channel_name,
                channel_url=db_channel.channel_url,
                assigned_categories=json.loads(db_channel.assigned_categories),
                upload_playlist_id=db_channel.upload_playlist_id,
                last_scanned_date=db_channel.last_scanned_date,
                date_added_to_ytap=db_channel.date_added_to_ytap,
            )
        return None

    def get_all_channels(self) -> list[APIChannel]:
        db_channels = self.channel_repo.get_all_channels()
        return [
            APIChannel(
                channel_id=ch.channel_id,
                channel_name=ch.channel_name,
                channel_url=ch.channel_url,
                assigned_categories=json.loads(ch.assigned_categories),
                upload_playlist_id=ch.upload_playlist_id,
                last_scanned_date=ch.last_scanned_date,
                date_added_to_ytap=ch.date_added_to_ytap,
            )
            for ch in db_channels
        ]

    def update_channel(
        self, channel_id: str, channel_update: ChannelUpdate
    ) -> APIChannel | None:
        db_channel = self.channel_repo.get_channel_by_id(channel_id)
        if not db_channel:
            return None

        update_data = channel_update.model_dump(exclude_unset=True)

        if "channel_name" in update_data:
            db_channel.channel_name = update_data["channel_name"]
        if "channel_url" in update_data:
            if not self.validate_url(update_data["channel_url"]):
                raise ValueError("Invalid YouTube channel URL format for update.")
            db_channel.channel_url = update_data["channel_url"]
        if "assigned_categories" in update_data:
            for category_name in update_data["assigned_categories"]:
                if not self.category_repo.get_category_by_name(category_name):
                    raise ValueError(f"Category '{category_name}' does not exist.")
            db_channel.assigned_categories = json.dumps(
                update_data["assigned_categories"]
            )
        if "upload_playlist_id" in update_data:
            db_channel.upload_playlist_id = update_data["upload_playlist_id"]
        if "last_scanned_date" in update_data:
            db_channel.last_scanned_date = update_data["last_scanned_date"]

        updated_db_channel = self.channel_repo.update_channel(db_channel)
        if updated_db_channel:
            return APIChannel(
                channel_id=updated_db_channel.channel_id,
                channel_name=updated_db_channel.channel_name,
                channel_url=updated_db_channel.channel_url,
                assigned_categories=json.loads(updated_db_channel.assigned_categories),
                upload_playlist_id=updated_db_channel.upload_playlist_id,
                last_scanned_date=updated_db_channel.last_scanned_date,
                date_added_to_ytap=updated_db_channel.date_added_to_ytap,
            )
        return None

    def delete_channel(self, channel_id: str) -> bool:
        return self.channel_repo.delete_channel(channel_id)

    def add_video_to_channel(
        self, channel_id: str, video_data: VideoCreate
    ) -> APIVideo:
        # Check if channel exists
        if not self.channel_repo.get_channel_by_id(channel_id):
            raise ValueError(f"Channel with ID '{channel_id}' not found.")

        # Validate categories
        for category_name in video_data.assigned_categories:
            if not self.category_repo.get_category_by_name(category_name):
                raise ValueError(f"Category '{category_name}' does not exist.")

        # Convert Pydantic VideoCreate to DBVideo
        db_video = DBVideo(
            video_id=video_data.video_id,
            channel_id=channel_id,
            video_title=video_data.video_title,
            video_url=str(video_data.video_url),  # Convert HttpUrl to string
            publication_date=video_data.publication_date,
            duration=video_data.duration,
            view_count=video_data.view_count,
            transcript_status=video_data.transcript_status,
            transcript_source=video_data.transcript_source,
            transcript_file_path=video_data.transcript_file_path,
            automated_quality_indicators=json.dumps(
                video_data.automated_quality_indicators
            )
            if video_data.automated_quality_indicators
            else "[]",
            manual_quality_flag=video_data.manual_quality_flag,
            manual_quality_note=video_data.manual_quality_note,
            assigned_categories=json.dumps(video_data.assigned_categories),
        )

        created_db_video = self.video_repo.create_video(db_video)

        return APIVideo(
            video_id=created_db_video.video_id,
            channel_id=created_db_video.channel_id,
            video_title=created_db_video.video_title,
            video_url=created_db_video.video_url,
            publication_date=created_db_video.publication_date,
            duration=created_db_video.duration,
            view_count=created_db_video.view_count,
            transcript_status=created_db_video.transcript_status,
            transcript_source=created_db_video.transcript_source,
            transcript_file_path=created_db_video.transcript_file_path,
            automated_quality_indicators=json.loads(
                created_db_video.automated_quality_indicators
            )
            if created_db_video.automated_quality_indicators
            else [],
            manual_quality_flag=created_db_video.manual_quality_flag,
            manual_quality_note=created_db_video.manual_quality_note,
            date_added_to_ytap=created_db_video.date_added_to_ytap,
            last_processed_date=created_db_video.last_processed_date,
            assigned_categories=json.loads(created_db_video.assigned_categories),
        )

    def get_videos_for_channel(self, channel_id: str) -> list[APIVideo]:
        db_videos = self.video_repo.get_videos_by_channel_id(channel_id)
        return [
            APIVideo(
                video_id=v.video_id,
                channel_id=v.channel_id,
                video_title=v.video_title,
                video_url=v.video_url,
                publication_date=v.publication_date,
                duration=v.duration,
                view_count=v.view_count,
                transcript_status=v.transcript_status,
                transcript_source=v.transcript_source,
                transcript_file_path=v.transcript_file_path,
                automated_quality_indicators=json.loads(v.automated_quality_indicators)
                if v.automated_quality_indicators
                else [],
                manual_quality_flag=v.manual_quality_flag,
                manual_quality_note=v.manual_quality_note,
                date_added_to_ytap=v.date_added_to_ytap,
                last_processed_date=v.last_processed_date,
                assigned_categories=json.loads(v.assigned_categories),
            )
            for v in db_videos
        ]

    def get_video(self, video_id: str) -> APIVideo | None:
        db_video = self.video_repo.get_video_by_id(video_id)
        if db_video:
            return APIVideo(
                video_id=db_video.video_id,
                channel_id=db_video.channel_id,
                video_title=db_video.video_title,
                video_url=db_video.video_url,
                publication_date=db_video.publication_date,
                duration=db_video.duration,
                view_count=db_video.view_count,
                transcript_status=db_video.transcript_status,
                transcript_source=db_video.transcript_source,
                transcript_file_path=db_video.transcript_file_path,
                automated_quality_indicators=json.loads(
                    db_video.automated_quality_indicators
                )
                if db_video.automated_quality_indicators
                else [],
                manual_quality_flag=db_video.manual_quality_flag,
                manual_quality_note=db_video.manual_quality_note,
                date_added_to_ytap=db_video.date_added_to_ytap,
                last_processed_date=db_video.last_processed_date,
                assigned_categories=json.loads(db_video.assigned_categories),
            )
        return None

    def update_video(self, video_id: str, video_update: VideoUpdate) -> APIVideo | None:
        db_video = self.video_repo.get_video_by_id(video_id)
        if not db_video:
            return None

        update_data = video_update.model_dump(exclude_unset=True)

        if "video_title" in update_data:
            db_video.video_title = update_data["video_title"]
        if "video_url" in update_data:
            db_video.video_url = update_data["video_url"]
        if "publication_date" in update_data:
            db_video.publication_date = update_data["publication_date"]
        if "duration" in update_data:
            db_video.duration = update_data["duration"]
        if "view_count" in update_data:
            db_video.view_count = update_data["view_count"]
        if "transcript_status" in update_data:
            db_video.transcript_status = update_data["transcript_status"]
        if "transcript_source" in update_data:
            db_video.transcript_source = update_data["transcript_source"]
        if "transcript_file_path" in update_data:
            db_video.transcript_file_path = update_data["transcript_file_path"]
        if "automated_quality_indicators" in update_data:
            db_video.automated_quality_indicators = json.dumps(
                update_data["automated_quality_indicators"]
            )
        if "manual_quality_flag" in update_data:
            db_video.manual_quality_flag = update_data["manual_quality_flag"]
        if "manual_quality_note" in update_data:
            db_video.manual_quality_note = update_data["manual_quality_note"]
        if "assigned_categories" in update_data:
            for category_name in update_data["assigned_categories"]:
                if not self.category_repo.get_category_by_name(category_name):
                    raise ValueError(f"Category '{category_name}' does not exist.")
            db_video.assigned_categories = json.dumps(
                update_data["assigned_categories"]
            )

        updated_db_video = self.video_repo.update_video(db_video)
        if updated_db_video:
            return APIVideo(
                video_id=updated_db_video.video_id,
                channel_id=updated_db_video.channel_id,
                video_title=updated_db_video.video_title,
                video_url=updated_db_video.video_url,
                publication_date=updated_db_video.publication_date,
                duration=updated_db_video.duration,
                view_count=updated_db_video.view_count,
                transcript_status=updated_db_video.transcript_status,
                transcript_source=updated_db_video.transcript_source,
                transcript_file_path=updated_db_video.transcript_file_path,
                automated_quality_indicators=json.loads(
                    updated_db_video.automated_quality_indicators
                )
                if updated_db_video.automated_quality_indicators
                else [],
                manual_quality_flag=updated_db_video.manual_quality_flag,
                manual_quality_note=updated_db_video.manual_quality_note,
                date_added_to_ytap=updated_db_video.date_added_to_ytap,
                last_processed_date=updated_db_video.last_processed_date,
                assigned_categories=json.loads(updated_db_video.assigned_categories),
            )
        return None

    def delete_video(self, video_id: str) -> bool:
        return self.video_repo.delete_video(video_id)
