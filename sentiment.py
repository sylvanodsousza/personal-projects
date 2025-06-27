import re
from collections import Counter
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import streamlit as st
from textblob import TextBlob


def get_video_comments(video_id, max_comments=100):
    import os
    import requests
    from dotenv import load_dotenv

    load_dotenv()
    API_KEY = os.getenv("YOUTUBE_API_KEY")

    url = "https://www.googleapis.com/youtube/v3/commentThreads"
    params = {
        "part": "snippet",
        "videoId": video_id,
        "key": API_KEY,
        "maxResults": 100,
        "textFormat": "plainText"
    }

    comments = []
    while len(comments) < max_comments:
        response = requests.get(url, params=params)
        data = response.json()

        if "items" not in data:
            break

        for item in data["items"]:
            try:
                comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                comments.append(comment)
                if len(comments) >= max_comments:
                    break
            except KeyError:
                continue

        if "nextPageToken" in data:
            params["pageToken"] = data["nextPageToken"]
        else:
            break

    return comments


def analyze_sentiment(comments):
    results = {"positive": 0, "negative": 0, "neutral": 0}
    categorized = {"positive": [], "negative": [], "neutral": []}

    for comment in comments:
        polarity = TextBlob(comment).sentiment.polarity
        if polarity > 0.1:
            results["positive"] += 1
            categorized["positive"].append(comment)
        elif polarity < -0.1:
            results["negative"] += 1
            categorized["negative"].append(comment)
        else:
            results["neutral"] += 1
            categorized["neutral"].append(comment)

    return results, categorized


def generate_wordcloud(comments, title="Word Cloud"):
    if not comments:
        st.warning("No comments to generate word cloud.")
        return

    text = " ".join(comments)
    wordcloud = WordCloud(width=800, height=400, background_color="white").generate(text)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wordcloud, interpolation="bilinear")
    ax.axis("off")
    st.pyplot(fig)