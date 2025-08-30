# yt_test.py
# NO Streamlit. Prints structured results and shows/saves charts.
# Defaults let you run with no CLI flags; you can still override them.

import argparse
import sys
import requests
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud

# ====== CONFIG ======
API_KEY = "AIzaSyDXtWRGfAPik2k8r0BHgZ6lOy1o6KPT0zI"  # <-- paste your YouTube Data API v3 key here

# ====== YOUTUBE DATA API HELPERS ======
def get_channel_id(channel_name: str):
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": channel_name,
        "type": "channel",
        "key": API_KEY,
        "maxResults": 1,
    }
    r = requests.get(url, params=params)
    data = r.json()
    if "error" in data:
        msg = data["error"].get("message", "Unknown API error")
        raise RuntimeError(f"YouTube API error (search channel): {msg}")
    items = data.get("items", [])
    if not items:
        return None
    item = items[0]
    return {
        "channel_id": item["snippet"]["channelId"],
        "channel_title": item["snippet"]["title"],
        "description": item["snippet"].get("description", ""),
    }

def get_last_5_videos(channel_id: str):
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "channelId": channel_id,
        "maxResults": 5,
        "order": "date",
        "type": "video",
        "key": API_KEY,
    }
    r = requests.get(url, params=params)
    data = r.json()
    if "error" in data:
        msg = data["error"].get("message", "Unknown API error")
        raise RuntimeError(f"YouTube API error (list videos): {msg}")
    vids = []
    for item in data.get("items", []):
        vids.append({
            "video_id": item["id"]["videoId"],
            "title": item["snippet"]["title"],
            "publishedAt": item["snippet"]["publishedAt"],
        })
    return vids

def get_video_stats(video_id: str):
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {"part": "statistics", "id": video_id, "key": API_KEY}
    r = requests.get(url, params=params)
    data = r.json()
    if "error" in data:
        msg = data["error"].get("message", "Unknown API error")
        raise RuntimeError(f"YouTube API error (video stats): {msg}")
    items = data.get("items", [])
    stats = items[0]["statistics"] if items else {}
    def to_int(x):
        try:
            return int(x)
        except:
            return 0
    return {
        "views": to_int(stats.get("viewCount", 0)),
        "likes": to_int(stats.get("likeCount", 0)),
        "comments": to_int(stats.get("commentCount", 0)),
    }

def get_comments(video_id: str, max_comments=200):
    comments = []
    url = "https://www.googleapis.com/youtube/v3/commentThreads"
    params = {
        "part": "snippet",
        "videoId": video_id,
        "key": API_KEY,
        "maxResults": 100,
        "textFormat": "plainText",
    }
    while len(comments) < max_comments:
        r = requests.get(url, params=params)
        data = r.json()
        if "error" in data:
            break  # comments disabled or quota issue — skip gracefully
        items = data.get("items", [])
        if not items:
            break
        for it in items:
            c = it["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
            if c and len(c.strip()) > 5:
                comments.append(c)
            if len(comments) >= max_comments:
                break
        if "nextPageToken" in data and len(comments) < max_comments:
            params["pageToken"] = data["nextPageToken"]
        else:
            break
    return comments

# ====== VISUALIZATIONS ======
def plot_views_bar(df_stats: pd.DataFrame, filename="views_bar.png"):
    fig, ax = plt.subplots()
    ax.bar(df_stats["Title"], df_stats["Views"])
    ax.set_title("Views on Last 5 Videos")
    ax.set_xlabel("Video Title")
    ax.set_ylabel("Views")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(filename, dpi=150)
    plt.show()

def plot_simulated_subs(titles, filename="subs_line.png"):
    subs = [1000 + i * 300 for i in range(len(titles))]
    fig, ax = plt.subplots()
    ax.plot(titles, subs, marker="o")
    ax.set_title("Simulated Subscriber Growth")
    ax.set_xlabel("Video Title")
    ax.set_ylabel("Subscribers")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(filename, dpi=150)
    plt.show()

def plot_wordcloud(comments, filename="wordcloud.png"):
    text = " ".join(comments) if comments else "No comments available"
    wc = WordCloud(width=1000, height=500, background_color="white").generate(text)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(filename, dpi=150)
    plt.show()

def plot_demo_geography(df_demo: pd.DataFrame, filename="demo_geography.png"):
    fig, ax = plt.subplots()
    ax.bar(df_demo["Country"], df_demo["Viewer %"])
    ax.set_title("Audience Geography (Demo Data)")
    ax.set_xlabel("Country")
    ax.set_ylabel("Viewer %")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(filename, dpi=150)
    plt.show()

# ====== MAIN ======
def main():
    parser = argparse.ArgumentParser(description="YouTube CLI Analyzer (no Streamlit)")
    parser.add_argument("--channel", default="MrBeast", help="Channel name (default: MrBeast)")
    parser.add_argument("--budget", type=float, default=1000.0, help="Budget in $ for CPV (default: 1000)")
    args = parser.parse_args()

    if not API_KEY or "PASTE_YOUR_KEY_HERE" in API_KEY:
        print("❌ Please paste your YouTube Data API key into API_KEY at the top of this script.")
        sys.exit(1)

    print(f"🔎 Looking up channel: {args.channel}")
    info = get_channel_id(args.channel)
    if not info:
        print("❌ Channel not found or API error.")
        sys.exit(1)

    print("\n📺 Channel Info")
    print(f"  Title     : {info['channel_title']}")
    print(f"  ChannelID : {info['channel_id']}")
    print(f"  About     : {info['description'][:120]}{'...' if len(info['description'])>120 else ''}")

    videos = get_last_5_videos(info["channel_id"])
    if not videos:
        print("\n⚠️ No videos found.")
        sys.exit(0)

    print("\n🎬 Last 5 Videos")
    for i, v in enumerate(videos, 1):
        print(f"  {i}. {v['title']}")
        print(f"     VideoID   : {v['video_id']}")
        print(f"     Published : {v['publishedAt']}")

    rows, all_comments = [], []
    for v in videos:
        stats = get_video_stats(v["video_id"])
        rows.append({"Title": v["title"], "Views": stats["views"], "Likes": stats["likes"], "Comments": stats["comments"]})
        all_comments.extend(get_comments(v["video_id"]))

    df_stats = pd.DataFrame(rows)

    total_views = int(df_stats["Views"].sum()) if not df_stats.empty else 0
    cpv = (args.budget / total_views) if total_views else 0.0
    print("\n💰 Cost Per View (CPV)")
    print(f"  Budget: ${args.budget:,.2f} | Total Views: {total_views:,} | CPV: ${cpv:,.6f}")

    print("\n📈 Video Stats (Last 5)")
    print(df_stats.to_string(index=False))

    print("\n🖼️ Generating charts (also saved as PNGs)...")
    plot_views_bar(df_stats, "views_bar.png")
    plot_simulated_subs(df_stats["Title"].tolist(), "subs_line.png")
    plot_wordcloud(all_comments, "wordcloud.png")

    demo_df = pd.DataFrame({
        "Country": ["United States", "India", "United Kingdom", "Brazil", "Germany"],
        "Viewer %": [35, 25, 15, 10, 5],
    })
    print("\n🌍 Audience Geography (Demo Data)")
    print(demo_df.to_string(index=False))
    plot_demo_geography(demo_df, "demo_geography.png")

    print("\n✅ Done. Saved: views_bar.png, subs_line.png, wordcloud.png, demo_geography.png")

if __name__ == "__main__":
    main()
