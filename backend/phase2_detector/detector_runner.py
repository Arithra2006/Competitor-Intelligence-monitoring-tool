# backend/phase2_detector/detector_runner.py
# Master runner for Phase 2 — ties embedder, ChromaDB, and similarity checker together
# Takes Phase 1 output, returns meaningful changes for Phase 3 classifier

import sys
import os
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import init_db, get_latest_snapshot, get_competitor_by_id, get_all_competitors
from models.snapshot import DetectedChange
from embedder import generate_embedding
from chroma_client import store_embedding, get_stored_embedding
from similarity_checker import is_meaningful_change, batch_check_similarities


# ─────────────────────────────────────────
# MAIN RUNNER
# ─────────────────────────────────────────

def run_detector_for_competitor(
    competitor_id: int,
    scraped_data: list,
) -> list[DetectedChange]:
    """
    Run Phase 2 detector for a single competitor.
    Takes list of RawScrapedData from Phase 1.
    Returns list of DetectedChange objects for Phase 3.

    Args:
        competitor_id: ID of the competitor
        scraped_data: List of RawScrapedData objects from Phase 1

    Returns:
        List of DetectedChange objects — only meaningful changes
    """
    competitor = get_competitor_by_id(competitor_id)
    name = competitor["name"] if competitor else f"ID:{competitor_id}"

    print(f"\n{'='*55}")
    print(f"🧠 Starting detector for: {name}")
    print(f"   Sources to check : {len(scraped_data)}")
    print(f"   Started at       : {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"{'='*55}")

    if not scraped_data:
        print("⚠️  No scraped data received — skipping detector")
        return []

    detected_changes = []

    for data in scraped_data:
        print(f"\n── Checking source: {data.source} ──")
        try:
            # Get old text from SQLite for before/after comparison
            old_snapshot = get_latest_snapshot(competitor_id, data.source)

            # If this is the very first crawl, no old text exists
            if old_snapshot is None:
                old_text = ""
                print(f"   📌 First crawl for {data.source} — storing baseline")
            else:
                old_text = old_snapshot.get("raw_text", "")

            # Run similarity check + threshold filter
            change = is_meaningful_change(
                competitor_id=competitor_id,
                source=data.source,
                url=data.url,
                new_text=data.raw_text,
                old_text=old_text,
            )

            if change:
                detected_changes.append(change)
                print(f"   ✅ Passed filter — queued for classification")
            else:
                print(f"   ⏭️  Filtered out — no meaningful change")

        except Exception as e:
            print(f"   ❌ Detector failed for {data.source}: {e}")
            continue

    # Summary
    print(f"\n{'─'*55}")
    print(f"🧠 Detector complete for: {name}")
    print(f"   Sources checked  : {len(scraped_data)}")
    print(f"   Changes detected : {len(detected_changes)}")
    if detected_changes:
        print(f"   Changed sources  : {[c.source for c in detected_changes]}")
    print(f"{'─'*55}\n")

    return detected_changes


def run_detector_for_all(all_scraped: dict) -> dict:
    """
    Run detector for ALL competitors.
    Takes dict from Phase 1 runner, returns dict for Phase 3.

    Args:
        all_scraped: {competitor_id: [RawScrapedData, ...]}

    Returns:
        {competitor_id: [DetectedChange, ...]}
    """
    all_changes = {}

    for competitor_id, scraped_data in all_scraped.items():
        changes = run_detector_for_competitor(competitor_id, scraped_data)
        all_changes[competitor_id] = changes

    total_changes = sum(len(v) for v in all_changes.values())
    print(f"\n🏁 Detector complete — {total_changes} total changes across all competitors")
    return all_changes


# ─────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────

if __name__ == "__main__":
    import asyncio
    import sys

    # Add phase1 to path
    sys.path.append(os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "phase1_collector"
    ))

    from collector_runner import run_collector_for_competitor
    from database import get_all_competitors

    init_db()

    print("🧪 Testing Phase 2 Detector — full pipeline run\n")

    # Get first competitor from DB
    competitors = get_all_competitors()
    if not competitors:
        print("❌ No competitors in database.")
        print("   Run collector_runner.py first to add Notion as test competitor.")
        sys.exit(1)

    competitor = competitors[0]
    print(f"📋 Using competitor: {competitor['name']}")

    # Run Phase 1 first to get fresh scraped data
    print("\n⏳ Running Phase 1 collector first...")
    scraped_data = asyncio.run(run_collector_for_competitor(competitor))
    print(f"✅ Phase 1 complete — {len(scraped_data)} sources collected")

    # Run Phase 2 detector
    print("\n⏳ Running Phase 2 detector...")
    changes = run_detector_for_competitor(competitor["id"], scraped_data)

    # Final summary
    print("\n" + "="*55)
    print("📊 PHASE 2 COMPLETE — SUMMARY")
    print("="*55)
    print(f"  Sources scraped  : {len(scraped_data)}")
    print(f"  Changes detected : {len(changes)}")
    if changes:
        for c in changes:
            print(f"  🔴 {c.source:<10} | similarity: {c.similarity_score:.4f} | {c.change_magnitude()}")
    else:
        print("  ✅ No meaningful changes detected — all sources stable")
    print("="*55)