import os
import streamlit as st
import matplotlib.pyplot as plt
import plotly.express as px
from dotenv import load_dotenv

from yt_api import get_channel_id, get_last_5_videos, get_subscriber_count
from sentiment import get_video_comments, analyze_sentiment, generate_wordcloud

# Load API Key
load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")
st.write(f"🔑 API Key Loaded: {API_KEY[:10]}...")

# UI
st.title("📺 YouTube Comment Analyzer")

channel_name = st.text_input("Enter YouTube Channel Name", value="MrBeast")
budget = st.number_input("Enter Proposed Budget (USD)", min_value=1)

if st.button("Analyze"):
    channel_id = get_channel_id(channel_name)

    if not channel_id:
        st.error("❌ Channel not found.")
    else:
        @st.cache_data(show_spinner=False)
        def get_videos_cached(cid):
            return get_last_5_videos(cid)

        df = get_videos_cached(channel_id)

        # Cost Per View
        total_views = df["views"].sum()
        cpv = budget / total_views if total_views else 0
        st.metric("💰 Estimated Cost per View", f"${cpv:.4f}")

        # Add subscriber counts
        subscriber_counts = []
        for _ in df.itertuples():
            count = get_subscriber_count(channel_id)
            subscriber_counts.append(count)
        df["subscribers"] = subscriber_counts

        # Views Bar Chart
        st.subheader("📈 Views per Video")
        fig_views = px.bar(df, x="title", y="views", text="views", labels={"title": "Video Title"}, height=400)
        fig_views.update_traces(marker_color="lightskyblue", textposition="outside")
        fig_views.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_views, use_container_width=True)

        # Subscriber Growth Line Chart
        st.subheader("👥 Estimated Subscriber Growth Over Last 5 Videos")
        fig_subs = px.line(df, x="title", y="subscribers", markers=True, labels={"title": "Video Title"}, height=400)
        fig_subs.update_traces(line_color="mediumseagreen")
        fig_subs.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_subs, use_container_width=True)

        # Analyze Comments & Sentiment
        all_comments = []
        all_sentiment = {"positive": 0, "negative": 0, "neutral": 0}

        with st.spinner("Analyzing comments..."):
            for _, row in df.iterrows():
                st.write(f"📥 Fetching comments for: `{row['title']}`")
                comments = get_video_comments(row["video_id"])
                sentiment_counts, categorized = analyze_sentiment(comments)

                all_comments.extend(comments)
                all_sentiment["positive"] += sentiment_counts["positive"]
                all_sentiment["negative"] += sentiment_counts["negative"]
                all_sentiment["neutral"] += sentiment_counts["neutral"]

                # Show example comments
                with st.expander(f"💬 Positive Comments: {len(categorized['positive'])}"):
                    for c in categorized["positive"][:3]:
                        st.write(f"👍 {c}")

                with st.expander(f"💬 Negative Comments: {len(categorized['negative'])}"):
                    for c in categorized["negative"][:3]:
                        st.write(f"👎 {c}")

                with st.expander(f"💬 Neutral Comments: {len(categorized['neutral'])}"):
                    for c in categorized["neutral"][:3]:
                        st.write(f"😐 {c}")

        # Sentiment Breakdown Summary
        st.subheader("📊 Overall Sentiment Breakdown")
        st.write(all_sentiment)

        # Word Cloud for all comments
        st.subheader("☁️ Word Cloud for All Comments")
        generate_wordcloud(all_comments, "Overall Comment Word Cloud")



