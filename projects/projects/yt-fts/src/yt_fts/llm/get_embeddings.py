import uuid
from collections.abc import Generator

# from openai import OpenAI  # Lazy import below
from datetime import datetime

from rich.console import Console
from rich.progress import track

from yt_fts.core.database import (
    get_channel_name_from_id,
    get_metadata_from_db,
    get_subs_by_video_id,
    get_vid_ids_by_channel_id,
)
from yt_fts.utils import get_model_config, time_to_secs


class EmbeddingsHandler:

    def __init__(self, interval: int = 10) -> None:
        """
        Initialize the embeddings processor.

        Args:
            interval: Time interval in seconds for chunking.

        Returns:
            None
        """
        self.interval = interval
        self.console = Console()

        channel_name = get_channel_name_from_id(channel_id)
        channel_video_ids = [video_id[0] for video_id
                             in get_vid_ids_by_channel_id(channel_id)]

        formatted_segments = []
        for video_id in channel_video_ids:

            split_subs = self.split_subtitles(video_id)
            video_meta_data = get_metadata_from_db(video_id)

            if split_subs is None:
                continue

            for segment in split_subs:
                if segment["text"] == "":
                    continue

                text_with_meta_data = self.add_meta_data_to_text(
                    channel_name,
                    video_meta_data["video_title"],
                    video_meta_data["video_date"],
                    segment
                )
                formatted_segments.append({
                    "channel_name": channel_name,
                    "channel_id": channel_id,
                    "video_title": video_meta_data["video_title"],
                    "video_date": video_meta_data["video_date"].strftime("%Y-%m-%d"),
                    "video_id": video_id,
                    "start_time": segment["start_time"],
                    "text": segment["text"],
                    "text_with_meta_data": text_with_meta_data,
                })


        from openai import OpenAI
        client = OpenAI(api_key=model["api_key"], base_url=model["base_url"])

        embedding_gen = self.get_embedding(
            text_list=[segment["text_with_meta_data"] for segment in formatted_segments],
            model=model["embedding_model"],
            client=client
        )

        embeddings = list(track(embedding_gen, description="Getting embeddings"))
        meta_data = []
        uuids = []
        documents = []
        for segment_object in formatted_segments:
            documents.append(segment_object["text"])
            meta_data.append({
                "channel_id": segment_object["channel_id"],
                "channel_name": segment_object["channel_name"],
                "video_id": segment_object["video_id"],
                "start_time": segment_object["start_time"],
                "video_title": segment_object["video_title"],
                "video_date": segment_object["video_date"],
            })
            uuids.append(str(uuid.uuid4()))


            collection.add(
                documents=documents[i:j],
                embeddings=embeddings[i:j],
                metadatas=meta_data[i:j],
                ids=uuids[i:j]
            )

    def add_meta_data_to_text(self,
                              channel_name: str,
                              video_title: str,
                              video_date: datetime.date,
                              segment: dict[str, str]) -> str:
        """
        Add metadata context to subtitle text segments.

        Args:
            channel_name: Channel name for context.
            video_title: Video title for context.
            video_date: Video publication date.
            segment: Subtitle segment dict with text and timing.

        Returns:
            Text with metadata prepended.
        """
        metadata = {
            "video_title": video_title,
            "channel_name": channel_name,
            "video_date": video_date,
            "segment_start_time": segment["start_time"]
        }

        text_with_metadata = "---\n"
        text_with_metadata += "\n".join([f"{key}: {value}" for key, value in metadata.items()])
        text_with_metadata += f"\n---\n\nContent:\n\n{segment['text']}"

        return text_with_metadata

    def split_subtitles(self, video_id: str) -> list[dict[str, str]] | None:
        """
        Split subtitles into chunks for embedding.

        Args:
            video_id: Video identifier.

        Returns:
            List of subtitle chunks or None if error.
        """
        raw_subtitles = get_subs_by_video_id(video_id)

        if len(raw_subtitles) == 0:
            print(f"Error: No subtitles found for video: {video_id}")
            return None

        total_seconds = time_to_secs(raw_subtitles[-1][1])

        if total_seconds < self.interval:
            self.console.print(f"https://youtu.be/{video_id} is too short to split with the given interval.")
            return None

        # Convert timestamps to seconds and store texts
        segments_with_seconds = []
        for start_timestamp, _stop_timestamp, text in raw_subtitles:
            segments_with_seconds.append({
                "start_timestamp": start_timestamp,
                "start_seconds": self.time_to_seconds(start_timestamp),
                "text": text
            })

        # Split texts into intervals based on self.interval
        segment_intervals = {}
        for sub_obj in segments_with_seconds:

            split_interval = int(sub_obj["start_seconds"] // self.interval) * self.interval

            if split_interval not in segment_intervals:
                segment_intervals[split_interval] = {
                    "start_time": sub_obj["start_timestamp"],
                    "texts": []
                }

            segment_intervals[split_interval]["texts"].append(sub_obj["text"])

        # Combine texts within each interval
        combined_intervals = []
        for interval_obj in segment_intervals.values():
            combined_text = " ".join(interval_obj["texts"]).strip()

            combined_intervals.append({
                "start_time": interval_obj["start_time"],
                "text": combined_text
            })

        return combined_intervals

    def get_embedding(self, text_list: list[str], model: str, client: OpenAI | None = None, batch_size: int = 100) -> Generator[list[float], None, None]:
        """
        Generate embeddings for text using OpenAI API.

        Args:
            text_list: List of text strings to embed.
            model: Embedding model name.
            client: OpenAI client instance.
            batch_size: Number of texts to process per batch.

        Returns:
            Generator yielding embedding vectors.
        """
        if client is None:
            model_config = get_model_config()
            from openai import OpenAI
            client = OpenAI(
                api_key=model_config["api_key"],
                base_url=model_config["base_url"]
            )

        text_list = [text.replace("\n", " ") for text in text_list]

        for i in range(0, len(text_list), batch_size):
            batch = text_list[i:i + batch_size]
            response = client.embeddings.create(input=batch, model=model).data
            embeddings = [data.embedding for data in response]
            yield from embeddings

    def time_to_seconds(self, time_str: str) -> float:
        """ Convert time string to total seconds """
        time_obj = datetime.strptime(time_str, "%H:%M:%S.%f").time()
        return (time_obj.hour * 3600 +
                time_obj.minute * 60 +
                time_obj.second +
                time_obj.microsecond / 1e6)
