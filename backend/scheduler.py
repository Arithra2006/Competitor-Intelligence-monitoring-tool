# backend/scheduler.py
# APScheduler — triggers full pipeline automatically
# Respects each competitor's frequency setting (daily/weekly/monthly)
# Run with: python scheduler.py --mode weekly

import sys
import os
import asyncio
from datetime import datetime, timezone

# Add backend and all phase folders to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

for phase in ["phase1_collector", "phase2_detector",
              "phase3_classifier", "phase4_scorer",
              "phase5_reporter", "phase6_delivery"]:
    sys.path.insert(0, os.path.join(backend_dir, phase))

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from database import init_db, get_all_competitors


# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────

SCHEDULE_DAY  = "mon"
SCHEDULE_HOUR = 8
SCHEDULE_MIN  = 0


# ─────────────────────────────────────────
# FREQUENCY FILTER
# ─────────────────────────────────────────

def _filter_by_frequency(competitors: list) -> list:
    """
    Filter competitors based on their frequency setting
    and today's day of week.

    - daily   → runs every day
    - weekly  → runs on Monday only
    - monthly → runs on 1st of month only
    """
    now = datetime.now(timezone.utc)
    day_of_week  = now.weekday()  # 0=Monday, 6=Sunday
    day_of_month = now.day

    eligible = []

    for comp in competitors:
        frequency = comp.get("frequency", "weekly")

        if frequency == "daily":
            eligible.append(comp)
            print(f"   ✅ {comp['name']} — daily, always runs")

        elif frequency == "weekly":
            if day_of_week == 0:  # Monday
                eligible.append(comp)
                print(f"   ✅ {comp['name']} — weekly, today is Monday")
            else:
                print(f"   ⏭️  {comp['name']} — weekly, not Monday yet")

        elif frequency == "monthly":
            if day_of_month == 1:  # First of month
                eligible.append(comp)
                print(f"   ✅ {comp['name']} — monthly, today is 1st")
            else:
                print(f"   ⏭️  {comp['name']} — monthly, not 1st yet")

        else:
            # Unknown frequency — default to weekly on Monday
            if day_of_week == 0:
                eligible.append(comp)
                print(f"   ✅ {comp['name']} — unknown frequency, defaulting to weekly")

    return eligible


# ─────────────────────────────────────────
# PIPELINE RUNNER
# ─────────────────────────────────────────

def run_pipeline_for_all_competitors():
    """
    Run full pipeline for ALL eligible competitors.
    Respects each competitor's frequency setting.
    Called automatically by scheduler every day at 8 AM UTC.
    """
    print(f"\n{'='*60}")
    print(f"⏰ SCHEDULED RUN TRIGGERED")
    print(f"   Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"{'='*60}")

    from phase1_collector.collector_runner import run_collector_for_competitor
    from phase2_detector.detector_runner import run_detector_for_competitor
    from phase3_classifier.classifier_runner import run_classifier_for_competitor
    from phase4_scorer.scorer_runner import run_scorer_for_competitor
    from phase5_reporter.reporter_runner import run_reporter_for_competitor
    from phase6_delivery.delivery_runner import run_delivery_for_competitor

    competitors = get_all_competitors()

    if not competitors:
        print("⚠️  No competitors in database — skipping run")
        return

    print(f"\n📋 Checking frequency for {len(competitors)} competitor(s):")

    # Filter by frequency
    competitors_to_run = _filter_by_frequency(competitors)

    if not competitors_to_run:
        print("\n⚠️  No competitors due for running today — skipping")
        return

    print(f"\n🚀 Running pipeline for {len(competitors_to_run)} competitor(s)")

    for competitor in competitors_to_run:
        try:
            print(f"\n{'─'*60}")
            print(f"🚀 Starting pipeline for: {competitor['name']} ({competitor['frequency']})")

            # Create new event loop for each competitor
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                scraped    = loop.run_until_complete(
                    run_collector_for_competitor(competitor)
                )
                detected   = run_detector_for_competitor(competitor["id"], scraped)
                classified = run_classifier_for_competitor(competitor["id"], detected)
                scored     = run_scorer_for_competitor(competitor["id"], classified)
                report     = run_reporter_for_competitor(competitor["id"], scored)
                run_delivery_for_competitor(report)

                print(f"✅ Pipeline complete for: {competitor['name']}")

            finally:
                loop.close()

        except Exception as e:
            import traceback
            print(f"❌ Pipeline failed for {competitor['name']}: {e}")
            print(traceback.format_exc())
            continue

    print(f"\n{'='*60}")
    print(f"🏁 Scheduled run complete")
    print(f"   Ran for   : {len(competitors_to_run)} competitor(s)")
    print(f"   Skipped   : {len(competitors) - len(competitors_to_run)} competitor(s)")
    print(f"   Time      : {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"{'='*60}\n")


# ─────────────────────────────────────────
# SCHEDULER SETUP
# ─────────────────────────────────────────

def start_scheduler(mode: str = "weekly"):
    """
    Start the APScheduler.

    Modes:
    - 'weekly'  → runs every Monday at 8 AM UTC (production)
    - 'daily'   → runs every day at 8 AM UTC
    - 'hourly'  → runs every hour (for testing)
    - 'test'    → runs once immediately then exits
    """
    init_db()

    if mode == "test":
        print("🧪 TEST MODE — running pipeline once immediately")
        run_pipeline_for_all_competitors()
        return

    scheduler = BlockingScheduler(timezone="UTC")

    if mode == "weekly":
        # Run every Monday at 8 AM
        # Frequency filter inside will handle daily/weekly/monthly
        trigger = CronTrigger(
            day_of_week=SCHEDULE_DAY,
            hour=SCHEDULE_HOUR,
            minute=SCHEDULE_MIN,
        )
        schedule_desc = f"Every {SCHEDULE_DAY.upper()} at {SCHEDULE_HOUR:02d}:{SCHEDULE_MIN:02d} UTC"

    elif mode == "daily":
        # Run every day at 8 AM
        # Best for production — frequency filter handles the rest
        trigger = CronTrigger(
            hour=SCHEDULE_HOUR,
            minute=SCHEDULE_MIN,
        )
        schedule_desc = f"Every day at {SCHEDULE_HOUR:02d}:{SCHEDULE_MIN:02d} UTC"

    elif mode == "hourly":
        trigger = IntervalTrigger(hours=1)
        schedule_desc = "Every hour"

    else:
        print(f"❌ Unknown mode: {mode}")
        return

    scheduler.add_job(
        func=run_pipeline_for_all_competitors,
        trigger=trigger,
        id="competitor_pipeline",
        name="Competitor Intelligence Pipeline",
        misfire_grace_time=3600,
        coalesce=True,
    )

    print(f"\n{'='*60}")
    print(f"⏰ COMPETITOR INTELLIGENCE SCHEDULER")
    print(f"{'='*60}")
    print(f"   Schedule  : {schedule_desc}")
    print(f"   Mode      : {mode}")
    print(f"   Frequency : Respects per-competitor settings")
    print(f"   Started   : {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"{'='*60}")
    print(f"\n✅ Scheduler running — press Ctrl+C to stop\n")

    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("\n⏹️  Scheduler stopped by user")
        scheduler.shutdown()


# ─────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Competitor Intelligence Scheduler")
    parser.add_argument(
        "--mode",
        choices=["weekly", "daily", "hourly", "test"],
        default="daily",
        help="Schedule mode (default: daily)"
    )
    args = parser.parse_args()

    start_scheduler(mode=args.mode)