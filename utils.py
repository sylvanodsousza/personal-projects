import os
import requests
from textblob import TextBlob
from wordcloud import WordCloud
import tempfile
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")

def get_video_comments(video_id, max_comments=500):
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
        response = requests.get(url, params=params).json()

        items = response.get("items", [])
        comments.extend(
            item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
            for item in items
            if len(item["snippet"]["topLevelComment"]["snippet"]["textDisplay"].strip()) > 10
        )

        if len(comments) >= max_comments or "nextPageToken" not in response:
            break

        params["pageToken"] = response["nextPageToken"]

    return comments[:max_comments]


def analyze_sentiment(comments):
    results = {"positive": 0, "negative": 0, "neutral": 0}
    categorized = {"positive": [], "negative": [], "neutral": []}

    for comment in comments:
        polarity = TextBlob(comment).sentiment.polarity
        if polarity > 0:
            results["positive"] += 1
            categorized["positive"].append(comment)
        elif polarity < 0:
            results["negative"] += 1
            categorized["negative"].append(comment)
        else:
            results["neutral"] += 1
            categorized["neutral"].append(comment)
    return results, categorized


def generate_wordcloud_image(comments):
    if not comments:
        return None
    text = " ".join(comments)
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
    _, tmp_path = tempfile.mkstemp(suffix=".png")
    wordcloud.to_file(tmp_path)
    return tmp_path

