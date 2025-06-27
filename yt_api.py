import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")
print(f"🔑 API Key Loaded: {API_KEY}")


def get_channel_id(channel_name):
    search_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": channel_name,
        "type": "channel",
        "key": API_KEY,
        "maxResults": 1
    }
    response = requests.get(search_url, params=params).json()
    print("🔍 Search result:", response)

    if "items" in response and response["items"]:
        return response["items"][0]["snippet"]["channelId"]
    return None


def get_last_5_videos(channel_id):
    try:
        uploads_url = "https://www.googleapis.com/youtube/v3/channels"
        uploads_params = {
            "part": "contentDetails",
            "id": channel_id,
            "key": API_KEY
        }
        uploads_response = requests.get(uploads_url, params=uploads_params).json()
        uploads_playlist = uploads_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

        playlist_items_url = "https://www.googleapis.com/youtube/v3/playlistItems"
        playlist_params = {
            "part": "snippet",
            "playlistId": uploads_playlist,
            "maxResults": 5,
            "key": API_KEY
        }
        videos_response = requests.get(playlist_items_url, params=playlist_params).json()

        video_data = []
        for item in videos_response.get("items", []):
            try:
                video_id = item["snippet"]["resourceId"]["videoId"]
                title = item["snippet"]["title"]
                published = item["snippet"]["publishedAt"]

                # Get view count
                stats_url = "https://www.googleapis.com/youtube/v3/videos"
                stats_params = {
                    "part": "statistics",
                    "id": video_id,
                    "key": API_KEY
                }
                stats_response = requests.get(stats_url, params=stats_params).json()
                view_count = int(stats_response["items"][0]["statistics"].get("viewCount", 0))

                video_data.append({
                    "video_id": video_id,
                    "title": title,
                    "published": published,
                    "views": view_count
                })
            except Exception as e:
                print(f"⚠️ Skipped one video due to error: {e}")

        return pd.DataFrame(video_data)

    except Exception as e:
        print(f"❌ Error fetching videos: {e}")
        return pd.DataFrame()


def get_subscriber_count(channel_id):
    stats_url = "https://www.googleapis.com/youtube/v3/channels"
    params = {
        "part": "statistics",
        "id": channel_id,
        "key": API_KEY
    }
    response = requests.get(stats_url, params=params).json()
    return int(response["items"][0]["statistics"].get("subscriberCount", 0))


if __name__ == "__main__":
    name = input("Enter YouTube Channel Name: ")
    cid = get_channel_id(name)
    if cid:
        df = get_last_5_videos(cid)
        print(df)
        subs = get_subscriber_count(cid)
        print(f"👥 Subscriber Count: {subs}")
    else:
        print("❌ Channel not found.")
