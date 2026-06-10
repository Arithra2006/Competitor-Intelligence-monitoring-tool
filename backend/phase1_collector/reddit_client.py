# backend/phase1_collector/reddit_client.py
# Fetches Reddit discussions mentioning a competitor
# Uses Reddit public JSON API — no API key needed for read-only access

import requests
import re
from datetime import datetime, timezone
import time
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import insert_snapshot
from models.competitor import RawScrapedData


# ─────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────

REDDIT_BASE = "https://www.reddit.com"
MAX_POSTS = 15        # Top 15 posts per search
MAX_TEXT_LENGTH = 50000

# Subreddits most likely to have competitor discussions
TARGET_SUBREDDITS = [
    "SaaS", "startups", "entrepreneur", "ProductManagement",
    "software", "technology", "artificial", "MachineLearning"
]

# Sentiment signal keywords
NEGATIVE_KEYWORDS = [
    "slow", "buggy", "expensive", "overpriced", "switching",
    "leaving", "cancelled", "terrible", "frustrating", "broken",
    "down", "outage", "issue", "problem", "hate", "disappointed"
]

POSITIVE_KEYWORDS = [
    "love", "amazing", "great", "fast", "recommend", "switched to",
    "best", "excellent", "impressed", "perfect", "fantastic", "worth it"
]

COMPETITOR_THREAT_KEYWORDS = [
    "better than", "switching from", "alternative to", "replaced",
    "moved from", "compared to", "vs ", "versus"
]


# ─────────────────────────────────────────
# MAIN CLIENT FUNCTION
# ─────────────────────────────────────────

def get_reddit_signals(competitor_id: int, keyword: str) -> RawScrapedData | None:
    """
    Reddit API requires approval as of 2026.
    Skipped in v1 — returns None gracefully.
    Pipeline continues with other 4 sources.
    """
    print(f"⏭️  Reddit skipped for '{keyword}' — API approval required.")
    return None

    raw_text = _build_raw_text(keyword, posts)

    # Save snapshot to SQLite
    url = f"{REDDIT_BASE}/search.json?q={keyword}"
    insert_snapshot(
        competitor_id=competitor_id,
        source="reddit",
        url=url,
        raw_text=raw_text,
    )

    print(f"✅ Reddit signals fetched — {metadata.get('post_count', 0)} posts for '{keyword}'")

    return RawScrapedData(
        competitor_id=competitor_id,
        source="reddit",
        url=url,
        raw_text=raw_text,
        metadata=metadata,
    )


# ─────────────────────────────────────────
# INTERNAL HELPERS
# ─────────────────────────────────────────

def _fetch_reddit_posts(keyword: str) -> tuple:
    """
    Fetch posts from Reddit search using public JSON API.
    Returns (posts_list, metadata_dict).
    """
    try:
        headers = {
            "User-Agent": "CompetitorIntelligenceBot/1.0 (research tool)"
        }

        # Use Reddit's public search endpoint
        url = f"{REDDIT_BASE}/search.json"
        params = {
            "q": keyword,
            "sort": "new",
            "limit": MAX_POSTS,
            "type": "link",
            "t": "month",    # Posts from last month only
        }

        # Reddit rate limits — be polite
        time.sleep(1)

        response = requests.get(url, headers=headers, params=params, timeout=15)

        if response.status_code == 429:
            print(f"   ⚠️  Reddit rate limited — waiting 5 seconds...")
            time.sleep(5)
            response = requests.get(url, headers=headers, params=params, timeout=15)

        if response.status_code != 200:
            print(f"   ❌ Reddit API returned status {response.status_code}")
            return [], {}

        data = response.json()
        raw_posts = data.get("data", {}).get("children", [])

        if not raw_posts:
            return [], {}

        posts = []
        for post in raw_posts:
            post_data = post.get("data", {})
            posts.append({
                "title": post_data.get("title", ""),
                "text": _clean_text(post_data.get("selftext", "")),
                "subreddit": post_data.get("subreddit", ""),
                "score": post_data.get("score", 0),
                "num_comments": post_data.get("num_comments", 0),
                "url": post_data.get("url", ""),
                "created_utc": post_data.get("created_utc", 0),
                "upvote_ratio": post_data.get("upvote_ratio", 0),
            })

        metadata = _analyze_reddit_signals(posts, keyword)
        return posts, metadata

    except Exception as e:
        print(f"❌ Error fetching Reddit posts for '{keyword}': {e}")
        return [], {}


