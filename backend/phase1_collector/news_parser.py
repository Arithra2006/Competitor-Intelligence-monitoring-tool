# backend/phase1_collector/news_parser.py
# Parses Google News RSS feed for competitor mentions
# No API key needed — completely free

import feedparser
import re
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import insert_snapshot
from models.competitor import RawScrapedData


# ─────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────

GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
MAX_ARTICLES = 10  # Only grab top 10 results per competitor

# High signal keywords in news
FUNDING_KEYWORDS = ["funding", "raises", "series a", "series b", "series c",
                    "million", "billion", "investment", "investor", "vc"]
PRODUCT_KEYWORDS = ["launches", "release", "announces", "new feature",
                    "product update", "partnership", "acquires", "acquisition"]
LEADERSHIP_KEYWORDS = ["appoints", "hires", "ceo", "cto", "coo", "vp",
                       "chief", "joins", "leaves", "resigns", "founder"]


# ─────────────────────────────────────────
# MAIN PARSER FUNCTION
# ─────────────────────────────────────────

def parse_news(competitor_id: int, competitor_name: str) -> RawScrapedData | None:
    """
    Fetch and parse Google News RSS for competitor mentions.
    No API key needed — uses public RSS feed.

    Args:
        competitor_id: ID of the competitor in the database
        competitor_name: Name used to search Google News

    Returns:
        RawScrapedData object with news text + metadata, or None on failure
    """
    print(f"📰 Fetching news for: {competitor_name}")

    articles, metadata = _fetch_news(competitor_name)

    if not articles:
        print(f"⚠️  No news found for {competitor_name} — skipping.")
        return None

    # Build raw text from all article titles + summaries
    raw_text = _build_raw_text(articles)

    # Save snapshot to SQLite
    rss_url = GOOGLE_NEWS_RSS.format(query=competitor_name.replace(" ", "+"))
    insert_snapshot(
        competitor_id=competitor_id,
        source="news",
        url=rss_url,
        raw_text=raw_text,
    )

    print(f"✅ News parsed — {metadata.get('article_count', 0)} articles found for {competitor_name}")

    return RawScrapedData(
        competitor_id=competitor_id,
        source="news",
        url=rss_url,
        raw_text=raw_text,
        metadata=metadata,
    )


# ─────────────────────────────────────────
# INTERNAL HELPERS
# ─────────────────────────────────────────

def _fetch_news(competitor_name: str) -> tuple:
    """
    Fetch RSS feed from Google News and parse articles.
    Returns (articles_list, metadata_dict).
    """
    try:
        rss_url = GOOGLE_NEWS_RSS.format(query=competitor_name.replace(" ", "+"))
        feed = feedparser.parse(rss_url)

        if not feed.entries:
            return [], {}

        articles = []
        for entry in feed.entries[:MAX_ARTICLES]:
            article = {
                "title": entry.get("title", ""),
                "summary": _clean_html(entry.get("summary", "")),
                "link": entry.get("link", ""),
                "published": entry.get("published", ""),
                "source": entry.get("source", {}).get("title", "Unknown"),
            }
            articles.append(article)

        metadata = _analyze_news_signals(articles, competitor_name)
        return articles, metadata

    except Exception as e:
        print(f"❌ Error fetching news for {competitor_name}: {e}")
        return [], {}


def _build_raw_text(articles: list) -> str:
    """
    Combine all article titles and summaries into one text block.
    This is what gets embedded and compared in Phase 2.
    """
    parts = []
    for i, article in enumerate(articles, 1):
        parts.append(
            f"Article {i}: {article['title']} | "
            f"Source: {article['source']} | "
            f"Published: {article['published']} | "
            f"Summary: {article['summary']}"
        )
    return "\n\n".join(parts)


def _clean_html(text: str) -> str:
    """Strip HTML tags from RSS summary text."""
    clean = re.sub(r"<[^>]+>", " ", text)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


def _analyze_news_signals(articles: list, competitor_name: str) -> dict:
    """
    Scan article titles and summaries for high-signal keywords.
    Returns structured metadata dict.
    """
    all_text = " ".join([
        a["title"] + " " + a["summary"]
        for a in articles
    ]).lower()

    funding_signals = [kw for kw in FUNDING_KEYWORDS if kw in all_text]
    product_signals = [kw for kw in PRODUCT_KEYWORDS if kw in all_text]
    leadership_signals = [kw for kw in LEADERSHIP_KEYWORDS if kw in all_text]

    metadata = {
        "competitor_name": competitor_name,
        "article_count": len(articles),
        "articles": articles,
        "funding_signals": funding_signals,
        "funding_detected": len(funding_signals) > 0,
        "product_signals": product_signals,
        "product_detected": len(product_signals) > 0,
        "leadership_signals": leadership_signals,
        "leadership_detected": len(leadership_signals) > 0,
        "fetched_at": datetime.utcnow().isoformat(),
    }

    # Log signals found
    if funding_signals:
        print(f"   💰 Funding signals detected: {funding_signals}")
    if product_signals:
        print(f"   🚀 Product signals detected: {product_signals}")
    if leadership_signals:
        print(f"   👤 Leadership signals detected: {leadership_signals}")

    return metadata


# ─────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────

if __name__ == "__main__":
    from database import init_db

    init_db()

    if len(sys.argv) == 3:
        comp_id = int(sys.argv[1])
        comp_name = sys.argv[2]
    else:
        comp_id = 1
        comp_name = "Notion"

    result = parse_news(comp_id, comp_name)

    if result:
        print("\n--- RESULT ---")
        print(f"Source     : {result.source}")
        print(f"Chars      : {len(result.raw_text)}")
        print(f"Articles   : {result.metadata.get('article_count', 0)}")
        print(f"Funding    : {result.metadata.get('funding_signals', [])}")
        print(f"Product    : {result.metadata.get('product_signals', [])}")
        print(f"Leadership : {result.metadata.get('leadership_signals', [])}")
        print(f"\nPreview:\n{result.raw_text[:400]}...")
    else:
        print("❌ News parsing failed.")