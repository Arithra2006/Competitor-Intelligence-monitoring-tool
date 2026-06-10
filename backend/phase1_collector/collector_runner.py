# backend/phase1_collector/collector_runner.py
# Master runner for Phase 1 — runs all 4 scrapers for one competitor
# This is what the scheduler calls every week

import asyncio
import sys
import os
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import init_db, get_all_competitors, get_competitor_by_id
from models.competitor import Competitor, RawScrapedData

from website_scraper import scrape_website
from careers_scraper import scrape_careers
from news_parser import parse_news
from github_client import get_github_signals
from reddit_client import get_reddit_signals


# ─────────────────────────────────────────
# MAIN RUNNER
# ─────────────────────────────────────────

async def run_collector_for_competitor(competitor: dict) -> list[RawScrapedData]:
    """
    Run all 4 scrapers for a single competitor.
    Returns list of RawScrapedData objects — one per source.

    Args:
        competitor: dict from database with all competitor fields

    Returns:
        List of RawScrapedData objects (only successful scrapes)
    """
    comp_id   = competitor["id"]
    name      = competitor["name"]
    website   = competitor["website_url"]
    careers   = competitor["careers_url"]
    github    = competitor["github_org"]
    reddit_kw = competitor["reddit_keyword"]

    print(f"\n{'='*55}")
    print(f"🚀 Starting collection for: {name}")
    print(f"   Started at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"{'='*55}")

    results = []

    # ── 1. Website Scraper ──────────────────────────────
    if website:
        try:
            result = await scrape_website(comp_id, website)
            if result:
                results.append(result)
        except Exception as e:
            print(f"❌ Website scraper failed for {name}: {e}")
    else:
        print("⏭️  No website URL — skipping website scraper")

    # ── 2. Careers Scraper ─────────────────────────────
    if careers:
        try:
            result = await scrape_careers(comp_id, careers)
            if result:
                results.append(result)
        except Exception as e:
            print(f"❌ Careers scraper failed for {name}: {e}")
    else:
        print("⏭️  No careers URL — skipping careers scraper")

    # ── 3. News Parser ─────────────────────────────────
    try:
        result = parse_news(comp_id, name)
        if result:
            results.append(result)
    except Exception as e:
        print(f"❌ News parser failed for {name}: {e}")

    # ── 4. GitHub Client ───────────────────────────────
    if github:
        try:
            result = get_github_signals(comp_id, github)
            if result:
                results.append(result)
        except Exception as e:
            print(f"❌ GitHub client failed for {name}: {e}")
    else:
        print("⏭️  No GitHub org — skipping GitHub client")

    # ── 5. Reddit Client (graceful skip) ───────────────
    if reddit_kw:
        try:
            result = get_reddit_signals(comp_id, reddit_kw)
            if result:
                results.append(result)
        except Exception as e:
            print(f"❌ Reddit client failed for {name}: {e}")
    else:
        print("⏭️  No Reddit keyword — skipping Reddit client")

    # ── Summary ────────────────────────────────────────
    print(f"\n{'─'*55}")
    print(f"✅ Collection complete for: {name}")
    print(f"   Sources collected : {len(results)}/{_count_active_sources(competitor)}")
    print(f"   Sources           : {[r.source for r in results]}")
    print(f"{'─'*55}\n")

    return results


async def run_collector_for_all() -> dict:
    """
    Run collector for ALL competitors in the database.
    Returns dict mapping competitor_id to list of RawScrapedData.
    Called by the weekly scheduler.
    """
    competitors = get_all_competitors()

    if not competitors:
        print("⚠️  No competitors in database. Add one first.")
        return {}

    print(f"\n🔍 Running collection for {len(competitors)} competitor(s)...")

    all_results = {}
    for competitor in competitors:
        results = await run_collector_for_competitor(competitor)
        all_results[competitor["id"]] = results

    print(f"\n🏁 All collections complete — {len(competitors)} competitor(s) processed.")
    return all_results


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────

def _count_active_sources(competitor: dict) -> int:
    """Count how many sources are configured for this competitor."""
    count = 1  # News always runs
    if competitor.get("website_url"):
        count += 1
    if competitor.get("careers_url"):
        count += 1
    if competitor.get("github_org"):
        count += 1
    if competitor.get("reddit_keyword"):
        count += 1
    return count


def add_test_competitor() -> dict:
    """
    Add a test competitor to the database if none exist.
    Uses Notion as the test case.
    """
    from database import insert_competitor
    comp_id = insert_competitor(
        name="Notion",
        website_url="https://notion.so",
        careers_url="https://www.notion.so/careers",
        github_org="notionhq",
        reddit_keyword="Notion app",
        frequency="weekly",
    )
    print(f"✅ Test competitor added — ID: {comp_id}")
    return get_competitor_by_id(comp_id)


# ─────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────

if __name__ == "__main__":
    # Initialize database
    init_db()

    # Check if competitor ID passed as argument
    if len(sys.argv) == 2:
        comp_id = int(sys.argv[1])
        competitor = get_competitor_by_id(comp_id)
        if not competitor:
            print(f"❌ No competitor found with ID {comp_id}")
            sys.exit(1)
    else:
        # Use existing competitors or add test one
        competitors = get_all_competitors()
        if competitors:
            competitor = competitors[0]
            print(f"📋 Using existing competitor: {competitor['name']}")
        else:
            print("📋 No competitors found — adding Notion as test competitor...")
            competitor = add_test_competitor()

    # Run collector
    results = asyncio.run(run_collector_for_competitor(competitor))

    # Final summary
    print("\n" + "="*55)
    print("📊 PHASE 1 COMPLETE — SUMMARY")
    print("="*55)
    for r in results:
        print(f"  ✅ {r.source:<10} | {len(r.raw_text):>6} chars | {r.url[:50]}")
    print(f"\n  Total sources collected: {len(results)}")
    print("="*55)