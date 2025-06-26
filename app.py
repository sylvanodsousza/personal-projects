import os
import pandas as pd
from dotenv import load_dotenv
from shiny import App, ui, reactive, render
from yt_api import get_channel_id, get_last_5_videos
from utils import get_video_comments, analyze_sentiment, generate_wordcloud_image

load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")

def compute_cpv_cr(df, budget):
    avg_views = df["views"].mean()
    cpv = budget / avg_views if avg_views else 0
    cpr = cpv * 1.5
    return cpv, cpr

app_ui = ui.page_fluid(
    ui.h2("📊 YouTube Sentiment Analyzer + Cost Insights"),
    ui.input_text("channel", "Enter YouTube Channel Name", placeholder="e.g. MrBeast"),
    ui.input_numeric("budget", "Partnership Budget ($)", 1000),
    ui.input_action_button("go", "Analyze", class_="btn-primary"),
    ui.output_text("summary"),
    ui.output_ui("wc_overall_ui"),
    ui.output_ui("wc_positive_ui")
)

def server(input, output, session):
    overall_img_path = reactive.Value(None)
    pos_img_path = reactive.Value(None)

    @reactive.event(input.go)
    def run_analysis():
        name = input.channel().strip()
        budget = input.budget()
        cid = get_channel_id(name)

        if not cid:
            output.summary.set("❌ Channel not found.")
            overall_img_path.set(None)
            pos_img_path.set(None)
            return

        df = get_last_5_videos(cid)
        if df.empty:
            output.summary.set("❌ No recent videos found.")
            overall_img_path.set(None)
            pos_img_path.set(None)
            return

        all_comments = []
        all_sentiment = {"positive": 0, "negative": 0, "neutral": 0}
        categorized = {"positive": [], "negative": [], "neutral": []}

        for _, row in df.iterrows():
            comments = get_video_comments(row["video_id"])
            sentiment, cat = analyze_sentiment(comments)

            for key in all_sentiment:
                all_sentiment[key] += sentiment[key]
                categorized[key].extend(cat[key])

            all_comments.extend(comments)

        cpv, cpr = compute_cpv_cr(df, budget)

        output.summary.set(
            f"✅ Analyzed 5 videos from '{name}'.\n"
            f"💬 Total Comments: {len(all_comments)}\n"
            f"Sentiment → 👍 {all_sentiment['positive']} | 👎 {all_sentiment['negative']} | 😐 {all_sentiment['neutral']}\n"
            f"💰 Estimated CPV: ${cpv:.4f} | CPR: ${cpr:.4f}"
        )

        overall_img_path.set(generate_wordcloud_image(all_comments))
        pos_img_path.set(generate_wordcloud_image(categorized["positive"]))

    @output
    @render.ui
    def wc_overall_ui():
        if overall_img_path.get():
            return ui.output_image("wc_overall")
        return ui.span("")

    @output
    @render.ui
    def wc_positive_ui():
        if pos_img_path.get():
            return ui.output_image("wc_positive")
        return ui.span("")

    @output
    @render.image
    def wc_overall():
        path = overall_img_path.get()
        if path:
            return {"src": path, "width": "100%"}
        return None

    @output
    @render.image
    def wc_positive():
        path = pos_img_path.get()
        if path:
            return {"src": path, "width": "100%"}
        return None

app = App(app_ui, server)



