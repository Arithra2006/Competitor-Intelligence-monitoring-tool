# backend/phase6_delivery/delivery_runner.py
# Master runner for Phase 6 — ties email and Slack delivery together
# Takes Phase 5 output (IntelligenceReport), delivers via all channels

import sys
import os
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import init_db, get_competitor_by_id, get_all_competitors
from models.report import IntelligenceReport
from email_sender import send_email_report
from slack_sender import send_slack_report


# ─────────────────────────────────────────
# MAIN RUNNER
# ─────────────────────────────────────────

def run_delivery_for_competitor(report: IntelligenceReport) -> dict:
    """
    Deliver intelligence report via all configured channels.
    Currently supports email and Slack.

    Args:
        report: IntelligenceReport object from Phase 5

    Returns:
        Dict with delivery results per channel
    """
    print(f"\n{'='*55}")
    print(f"📬 Starting delivery for: {report.competitor_name}")
    print(f"   Signals in report : {report.total_signals()}")
    print(f"   Started at        : {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"{'='*55}")

    results = {
        "competitor_name": report.competitor_name,
        "email": False,
        "slack": False,
        "delivered_at": datetime.now(timezone.utc).isoformat(),
    }

    # ── Email Delivery ─────────────────────────────────
    print("\n── Email Delivery ──")
    try:
        results["email"] = send_email_report(report)
    except Exception as e:
        print(f"❌ Email delivery failed: {e}")
        results["email"] = False

    # ── Slack Delivery ─────────────────────────────────
    print("\n── Slack Delivery ──")
    try:
        results["slack"] = send_slack_report(report)
    except Exception as e:
        print(f"❌ Slack delivery failed: {e}")
        results["slack"] = False

    # ── Summary ────────────────────────────────────────
    print(f"\n{'─'*55}")
    print(f"📬 Delivery complete for: {report.competitor_name}")
    print(f"   Email : {'✅ Sent' if results['email'] else '❌ Failed/Skipped'}")
    print(f"   Slack : {'✅ Sent' if results['slack'] else '⏭️  Skipped'}")
    print(f"{'─'*55}\n")

    return results


def run_delivery_for_all(all_reports: dict) -> list[dict]:
    """
    Deliver reports for ALL competitors.
    Takes dict from Phase 5, delivers via all channels.

    Args:
        all_reports: {competitor_id: IntelligenceReport}

    Returns:
        List of delivery result dicts
    """
    all_results = []

    for competitor_id, report in all_reports.items():
        result = run_delivery_for_competitor(report)
        all_results.append(result)

    # Summary
    email_sent = sum(1 for r in all_results if r["email"])
    slack_sent = sum(1 for r in all_results if r["slack"])
    print(f"\n🏁 Delivery complete — {email_sent} emails sent, {slack_sent} Slack messages sent")
    return all_results


# ─────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────

if __name__ == "__main__":
    import asyncio

    # Add all phase paths
    for phase in ["phase1_collector", "phase2_detector",
                  "phase3_classifier", "phase4_scorer", "phase5_reporter"]:
        sys.path.append(os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            phase
        ))

    from collector_runner import run_collector_for_competitor
    from detector_runner import run_detector_for_competitor
    from classifier_runner import run_classifier_for_competitor
    from scorer_runner import run_scorer_for_competitor
    from reporter_runner import run_reporter_for_competitor

    init_db()

    print("🧪 Testing Phase 6 Delivery — full pipeline run\n")

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
    print(f"✅ Phase 5 complete — report generated")

    # Phase 6 — Deliver
    print("\n⏳ Running Phase 6 delivery...")
    results = run_delivery_for_competitor(report)

    # Final summary
    print("\n" + "="*55)
    print("📊 PHASE 6 COMPLETE — SUMMARY")
    print("="*55)
    print(f"  Competitor : {results['competitor_name']}")
    print(f"  Email      : {'✅ Sent' if results['email'] else '❌ Failed/Skipped'}")
    print(f"  Slack      : {'✅ Sent' if results['slack'] else '⏭️  Skipped'}")
    print(f"  Delivered  : {results['delivered_at']}")
    print("="*55)