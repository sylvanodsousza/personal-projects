import os
import requests
import time
import pandas as pd
from dotenv import load_dotenv
from textblob import TextBlob
from yt_api import get_channel_id, get_last_5_videos
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# Load API key
load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")

def get_video_comments(video_id, max_comments=700):
    comments = []
    url = "https://www.googleapis.com/youtube/v3/commentThreads"
    params = {
        "part": "snippet",
        "videoId": video_id,
        "maxResults": 100,
        "textFormat": "plainText",
        "key": API_KEY
    }

    while len(comments) < max_comments:
        response = requests.get(url, params=params)
        data = response.json()

        if "items" not in data:
            break

        for item in data["items"]:
            comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
            if len(comment.strip()) > 10:
                comments.append(comment)
            if len(comments) >= max_comments:
                break

        if "nextPageToken" in data:
            params["pageToken"] = data["nextPageToken"]
        else:
            break

        time.sleep(0.3)  # small delay to avoid rate limit

    return comments

def analyze_sentiment(comments):
    results = {"positive": 0, "negative": 0, "neutral": 0}
    for comment in comments:
        analysis = TextBlob(comment)
        polarity = analysis.sentiment.polarity
        if polarity > 0:
            results["positive"] += 1
        elif polarity < 0:
            results["negative"] += 1
        else:
            results["neutral"] += 1
    return results

def generate_wordcloud(comments, title):
    text = " ".join(comments[:1000])  # limit to 1000 comments to reduce render time
    if not text.strip():
        print(f"⚠️ No content to generate word cloud for {title}")
        return
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
    plt.figure(figsize=(12, 6))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis("off")
    plt.title(title, fontsize=16)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    channel_name = input("Enter the YouTube Channel Name: ")
    channel_id = get_channel_id(channel_name)

    if not channel_id:
        print("❌ Channel not found.")
        exit()

    video_df = get_last_5_videos(channel_id)
    print(f"✅ Found {len(video_df)} videos. Fetching comments and aggregating sentiment...")

    all_comments = []
    all_sentiment = {"positive": 0, "negative": 0, "neutral": 0}

    for idx, row in video_df.iterrows():
        video_id = row["video_id"]
        print(f"\n🎥 [{idx+1}] {row['title']}")
        print(f"🔍 Fetching comments for video ID: {video_id}")
        comments = get_video_comments(video_id)
        print(f"💬 Fetched {len(comments)} comments")

        sentiment = analyze_sentiment(comments)
        all_sentiment["positive"] += sentiment["positive"]
        all_sentiment["negative"] += sentiment["negative"]
        all_sentiment["neutral"] += sentiment["neutral"]

        all_comments.extend(comments)

    print("\n📊 Combined Sentiment Analysis:", all_sentiment)
    print("\n☁️ Generating Word Cloud...")
    generate_wordcloud(all_comments, "Overall Word Cloud")
