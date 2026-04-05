from googleapiclient.discovery import build

# Set your YouTube API key here
API_KEY = "YOUR_API_KEY"  # Replace with your actual API key


def get_playlist_videos(playlist_id, max_results=5):
    youtube = build("youtube", "v3", developerKey=API_KEY)

    # Get playlist items
    request = youtube.playlistItems().list(
        part="snippet", playlistId=playlist_id, maxResults=max_results
    )
    response = request.execute()

    videos = []
    for item in response["items"]:
        video = item["snippet"]
        videos.append(
            {
                "title": video["title"],
                "video_id": video["resourceId"]["videoId"],
                "position": video["position"] + 1,
            }
        )

    return videos


if __name__ == "__main__":
    # WL is the special ID for Watch Later playlist
    playlist_id = "WL"
    videos = get_playlist_videos(playlist_id)

    print("First 5 videos in your Watch Later playlist:")
    for video in videos:
        print(
            f"{video['position']}. {video['title']} (https://www.youtube.com/watch?v={video['video_id']})"
        )
