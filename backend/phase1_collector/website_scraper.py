# backend/phase1_collector/website_scraper.py
# Scrapes competitor main website using Playwright + BeautifulSoup
# Extracts clean text content and saves snapshot to SQLite

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

from database import insert_snapshot, get_latest_snapshot
from models.competitor import RawScrapedData


# ─────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────

TIMEOUT_MS = 30000
MAX_TEXT_LENGTH = 50000


# ─────────────────────────────────────────
# MAIN SCRAPER FUNCTION
# ─────────────────────────────────────────

async def scrape_website(competitor_id: int, url: str) -> RawScrapedData | None:
    """
    Scrape the competitor's main website.
    Returns a RawScrapedData object or None if scraping fails.
    """
    print(f"🌐 Scraping website: {url}")

    raw_text = await _fetch_page_text(url)

    if not raw_text:
        print(f"⚠️  No text extracted from {url} — skipping.")
        return None

    insert_snapshot(
        competitor_id=competitor_id,
        source="website",
        url=url,
        raw_text=raw_text,
    )

    print(f"✅ Website scraped and saved — {len(raw_text)} chars from {url}")

    return RawScrapedData(
        competitor_id=competitor_id,
        source="website",
        url=url,
        raw_text=raw_text,
        metadata={"char_count": len(raw_text)},
    )


# ─────────────────────────────────────────
# INTERNAL HELPERS
# ─────────────────────────────────────────

async def _fetch_page_text(url: str) -> str | None:
    """
    Use Playwright to load the page then BeautifulSoup to extract text.
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
                print(f"⚠️  Timeout loading {url}")
                await browser.close()
                return None

            await asyncio.sleep(2)

            html_content = await page.content()
            await browser.close()

        clean_text = _extract_text_from_html(html_content)
        return clean_text

    except Exception as e:
        print(f"❌ Error scraping {url}: {e}")
        return None


async def _block_unnecessary_resources(route, request):
    """Block images, fonts, stylesheets, and media."""
    blocked_types = {"image", "media", "font", "stylesheet"}
    if request.resource_type in blocked_types:
        await route.abort()
    else:
        await route.continue_()


def _extract_text_from_html(html: str) -> str:
    """Extract clean readable text from raw HTML."""
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "nav", "footer",
                     "header", "meta", "noscript", "svg", "img"]):
        tag.decompose()

    text = soup.get_text(separator=" ", strip=True)
    text = re.sub(r"\s+", " ", text).strip()

    if len(text) > MAX_TEXT_LENGTH:
        text = text[:MAX_TEXT_LENGTH]

    return text


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
        test_url = "https://notion.so"

    result = asyncio.run(scrape_website(comp_id, test_url))

    if result:
        print("\n--- RESULT ---")
        print(f"Source   : {result.source}")
        print(f"URL      : {result.url}")
        print(f"Chars    : {len(result.raw_text)}")
        print(f"Preview  : {result.raw_text[:300]}...")
    else:
        print("❌ Scraping failed.")