def _analyze_reddit_signals(posts: list, keyword: str) -> dict:
    """
    Analyze posts for sentiment and competitive signals.
    Returns structured metadata dict.
    """
    all_text = " ".join([
        p["title"] + " " + p["text"]
        for p in posts
    ]).lower()

    negative_signals = [kw for kw in NEGATIVE_KEYWORDS if kw in all_text]
    positive_signals = [kw for kw in POSITIVE_KEYWORDS if kw in all_text]
    threat_signals = [kw for kw in COMPETITOR_THREAT_KEYWORDS if kw in all_text]

    # High engagement posts — score > 100
    high_engagement = [p for p in posts if p["score"] > 100]

    # Average sentiment score
    total_score = sum(p["score"] for p in posts)
    avg_score = total_score / len(posts) if posts else 0

    # Most active subreddits
    subreddits = list(set([p["subreddit"] for p in posts]))

    metadata = {
        "keyword": keyword,
        "post_count": len(posts),
        "high_engagement_posts": len(high_engagement),
        "average_score": round(avg_score, 1),
        "subreddits_found": subreddits,
        "negative_signals": negative_signals,
        "negative_sentiment_detected": len(negative_signals) > 0,
        "positive_signals": positive_signals,
        "positive_sentiment_detected": len(positive_signals) > 0,
        "threat_signals": threat_signals,
        "competitive_threat_detected": len(threat_signals) > 0,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }

    # Log signals
    if negative_signals:
        print(f"   👎 Negative signals: {negative_signals}")
    if positive_signals:
        print(f"   👍 Positive signals: {positive_signals}")
    if threat_signals:
        print(f"   ⚔️  Competitive threat signals: {threat_signals}")
    if high_engagement:
        print(f"   🔥 High engagement posts: {len(high_engagement)}")

    return metadata


def _build_raw_text(keyword: str, posts: list) -> str:
    """
    Build single text block from all Reddit posts.
    This is what gets embedded and compared in Phase 2.
    """
    parts = [f"Reddit Discussions — Keyword: {keyword}\n"]

    for i, post in enumerate(posts, 1):
        created = datetime.fromtimestamp(
            post["created_utc"], tz=timezone.utc
        ).strftime("%Y-%m-%d") if post["created_utc"] else "unknown"

        parts.append(
            f"Post {i}: {post['title']} | "
            f"Subreddit: r/{post['subreddit']} | "
            f"Score: {post['score']} | "
            f"Comments: {post['num_comments']} | "
            f"Date: {created} | "
            f"Text: {post['text'][:300]}"
        )

    return "\n\n".join(parts)


def _clean_text(text: str) -> str:
    """Clean Reddit post text — remove markdown and extra whitespace."""
    # Remove markdown links
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    # Remove markdown formatting
    text = re.sub(r"[*_~`#>]", "", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ─────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────

if __name__ == "__main__":
    from database import init_db

    init_db()

    if len(sys.argv) == 3:
        comp_id = int(sys.argv[1])
        keyword = sys.argv[2]
    else:
        comp_id = 1
        keyword = "Notion app"

    result = get_reddit_signals(comp_id, keyword)

    if result:
        print("\n--- RESULT ---")
        print(f"Source      : {result.source}")
        print(f"Chars       : {len(result.raw_text)}")
        print(f"Posts       : {result.metadata.get('post_count', 0)}")
        print(f"Avg Score   : {result.metadata.get('average_score', 0)}")
        print(f"Subreddits  : {result.metadata.get('subreddits_found', [])}")
        print(f"Negative    : {result.metadata.get('negative_signals', [])}")
        print(f"Positive    : {result.metadata.get('positive_signals', [])}")
        print(f"Threats     : {result.metadata.get('threat_signals', [])}")
        print(f"\nPreview:\n{result.raw_text[:400]}...")
    else:
        print("❌ Reddit fetch failed.")