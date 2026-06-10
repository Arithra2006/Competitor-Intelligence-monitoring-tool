# backend/phase4_scorer/scorer_runner.py
# Master runner for Phase 4 — ties evidence aggregator and confidence scorer together
# Takes Phase 3 output (ClassifiedSignal list), returns ScoredSignal list for Phase 5

import sys
import os
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import init_db, get_competitor_by_id, get_all_competitors
from models.signal import ClassifiedSignal, ScoredSignal
from evidence_aggregator import aggregate_evidence
from confidence_scorer import calculate_confidence, format_confidence_report


# ─────────────────────────────────────────
# MAIN RUNNER
# ─────────────────────────────────────────

def run_scorer_for_competitor(
    competitor_id: int,
    classified_signals: list[ClassifiedSignal],
) -> list[ScoredSignal]:
    """
    Run Phase 4 scorer for a single competitor.
    Takes ClassifiedSignal list from Phase 3.
    Returns ScoredSignal list for Phase 5.

    Args:
        competitor_id: ID of the competitor
        classified_signals: List of ClassifiedSignal objects from Phase 3

    Returns:
        List of ScoredSignal objects with confidence scores
    """
    competitor = get_competitor_by_id(competitor_id)
    name = competitor["name"] if competitor else f"ID:{competitor_id}"

    print(f"\n{'='*55}")
    print(f"📊 Starting scorer for: {name}")
    print(f"   Signals to score : {len(classified_signals)}")
    print(f"   Started at       : {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"{'='*55}")

    if not classified_signals:
        print("⚠️  No signals to score — skipping")
        return []

    # Step 1 — Aggregate evidence across sources
    evidence_bundles = aggregate_evidence(classified_signals)

    if not evidence_bundles:
        print("⚠️  No evidence bundles built — skipping")
        return []

    # Step 2 — Apply weighted confidence formula
    scored_signals = calculate_confidence(evidence_bundles)

    # Step 3 — Inject competitor_id into each signal
    for signal in scored_signals:
        signal.competitor_id = competitor_id

    # Step 4 — Print confidence report
    print(format_confidence_report(scored_signals))

    # Summary
    print(f"\n{'─'*55}")
    print(f"📊 Scorer complete for: {name}")
    print(f"   Signals scored   : {len(scored_signals)}")
    if scored_signals:
        print(f"   Priority summary : {_priority_summary(scored_signals)}")
    print(f"{'─'*55}\n")

    return scored_signals


def run_scorer_for_all(all_signals: dict) -> dict:
    """
    Run scorer for ALL competitors.
    Takes dict from Phase 3, returns dict for Phase 5.

    Args:
        all_signals: {competitor_id: [ClassifiedSignal, ...]}

    Returns:
        {competitor_id: [ScoredSignal, ...]}
    """
    all_scored = {}

    for competitor_id, signals in all_signals.items():
        scored = run_scorer_for_competitor(competitor_id, signals)
        all_scored[competitor_id] = scored

    total = sum(len(v) for v in all_scored.values())
    print(f"\n🏁 Scorer complete — {total} total scored signals across all competitors")
    return all_scored


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────

def _priority_summary(scored_signals: list[ScoredSignal]) -> str:
    """One line summary of signal counts by priority."""
    high   = len([s for s in scored_signals if s.priority == "HIGH"])
    medium = len([s for s in scored_signals if s.priority == "MEDIUM"])
    low    = len([s for s in scored_signals if s.priority == "LOW"])
    return f"🔴 {high} HIGH | 🟡 {medium} MEDIUM | 🟢 {low} LOW"


# ─────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────

if __name__ == "__main__":
    import asyncio

    # Add all phase paths
    sys.path.append(os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "phase1_collector"
    ))
    sys.path.append(os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "phase2_detector"
    ))
    sys.path.append(os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "phase3_classifier"
    ))

    from collector_runner import run_collector_for_competitor
    from detector_runner import run_detector_for_competitor
    from classifier_runner import run_classifier_for_competitor

    init_db()

    print("🧪 Testing Phase 4 Scorer — full pipeline run\n")

    # Get first competitor
    competitors = get_all_competitors()
    if not competitors:
        print("❌ No competitors in database.")
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
    classified_signals = run_classifier_for_competitor(competitor["id"], detected_changes)
    print(f"✅ Phase 3 complete — {len(classified_signals)} signals classified")

    # Phase 4 — Score
    print("\n⏳ Running Phase 4 scorer...")
    scored_signals = run_scorer_for_competitor(competitor["id"], classified_signals)

    # Final summary
    print("\n" + "="*55)
    print("📊 PHASE 4 COMPLETE — SUMMARY")
    print("="*55)
    print(f"  Sources scraped    : {len(scraped_data)}")
    print(f"  Changes detected   : {len(detected_changes)}")
    print(f"  Signals classified : {len(classified_signals)}")
    print(f"  Signals scored     : {len(scored_signals)}")
    if scored_signals:
        print(f"\n  Scored signals:")
        for s in scored_signals:
            print(
                f"  {s.priority_emoji()} {s.signal_type:<30} "
                f"| {s.confidence:.1f}% [{s.confidence_label()}]"
            )
    else:
        print("  ✅ No signals this run — all sources stable")
    print("="*55)