# backend/phase1_collector/careers_scraper.py
# Scrapes competitor careers/jobs page using Playwright + BeautifulSoup
# Detects hiring signals — role titles, departments, locations, job count

import asyncio
import re
import sys
import os

try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    pass

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import insert_snapshot
from models.competitor import RawScrapedData


# ─────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────

TIMEOUT_MS = 30000
MAX_TEXT_LENGTH = 50000

# Keywords that indicate AI/ML hiring — high signal
AI_KEYWORDS = [
    "machine learning", "artificial intelligence", "llm", "large language model",
    "nlp", "natural language", "deep learning", "ml engineer", "ai engineer",
    "data scientist", "mlops", "generative ai", "prompt engineer"
]

# Keywords that indicate expansion hiring — medium signal
EXPANSION_KEYWORDS = [
    "apac", "emea", "latam", "asia pacific", "europe", "sales director",
    "regional manager", "country manager", "market expansion", "growth"
]


# ─────────────────────────────────────────
# MAIN SCRAPER FUNCTION
# ─────────────────────────────────────────

async def scrape_careers(competitor_id: int, url: str) -> RawScrapedData | None:
    """
    Scrape the competitor's careers page.
    Extracts job listings, detects hiring signals.

    Args:
        competitor_id: ID of the competitor in the database
        url: Full URL of the careers page

    Returns:
        RawScrapedData object with job text + metadata, or None on failure
    """
    print(f"💼 Scraping careers page: {url}")

    raw_text, metadata = await _fetch_careers_text(url)

    if not raw_text:
        print(f"⚠️  No text extracted from careers page {url} — skipping.")
        return None

    # Save snapshot to SQLite
    insert_snapshot(
        competitor_id=competitor_id,
        source="careers",
        url=url,
        raw_text=raw_text,
    )

    print(f"✅ Careers page scraped — {metadata.get('job_count', 0)} jobs detected from {url}")

    return RawScrapedData(
        competitor_id=competitor_id,
        source="careers",
        url=url,
        raw_text=raw_text,
        metadata=metadata,
    )


# ─────────────────────────────────────────
# INTERNAL HELPERS
# ─────────────────────────────────────────

async def _fetch_careers_text(url: str):
    """
    Load careers page with Playwright, extract job listings text.
    Returns (raw_text, metadata) tuple.
    """
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)

            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 800},
            )

            page = await context.new_page()
            await page.route("**/*", _block_unnecessary_resources)

            try:
                await page.goto(url, timeout=TIMEOUT_MS, wait_until="domcontentloaded")
            except PlaywrightTimeout:
                print(f"⚠️  Timeout loading careers page {url}")
                await browser.close()
                return None, {}

            # Careers pages often lazy-load jobs — wait longer
            await asyncio.sleep(3)

            # Try scrolling to trigger lazy load
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)

            html_content = await page.content()
            await browser.close()

        raw_text, metadata = _extract_jobs_from_html(html_content, url)
        return raw_text, metadata

    except Exception as e:
        print(f"❌ Error scraping careers page {url}: {e}")
        return None, {}


async def _block_unnecessary_resources(route, request):
    """Block images, fonts, media to speed up scraping."""
    blocked_types = {"image", "media", "font", "stylesheet"}
    if request.resource_type in blocked_types:
        await route.abort()
    else:
        await route.continue_()


def _extract_jobs_from_html(html: str, url: str) -> tuple:
    """
    Extract job listings and hiring signals from careers page HTML.
    Returns (clean_text, metadata_dict).
    """
    soup = BeautifulSoup(html, "html.parser")

    # Count job links BEFORE stripping anything — look for <a> tags
    # whose href suggests a job posting. Done first because
    # decompose() below removes elements we might need to inspect.
    job_count_estimate = _count_job_links(soup)

    # Remove noise
    for tag in soup(["script", "style", "nav", "footer",
                     "header", "meta", "noscript", "svg", "img"]):
        tag.decompose()

    text = soup.get_text(separator=" ", strip=True)
    text = re.sub(r"\s+", " ", text).strip()

    if len(text) > MAX_TEXT_LENGTH:
        text = text[:MAX_TEXT_LENGTH]

    # Build metadata — signals for the scorer
    metadata = _analyze_hiring_signals(text, url, job_count_estimate)

    return text, metadata


def _count_job_links(soup: BeautifulSoup) -> int:
    """
    Count likely job postings by looking at link structure,
    not exact English phrases. Much more robust across
    differently-worded careers pages (Greenhouse, Lever, Ashby, etc.)
    than matching specific words like "Apply".
    """
    job_keywords_in_url = ["job", "career", "position", "opening", "role", "opportunit"]

    candidate_links = set()

    for link in soup.find_all("a", href=True):
        href = link["href"].lower()
        link_text = link.get_text(strip=True)

        # Skip empty or clearly non-job links (nav, social, etc.)
        if not link_text or len(link_text) < 3:
            continue

        # A link is a likely job posting if its URL contains job-related keywords
        if any(kw in href for kw in job_keywords_in_url):
            candidate_links.add(href)

    return len(candidate_links)


def _analyze_hiring_signals(text: str, url: str, job_count_estimate: int) -> dict:
    """
    Analyze extracted text for hiring signals.
    Returns structured metadata dict.
    """
    text_lower = text.lower()

    # Detect AI hiring signals
    ai_signals = [kw for kw in AI_KEYWORDS if kw in text_lower]

    # Detect expansion signals
    expansion_signals = [kw for kw in EXPANSION_KEYWORDS if kw in text_lower]

    # Detect engineering vs sales ratio signal
    eng_count = text_lower.count("engineer") + text_lower.count("developer")
    sales_count = text_lower.count("sales") + text_lower.count("account executive")

    metadata = {
        "job_count": job_count_estimate,
        "ai_hiring_signals": ai_signals,
        "ai_hiring_detected": len(ai_signals) > 0,
        "expansion_signals": expansion_signals,
        "expansion_detected": len(expansion_signals) > 0,
        "engineering_mentions": eng_count,
        "sales_mentions": sales_count,
        "source_url": url,
    }

    # Log what we found
    if ai_signals:
        print(f"   🤖 AI hiring signals detected: {ai_signals}")
    if expansion_signals:
        print(f"   🌍 Expansion signals detected: {expansion_signals}")

    return metadata


# ─────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────

if __name__ == "__main__":
    from database import init_db

    init_db()

    if len(sys.argv) == 3:
        comp_id = int(sys.argv[1])
        test_url = sys.argv[2]
    else:
        comp_id = 1
        test_url = "https://www.notion.so/careers"

    result = asyncio.run(scrape_careers(comp_id, test_url))

    if result:
        print("\n--- RESULT ---")
        print(f"Source   : {result.source}")
        print(f"URL      : {result.url}")
        print(f"Chars    : {len(result.raw_text)}")
        print(f"Metadata : {result.metadata}")
        print(f"Preview  : {result.raw_text[:300]}...")
    else:
        print("❌ Careers scraping failed.")