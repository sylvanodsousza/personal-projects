# streamlit_app.py
import requests
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import streamlit as st

# --- API Key (Hardcoded, unchanged) ---
API_KEY = "AIzaSyDbGw1-yEfPxrYJoxUvRAyp-T_f8Sc-Yzg"

# --- YouTube API Utilities (unchanged logic) ---
def get_channel_id(channel_name):
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {"part":"snippet","q":channel_name,"type":"channel","key":API_KEY}
    response = requests.get(url, params=params).json()
    try:
        return response["items"][0]["snippet"]["channelId"]
    except Exception as e:
        st.error(f"Error fetching channel ID: {e}")
        return None

def get_last_5_videos(channel_id):
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {"part":"snippet","channelId":channel_id,"maxResults":5,"order":"date","type":"video","key":API_KEY}
    response = requests.get(url, params=params).json()
    videos = []
    for item in response.get("items", []):
        if "videoId" in item["id"]:
            videos.append({"video_id":item["id"]["videoId"],"title":item["snippet"]["title"]})
    return videos

def get_video_stats(video_id):
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {"part":"statistics","id":video_id,"key":API_KEY}
    response = requests.get(url, params=params).json()
    stats = response.get("items", [{}])[0].get("statistics", {})
    to_int = lambda x: int(x) if str(x).isdigit() else 0
    return {"views":to_int(stats.get("viewCount",0)),"comments":to_int(stats.get("commentCount",0)),"likes":to_int(stats.get("likeCount",0))}

def get_comments(video_id, max_comments=200):
    comments = []
    url = "https://www.googleapis.com/youtube/v3/commentThreads"
    params = {"part":"snippet","videoId":video_id,"key":API_KEY,"maxResults":100,"textFormat":"plainText"}
    while len(comments) < max_comments:
        response = requests.get(url, params=params).json()
        if "items" not in response:
            break
        for item in response["items"]:
            c = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
            comments.append(c)
            if len(comments) >= max_comments:
                break
        if "nextPageToken" in response:
            params["pageToken"] = response["nextPageToken"]
        else:
            break
    return comments

def generate_wordcloud(comments):
    text = " ".join(comments) or "No comments"
    wc = WordCloud(width=800, height=400, background_color="white").generate(text)
    fig, ax = plt.subplots()
    ax.imshow(wc, interpolation="bilinear"); ax.axis("off")
    return fig

# --- Streamlit GUI ---
st.title("📊 YouTube Channel Analyzer")

# Placeholder (hint), NOT a default value
channel = st.text_input("Enter Channel Name:", placeholder="e.g. MrBeast")
budget = st.number_input("Enter Budget ($):", value=1000, min_value=0, step=100)

# Do absolutely nothing until Analyze is clicked
run = st.button("Analyze", type="primary")
if not run:
    st.info("Enter a channel and click Analyze to fetch data.")
    st.stop()

# Block if the field is empty after clicking
if not channel.strip():
    st.warning("Please enter a channel name.")
    st.stop()

# --- Run only after button + valid input ---
channel_id = get_channel_id(channel)
if not channel_id:
    st.error("Channel not found.")
    st.stop()

videos = get_last_5_videos(channel_id)
if not videos:
    st.warning("No recent videos found.")
    st.stop()

stats_data, comments = [], []
for v in videos:
    stats = get_video_stats(v["video_id"])
    stats_data.append({"title":v["title"],"views":stats["views"]})
    comments.extend(get_comments(v["video_id"]))
df = pd.DataFrame(stats_data)

# CPV
total_views = df["views"].sum()
cpv = (budget / total_views) if total_views else 0
st.subheader(f"💰 Cost Per View (CPV): ${cpv:.4f}")

# Views plot
st.subheader("Views on Last 5 Videos")
fig, ax = plt.subplots()
ax.bar(df["title"], df["views"], color="skyblue")
ax.set_title("Views on Last 5 Videos"); ax.set_xlabel("Video Title"); ax.set_ylabel("Views")
plt.xticks(rotation=45, ha="right")
st.pyplot(fig)

# Simulated subs plot (unchanged placeholder logic)
st.subheader("Simulated Subscriber Growth")
titles = [v["title"] for v in videos]
subs = [1000 + i*300 for i in range(len(videos))]
fig2, ax2 = plt.subplots()
ax2.plot(titles, subs, marker="o", color="green")
ax2.set_title("Simulated Subscriber Growth"); ax2.set_xlabel("Video Title"); ax2.set_ylabel("Subscribers")
plt.xticks(rotation=45, ha="right")
st.pyplot(fig2)

# Word cloud
st.subheader("Word Cloud of Comments")
if comments:
    st.pyplot(generate_wordcloud(comments))
else:
    st.info("No comments available.")
