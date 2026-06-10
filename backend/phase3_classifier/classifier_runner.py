
# backend/phase3_classifier/classifier_runner.py
# Master runner for Phase 3 — ties classifier and snapshot store together
# Takes Phase 2 output (DetectedChange list), returns ClassifiedSignal list

import sys
import os
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import init_db, get_all_competitors, get_competitor_by_id
from models.snapshot import DetectedChange
from models.signal import ClassifiedSignal
from change_classifier import classify_changes_batch
from snapshot_store import save_classified_snapshots_batch


# ─────────────────────────────────────────
# MAIN RUNNER
# ─────────────────────────────────────────

def run_classifier_for_competitor(
    competitor_id: int,
    detected_changes: list[DetectedChange],
) -> list[ClassifiedSignal]:
    """
    Run Phase 3 classifier for a single competitor.
    Takes DetectedChange list from Phase 2.
    Returns ClassifiedSignal list for Phase 4.

    Args:
        competitor_id: ID of the competitor
        detected_changes: List of DetectedChange objects from Phase 2

    Returns:
        List of ClassifiedSignal objects
    """
    competitor = get_competitor_by_id(competitor_id)
    name = competitor["name"] if competitor else f"ID:{competitor_id}"

    print(f"\n{'='*55}")
    print(f"🔬 Starting classifier for: {name}")
    print(f"   Changes to classify : {len(detected_changes)}")
    print(f"   Started at          : {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"{'='*55}")

    if not detected_changes:
        print("⚠️  No changes to classify — skipping")
        return []

    # Step 1 — Classify all changes using Groq
    classified_signals = classify_changes_batch(detected_changes)

    if not classified_signals:
        print("⚠️  No signals classified successfully")
        return []

    # Step 2 — Save all classified signals to SQLite
    save_classified_snapshots_batch(classified_signals)

    # Summary
    print(f"\n{'─'*55}")
    print(f"🔬 Classifier complete for: {name}")
    print(f"   Changes received : {len(detected_changes)}")
    print(f"   Signals classified : {len(classified_signals)}")
    for s in classified_signals:
        print(f"   {s.priority_emoji()} {s.source:<10} → {s.change_type}")
    print(f"{'─'*55}\n")

    return classified_signals


def run_classifier_for_all(all_changes: dict) -> dict:
    """
    Run classifier for ALL competitors.
    Takes dict from Phase 2, returns dict for Phase 4.

    Args:
        all_changes: {competitor_id: [DetectedChange, ...]}

    Returns:
        {competitor_id: [ClassifiedSignal, ...]}
    """
    all_signals = {}

    for competitor_id, changes in all_changes.items():
        signals = run_classifier_for_competitor(competitor_id, changes)
        all_signals[competitor_id] = signals

    total = sum(len(v) for v in all_signals.values())
    print(f"\n🏁 Classifier complete — {total} total signals across all competitors")
    return all_signals


# ─────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────

if __name__ == "__main__":
    import asyncio
    import sys

    # Add phase1 and phase2 to path
    sys.path.append(os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "phase1_collector"
    ))
    sys.path.append(os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "phase2_detector"
    ))

    from collector_runner import run_collector_for_competitor
    from detector_runner import run_detector_for_competitor
    from database import get_all_competitors

    init_db()

    print("🧪 Testing Phase 3 Classifier — full pipeline run\n")

    # Get first competitor
    competitors = get_all_competitors()
    if not competitors:
        print("❌ No competitors in database.")
        print("   Run collector_runner.py first.")
        sys.exit(1)

    competitor = competitors[0]
    print(f"📋 Using competitor: {competitor['name']}")

    # Phase 1 — Collect
    print("\n⏳ Running Phase 1 collector...")
    scraped_data = asyncio.run(run_collector_for_competitor(competitor))
    print(f"✅ Phase 1 complete — {len(scraped_data)} sources")

    # Phase 2 — Detect
    print("\n⏳ Running Phase 2 detector...")
    detected_changes = run_detector_for_competitor(competitor["id"], scraped_data)
    print(f"✅ Phase 2 complete — {len(detected_changes)} changes detected")

    # Phase 3 — Classify
    print("\n⏳ Running Phase 3 classifier...")
    signals = run_classifier_for_competitor(competitor["id"], detected_changes)

    # Final summary
    print("\n" + "="*55)
    print("📊 PHASE 3 COMPLETE — SUMMARY")
    print("="*55)
    print(f"  Sources scraped    : {len(scraped_data)}")
    print(f"  Changes detected   : {len(detected_changes)}")
    print(f"  Signals classified : {len(signals)}")
    if signals:
        print(f"\n  Classified signals:")
        for s in signals:
            print(f"  {s.priority_emoji()} {s.source:<10} → {s.change_type:<30} | confidence: {s.metadata.get('confidence', 0)}%")
    else:
        print("  ✅ No meaningful changes this run")
    print("="*55)