# backend/run_pipeline.py
import asyncio
import sys
import os

# Add backend and all phase folders to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

for phase in ["phase1_collector", "phase2_detector",
              "phase3_classifier", "phase4_scorer",
              "phase5_reporter", "phase6_delivery"]:
    sys.path.insert(0, os.path.join(backend_dir, phase))

from database import init_db, get_all_competitors
from phase1_collector.collector_runner import run_collector_for_competitor
from phase2_detector.detector_runner import run_detector_for_competitor
from phase3_classifier.classifier_runner import run_classifier_for_competitor
from phase4_scorer.scorer_runner import run_scorer_for_competitor
from phase5_reporter.reporter_runner import run_reporter_for_competitor
from phase6_delivery.delivery_runner import run_delivery_for_competitor


async def main():
    init_db()
    competitors = get_all_competitors()

    if not competitors:
        print("No competitors found in database")
        return

    competitor = competitors[-1]
    print(f"Running pipeline for: {competitor['name']}")

    scraped    = await run_collector_for_competitor(competitor)
    detected   = run_detector_for_competitor(competitor["id"], scraped)
    classified = run_classifier_for_competitor(competitor["id"], detected)
    scored     = run_scorer_for_competitor(competitor["id"], classified)
    report     = run_reporter_for_competitor(competitor["id"], scored)
    run_delivery_for_competitor(report)

    print("✅ Pipeline complete!")


asyncio.run(main())