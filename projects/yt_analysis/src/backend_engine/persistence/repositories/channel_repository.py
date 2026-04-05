import json

from sqlalchemy.orm import Session

from ..models.channel import Channel, Video


class ChannelRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_channel(self, channel: Channel) -> Channel:
        self.db.add(channel)
        self.db.commit()
        self.db.refresh(channel)
        return channel

    def get_channel_by_id(self, channel_id: str) -> Channel | None:
        return self.db.query(Channel).filter(Channel.channel_id == channel_id).first()

    def get_all_channels(self) -> list[Channel]:
        return self.db.query(Channel).all()

    def update_channel_categories(
        self, channel_id: str, categories: list[str]
    ) -> Channel | None:
        db_channel = self.get_channel_by_id(channel_id)
        if db_channel:
            db_channel.assigned_categories = json.dumps(categories)
            self.db.commit()
            self.db.refresh(db_channel)
            return db_channel
        return None

    def delete_channel(self, channel_id: str) -> bool:
        db_channel = self.get_channel_by_id(channel_id)
        if db_channel:
            self.db.delete(db_channel)
            self.db.commit()
            return True
        return False


class VideoRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_video(self, video: Video) -> Video:
        self.db.add(video)
        self.db.commit()
        self.db.refresh(video)
        return video

    def get_video_by_id(self, video_id: str) -> Video | None:
        return self.db.query(Video).filter(Video.video_id == video_id).first()

    def get_videos_by_channel_id(self, channel_id: str) -> list[Video]:
        return self.db.query(Video).filter(Video.channel_id == channel_id).all()

    def get_all_videos(self) -> list[Video]:
        return self.db.query(Video).all()

    def update_video_status(self, video_id: str, status: str) -> Video | None:
        db_video = self.get_video_by_id(video_id)
        if db_video:
            db_video.transcript_status = status
            self.db.commit()
            self.db.refresh(db_video)
            return db_video
        return None

    def delete_video(self, video_id: str) -> bool:
        db_video = self.get_video_by_id(video_id)
        if db_video:
            self.db.delete(db_video)
            self.db.commit()
            return True
        return False
