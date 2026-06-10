# backend/phase5_reporter/reporter_runner.py
# Master runner for Phase 5 — ties briefing generator, why it matters, and formatter
# Takes Phase 4 output (ScoredSignal list), returns IntelligenceReport
# Also saves report to SQLite database

import sys
import os
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import init_db, get_competitor_by_id, get_all_competitors, insert_report
from models.signal import ScoredSignal
from models.report import IntelligenceReport
from briefing_generator import generate_briefing
from report_formatter import format_report, format_slack_message, format_email_html


# ─────────────────────────────────────────
# MAIN RUNNER
# ─────────────────────────────────────────

def run_reporter_for_competitor(
    competitor_id: int,
    scored_signals: list[ScoredSignal],
) -> IntelligenceReport | None:
    """
    Run Phase 5 reporter for a single competitor.
    Takes ScoredSignal list from Phase 4.
    Returns IntelligenceReport for Phase 6 delivery.

    Args:
        competitor_id: ID of the competitor
        scored_signals: List of ScoredSignal objects from Phase 4

    Returns:
        IntelligenceReport object or None on failure
    """
    competitor = get_competitor_by_id(competitor_id)
    name = competitor["name"] if competitor else f"ID:{competitor_id}"

    print(f"\n{'='*55}")
    print(f"📰 Starting reporter for: {name}")
    print(f"   Signals to report : {len(scored_signals)}")
    print(f"   Started at        : {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"{'='*55}")

    # Step 1 — Generate base briefing
    print("\n⏳ Generating briefing...")
    report = generate_briefing(
        competitor_name=name,
        scored_signals=scored_signals,
        competitor_id=competitor_id,
    )

    # Step 2 — Format full report with why it matters
    print("\n⏳ Formatting report...")
    report = format_report(
        report=report,
        scored_signals=scored_signals,
        competitor_name=name,
    )

    # Step 3 — Save to SQLite
    print("\n⏳ Saving report to database...")
    report_id = insert_report(
        competitor_id=competitor_id,
        report_text=report.report_text,
    )
    report.metadata["report_id"] = report_id
    print(f"✅ Report saved — ID: {report_id}")

    # Summary
    print(f"\n{'─'*55}")
    print(f"📰 Reporter complete for: {name}")
    print(f"   Total signals     : {report.total_signals()}")
    print(f"   Priority summary  : {report.priority_summary()}")
    print(f"   Report length     : {len(report.report_text)} characters")
    print(f"{'─'*55}\n")

    return report


def run_reporter_for_all(all_scored: dict) -> dict:
    """
    Run reporter for ALL competitors.
    Takes dict from Phase 4, returns dict of reports.

    Args:
        all_scored: {competitor_id: [ScoredSignal, ...]}

    Returns:
        {competitor_id: IntelligenceReport}
    """
    all_reports = {}

    for competitor_id, scored_signals in all_scored.items():
        report = run_reporter_for_competitor(competitor_id, scored_signals)
        if report:
            all_reports[competitor_id] = report

    print(f"\n🏁 Reporter complete — {len(all_reports)} report(s) generated")
    return all_reports


# ─────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────

if __name__ == "__main__":
    import asyncio

    # Add all phase paths
    for phase in ["phase1_collector", "phase2_detector", "phase3_classifier", "phase4_scorer"]:
        sys.path.append(os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            phase
        ))

    from collector_runner import run_collector_for_competitor
    from detector_runner import run_detector_for_competitor
    from classifier_runner import run_classifier_for_competitor
    from scorer_runner import run_scorer_for_competitor

    init_db()

    print("🧪 Testing Phase 5 Reporter — full pipeline run\n")

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
    print(f"✅ Phase 4 complete — {len(scored_signals)} signals scored")

    # Phase 5 — Report
    print("\n⏳ Running Phase 5 reporter...")
    report = run_reporter_for_competitor(competitor["id"], scored_signals)

    # Final summary
    print("\n" + "="*55)
    print("📊 PHASE 5 COMPLETE — SUMMARY")
    print("="*55)
    print(f"  Sources scraped    : {len(scraped_data)}")
    print(f"  Changes detected   : {len(detected_changes)}")
    print(f"  Signals classified : {len(classified_signals)}")
    print(f"  Signals scored     : {len(scored_signals)}")
    if report:
        print(f"  Report generated   : ✅")
        print(f"  Total signals      : {report.total_signals()}")
        print(f"  Priority summary   : {report.priority_summary()}")
        print(f"\n{'─'*55}")
        print("FULL REPORT:")
        print("─"*55)
        print(report.report_text)
    else:
        print("  Report generated   : ❌ Failed")
    print("="*55)