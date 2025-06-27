import os
import requests
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from shiny import App, ui, render, reactive

# --- API Key (Hardcoded) ---
API_KEY = "AIzaSyDbGw1-yEfPxrYJoxUvRAyp-T_f8Sc-Yzg"
print("🔑 API Key Loaded:", API_KEY)

# --- YouTube API Utilities ---
def get_channel_id(channel_name):
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": channel_name,
        "type": "channel",
        "key": API_KEY
    }
    response = requests.get(url, params=params).json()
    try:
        return response["items"][0]["snippet"]["channelId"]
    except Exception as e:
        print(f"Error fetching channel ID: {e}")
        return None

def get_last_5_videos(channel_id):
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "channelId": channel_id,
        "maxResults": 5,
        "order": "date",
        "type": "video",
        "key": API_KEY
    }
    response = requests.get(url, params=params).json()
    videos = []
    for item in response.get("items", []):
        if "videoId" in item["id"]:
            videos.append({
                "video_id": item["id"]["videoId"],
                "title": item["snippet"]["title"]
            })
    return videos

def get_video_stats(video_id):
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "statistics",
        "id": video_id,
        "key": API_KEY
    }
    response = requests.get(url, params=params).json()
    stats = response.get("items", [{}])[0].get("statistics", {})
    return {
        "views": int(stats.get("viewCount", 0)),
        "comments": int(stats.get("commentCount", 0)),
        "likes": int(stats.get("likeCount", 0))
    }

def get_comments(video_id, max_comments=200):
    comments = []
    url = "https://www.googleapis.com/youtube/v3/commentThreads"
    params = {
        "part": "snippet",
        "videoId": video_id,
        "key": API_KEY,
        "maxResults": 100,
        "textFormat": "plainText"
    }
    while len(comments) < max_comments:
        response = requests.get(url, params=params).json()
        if "items" not in response:
            break
        for item in response["items"]:
            comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
            comments.append(comment)
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
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    return fig

# --- UI Layout ---
app_ui = ui.page_fluid(
    ui.h2("📊 YouTube Channel Analyzer"),
    ui.input_text("channel", "Enter Channel Name:", value="MrBeast"),
    ui.input_numeric("budget", "Enter Budget ($):", value=1000),
    ui.input_action_button("analyze_btn", "Analyze", class_="btn-primary"),
    ui.hr(),
    ui.output_text("cpv_output"),
    ui.output_plot("views_plot"),
    ui.output_plot("subs_plot"),
    ui.output_plot("wordcloud_plot"),
)

# --- Server Logic ---
def server(input, output, session):

    @reactive.event(input.analyze_btn)
    def fetch_data():
        channel_id = get_channel_id(input.channel())
        if not channel_id:
            return None, None, None
        videos = get_last_5_videos(channel_id)
        if not videos:
            return None, None, None
        stats_data = []
        for v in videos:
            stats = get_video_stats(v["video_id"])
            stats_data.append({
                "title": v["title"],
                "views": stats["views"]
            })
        comments = []
        for v in videos:
            comments.extend(get_comments(v["video_id"]))
        return videos, pd.DataFrame(stats_data), comments

    @output
    @render.text
    def cpv_output():
        _, video_df, _ = fetch_data()
        if video_df is None or video_df.empty:
            return "No data to calculate CPV."
        total_views = video_df["views"].sum()
        cpv = input.budget() / total_views if total_views else 0
        return f"💰 Cost Per View (CPV): ${cpv:.4f}"

    @output
    @render.plot
    def views_plot():
        _, video_df, _ = fetch_data()
        if video_df is None or video_df.empty:
            return
        fig, ax = plt.subplots()
        ax.bar(video_df["title"], video_df["views"], color="skyblue")
        ax.set_title("Views on Last 5 Videos")
        ax.set_xlabel("Video Title")
        ax.set_ylabel("Views")
        plt.xticks(rotation=45, ha="right")
        return fig

    @output
    @render.plot
    def subs_plot():
        videos, _, _ = fetch_data()
        if not videos:
            return
        titles = [v["title"] for v in videos]
        subs = [1000 + i * 300 for i in range(len(videos))]
        fig, ax = plt.subplots()
        ax.plot(titles, subs, marker="o", color="green")
        ax.set_title("Simulated Subscriber Growth")
        ax.set_xlabel("Video Title")
        ax.set_ylabel("Subscribers")
        plt.xticks(rotation=45, ha="right")
        return fig

    @output
    @render.plot
    def wordcloud_plot():
        _, _, comments = fetch_data()
        if not comments:
            return
        return generate_wordcloud(comments)

# --- Run App ---
app = App(app_ui, server)
