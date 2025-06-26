import os
import requests
import pandas as pd
import tempfile
import streamlit as st
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from wordcloud import WordCloud
from textblob import TextBlob

from yt_api import get_channel_id, get_last_10_videos

load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")


def get_video_comments(video_id, max_comments=5000):
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
            comments.append(comment)

            if len(comments) >= max_comments:
                break

        if "nextPageToken" in data:
            params["pageToken"] = data["nextPageToken"]
        else:
            break

    return comments


def analyze_sentiment(comments):
    results = {"positive": 0, "negative": 0, "neutral": 0}
    categorized = {"positive": [], "negative": [], "neutral": []}
    for comment in comments:
        analysis = TextBlob(comment)
        polarity = analysis.sentiment.polarity
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


def generate_wordcloud(comments, title):
    text = " ".join(comments)
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis("off")
    ax.set_title(title, fontsize=16)
    st.pyplot(fig)


def compute_cpv_cr(df, budget):
    avg_views = df["views"].mean()
    cpv = budget / avg_views if avg_views else 0
    cpr = cpv * 1.5
    return cpv, cpr


# Streamlit UI
st.title("📊 YouTube Sentiment Analyzer + Cost Insights")

channel_name = st.text_input("Enter YouTube Channel Name", "MrBeast")
budget = st.number_input("Partnership Budget ($)", min_value=100, value=1000, step=100)

if st.button("Analyze"):
    cid = get_channel_id(channel_name)
    if not cid:
        st.error("❌ Channel not found.")
    else:
        df = get_last_10_videos(cid)
        all_comments = []
        all_sentiment = {"positive": 0, "negative": 0, "neutral": 0}
        categorized = {"positive": [], "negative": [], "neutral": []}

        with st.spinner("Analyzing videos..."):
            for _, row in df.iterrows():
                video_id = row["video_id"]
                comments = get_video_comments(video_id)
                sentiment, cat = analyze_sentiment(comments)

                all_sentiment["positive"] += sentiment["positive"]
                all_sentiment["negative"] += sentiment["negative"]
                all_sentiment["neutral"] += sentiment["neutral"]

                categorized["positive"].extend(cat["positive"])
                categorized["negative"].extend(cat["negative"])
                categorized["neutral"].extend(cat["neutral"])
                all_comments.extend(comments)

        cpv, cpr = compute_cpv_cr(df, budget)
        st.success(
            f"✅ Analyzed 10 videos from '{channel_name}'.\n\n"
            f"💬 Total Comments: {len(all_comments)}\n"
            f"😊 Positive: {all_sentiment['positive']}, 😡 Negative: {all_sentiment['negative']}, 😐 Neutral: {all_sentiment['neutral']}\n"
            f"💰 Estimated CPV: ${cpv:.4f} | CPR: ${cpr:.4f}"
        )

        st.subheader("📌 Word Clouds")
        generate_wordcloud(all_comments, "Overall Word Cloud")
        generate_wordcloud(categorized["positive"], "Positive Comments Word Cloud")
        generate_wordcloud(categorized["negative"], "Negative Comments Word Cloud")
