# /home/ubuntu/reddit_dashboard/src/scrape_reddit.py

#!/home/ubuntu/reddit_dashboard/venv/bin/python
# -*- coding: utf-8 -*-

import praw
import pandas as pd
import os
from datetime import datetime, timezone
from supabase import create_client, Client

# --- Configuration ---
CLIENT_ID = "zz9MKUZecOZ6-UtRvT_pIw"
CLIENT_SECRET = "oRkOanOABFmpoBio3neFHhnuOUQVAQ"
USER_AGENT = "linux:my_reddit_dashboard_scraper:v1.0 (by /u/IllFox8126)"

# Supabase configuration
SUPABASE_URL = "https://mcvnrkoogobezgjcsivw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1jdm5ya29vZ29iZXpnamNzaXZ3Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NzgzMjIyNCwiZXhwIjoyMDYzNDA4MjI0fQ.D-uJysR1NPx1gZNdHPiNdjgFlZ1lLTJB_dJ2exopD_E"
BUCKET_NAME = "redditdashboard"

# Subreddit to scrape
SUBREDDIT_NAME = "popular"
# Number of posts to fetch
POST_LIMIT = 100
# Output directory and file name
OUTPUT_DIR = "/home/wmfs0449/reddit_dashboard/data"
today = datetime.now()
today_date = today.strftime("%Y%m%d")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, f"reddit_trends_{today_date}.csv")

def upload_to_supabase(file_path):
    """Upload le fichier CSV vers un bucket Supabase"""
    try:
        # Initialiser le client Supabase
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

        # Nom du fichier dans le bucket
        file_name = os.path.basename(file_path)

        # Ouvrir et lire le fichier
        with open(file_path, 'rb') as f:
            file_content = f.read()

        # Upload vers Supabase Storage
        response = supabase.storage.from_(BUCKET_NAME).upload(
            path=file_name,
            file=file_content,
            file_options={"content-type": "text/csv"}
        )

        print(f"File successfully uploaded to Supabase bucket '{BUCKET_NAME}'")
        return True
    except Exception as e:
        print(f"Error uploading to Supabase: {e}")
        return False

def scrape_reddit_trends():
    """Scrapes top posts from a specified subreddit and saves them to a CSV file."""
    print(f"Initializing Reddit API connection...")
    try:
        reddit = praw.Reddit(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            user_agent=USER_AGENT,
        )
        print(f"Reddit API connection successful (Read-Only: {reddit.read_only})")
    except Exception as e:
        print(f"Error connecting to Reddit API: {e}")
        return

    print(f"Fetching top {POST_LIMIT} posts from r/{SUBREDDIT_NAME}...")
    subreddit = reddit.subreddit(SUBREDDIT_NAME)
    posts_data = []

    try:
        for post in subreddit.hot(limit=POST_LIMIT):
            # Correction pour l'erreur UTC - utilisation de timezone.utc
            created_time = datetime.fromtimestamp(post.created_utc, tz=timezone.utc).isoformat()

            posts_data.append({
                "id": post.id,
                "title": post.title,
                "score": post.score,
                "num_comments": post.num_comments,
                "subreddit": post.subreddit.display_name,
                "url": post.url,
                "permalink": f"https://reddit.com{post.permalink}",
                "created_utc": created_time,
                "flair": post.link_flair_text,
                "is_video": post.is_video,
                "is_self": post.is_self,
                "domain": post.domain,
                "author": str(post.author),
                "scrape_date": today.strftime("%Y-%m-%d")  # Ajout de la date de scraping
            })
        print(f"Successfully fetched {len(posts_data)} posts.")
    except Exception as e:
        print(f"Error fetching posts from r/{SUBREDDIT_NAME}: {e}")
        return

    if not posts_data:
        print("No posts fetched. Exiting.")
        return

    # Create DataFrame
    df = pd.DataFrame(posts_data)

    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Save to CSV
    try:
        df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')
        print(f"Data saved successfully to {OUTPUT_FILE}")

        # Upload to Supabase
        upload_to_supabase(OUTPUT_FILE)
    except Exception as e:
        print(f"Error saving data to CSV: {e}")

if __name__ == "__main__":
    # Check if API credentials are placeholders
    if CLIENT_ID == "YOUR_CLIENT_ID" or CLIENT_SECRET == "YOUR_CLIENT_SECRET":
        print("\n*** WARNING: Reddit API credentials are placeholders! ***")
        print("Please update CLIENT_ID, CLIENT_SECRET, and USER_AGENT in the script.")
        print("You can obtain credentials from: https://www.reddit.com/prefs/apps")
        print("Script will not run with placeholder credentials.\n")
    else:
        scrape_reddit_trends()

