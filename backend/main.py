# backend/main.py
# FastAPI entry point — serves all API endpoints for the dashboard
# Run with: uvicorn main:app --reload --port 8000

import sys
import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio

# Add backend to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from database import (
    init_db,
    get_all_competitors,
    get_competitor_by_id,
    insert_competitor,
    delete_competitor,
    get_snapshots_by_competitor,
    get_signals_by_competitor,
    get_reports_by_competitor,
    update_signal_feedback,
)


# ─────────────────────────────────────────
# APP SETUP
# ─────────────────────────────────────────

app = FastAPI(
    title="Competitor Intelligence API",
    description="Autonomous competitor monitoring pipeline",
    version="1.0.0",
)

# Allow Next.js frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────
# PYDANTIC MODELS
# ─────────────────────────────────────────

class CompetitorCreate(BaseModel):
    name: str
    website_url: str
    careers_url: Optional[str] = None
    github_org: Optional[str] = None
    reddit_keyword: Optional[str] = None
    frequency: str = "weekly"


class FeedbackUpdate(BaseModel):
    feedback: str  # "useful" or "irrelevant"


# ─────────────────────────────────────────
# STARTUP
# ─────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    # Add all phase paths on startup
    for phase in ["phase1_collector", "phase2_detector",
                  "phase3_classifier", "phase4_scorer",
                  "phase5_reporter", "phase6_delivery"]:
        phase_path = os.path.join(backend_dir, phase)
        if phase_path not in sys.path:
            sys.path.insert(0, phase_path)

    init_db()
    print("✅ Competitor Intelligence API started")
    print("   Docs available at: http://localhost:8000/docs")


# ─────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "running",
        "service": "Competitor Intelligence API",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    competitors = get_all_competitors()
    return {
        "status": "healthy",
        "competitors_tracked": len(competitors),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ─────────────────────────────────────────
# COMPETITORS ENDPOINTS
# ─────────────────────────────────────────

@app.get("/api/competitors")
async def get_competitors():
    """Get all tracked competitors."""
    competitors = get_all_competitors()
    return {"competitors": competitors, "count": len(competitors)}


@app.get("/api/competitors/{competitor_id}")
async def get_competitor(competitor_id: int):
    """Get a single competitor by ID."""
    competitor = get_competitor_by_id(competitor_id)
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return competitor


@app.post("/api/competitors")
async def create_competitor(data: CompetitorCreate):
    """Add a new competitor to track."""
    try:
        comp_id = insert_competitor(
            name=data.name,
            website_url=data.website_url,
            careers_url=data.careers_url,
            github_org=data.github_org,
            reddit_keyword=data.reddit_keyword,
            frequency=data.frequency,
        )
        competitor = get_competitor_by_id(comp_id)
        return {"message": "Competitor added successfully", "competitor": competitor}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/competitors/{competitor_id}")
async def remove_competitor(competitor_id: int):
    """Remove a competitor from tracking."""
    competitor = get_competitor_by_id(competitor_id)
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    delete_competitor(competitor_id)
    return {"message": f"Competitor '{competitor['name']}' removed successfully"}


# ─────────────────────────────────────────
# PIPELINE TRIGGER
# ─────────────────────────────────────────

@app.post("/api/run/{competitor_id}")
async def run_pipeline(competitor_id: int, background_tasks: BackgroundTasks):
    """
    Trigger full pipeline for a competitor.
    Runs in background so API doesn't timeout.
    """
    competitor = get_competitor_by_id(competitor_id)
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")

    background_tasks.add_task(_run_full_pipeline, competitor)

    return {
        "message": f"Pipeline started for {competitor['name']}",
        "competitor_id": competitor_id,
        "status": "running",
    }


@app.post("/api/run/all")
async def run_pipeline_all(background_tasks: BackgroundTasks):
    """Trigger full pipeline for ALL competitors."""
    competitors = get_all_competitors()
    if not competitors:
        raise HTTPException(status_code=404, detail="No competitors found")

    for competitor in competitors:
        background_tasks.add_task(_run_full_pipeline, competitor)

    return {
        "message": f"Pipeline started for {len(competitors)} competitor(s)",
        "status": "running",
    }


async def _run_full_pipeline(competitor: dict):
    """Run full pipeline for one competitor in background."""
    try:
        for phase in ["phase1_collector", "phase2_detector",
                      "phase3_classifier", "phase4_scorer",
                      "phase5_reporter", "phase6_delivery"]:
            phase_path = os.path.join(backend_dir, phase)
            if phase_path not in sys.path:
                sys.path.insert(0, phase_path)

        from phase1_collector.collector_runner import run_collector_for_competitor
        from phase2_detector.detector_runner import run_detector_for_competitor
        from phase3_classifier.classifier_runner import run_classifier_for_competitor
        from phase4_scorer.scorer_runner import run_scorer_for_competitor
        from phase5_reporter.reporter_runner import run_reporter_for_competitor
        from phase6_delivery.delivery_runner import run_delivery_for_competitor

        print(f"\n🚀 Pipeline starting for: {competitor['name']}")

        # Run collector in separate thread to avoid Playwright asyncio conflict
        import concurrent.futures
        import functools

        def run_sync_pipeline():
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                scraped = loop.run_until_complete(
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

        with concurrent.futures.ThreadPoolExecutor() as pool:
            await asyncio.get_event_loop().run_in_executor(pool, run_sync_pipeline)

    except Exception as e:
        import traceback
        print(f"❌ Pipeline failed for {competitor['name']}: {e}")
        print(traceback.format_exc())
# ─────────────────────────────────────────
# SIGNALS ENDPOINTS
# ─────────────────────────────────────────

@app.get("/api/signals/{competitor_id}")
async def get_signals(competitor_id: int):
    """Get all signals for a competitor."""
    competitor = get_competitor_by_id(competitor_id)
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    signals = get_signals_by_competitor(competitor_id)
    return {
        "competitor": competitor["name"],
        "signals": signals,
        "count": len(signals),
    }


@app.patch("/api/signals/{signal_id}/feedback")
async def update_feedback(signal_id: int, data: FeedbackUpdate):
    """
    Update feedback for a signal — useful or irrelevant.
    Automatically triggers weight adjustment after saving.
    """
    if data.feedback not in ["useful", "irrelevant"]:
        raise HTTPException(
            status_code=400,
            detail="Feedback must be 'useful' or 'irrelevant'"
        )

    # Save feedback
    update_signal_feedback(signal_id, data.feedback)

    # Auto-adjust weights based on new feedback
    try:
        from phase4_scorer.weight_adjuster import adjust_weights_from_feedback
        adjustments = adjust_weights_from_feedback()
        print(f"🔧 Weights adjusted after feedback: {len(adjustments)} source(s) updated")
    except Exception as e:
        print(f"⚠️  Weight adjustment failed: {e}")
        adjustments = {}

    return {
        "message": "Feedback saved and weights adjusted",
        "signal_id": signal_id,
        "feedback": data.feedback,
        "weight_adjustments": adjustments,
    }


@app.get("/api/weights")
async def get_weights():
    """
    Get current source reliability weights.
    Shows default vs adjusted weights.
    """
    try:
        from phase4_scorer.weight_adjuster import get_current_weights
        from phase4_scorer.reliability_weights import SOURCE_RELIABILITY

        current = get_current_weights()

        weights_info = []
        for source, weight in current.items():
            default = SOURCE_RELIABILITY.get(source, 0.5)
            weights_info.append({
                "source": source,
                "current_weight": weight,
                "default_weight": default,
                "adjusted": weight != default,
                "change": round(weight - default, 2),
            })

        return {
            "weights": weights_info,
            "message": "Weights adjust automatically based on your feedback"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/weights/reset")
async def reset_weights():
    """Reset all weights back to defaults."""
    try:
        from phase4_scorer.weight_adjuster import reset_weights
        reset_weights()
        return {"message": "All weights reset to defaults"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────
# REPORTS ENDPOINTS
# ─────────────────────────────────────────

@app.get("/api/reports/{competitor_id}")
async def get_reports(competitor_id: int):
    """Get all reports for a competitor."""
    competitor = get_competitor_by_id(competitor_id)
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    reports = get_reports_by_competitor(competitor_id)
    return {
        "competitor": competitor["name"],
        "reports": reports,
        "count": len(reports),
    }


# ─────────────────────────────────────────
# SNAPSHOTS ENDPOINTS
# ─────────────────────────────────────────

@app.get("/api/snapshots/{competitor_id}")
async def get_snapshots(competitor_id: int):
    """Get all snapshots for a competitor."""
    competitor = get_competitor_by_id(competitor_id)
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    snapshots = get_snapshots_by_competitor(competitor_id)
    return {
        "competitor": competitor["name"],
        "snapshots": snapshots[:20],
        "count": len(snapshots),
    }


# ─────────────────────────────────────────
# DASHBOARD SUMMARY ENDPOINT
# ─────────────────────────────────────────

@app.get("/api/dashboard")
async def get_dashboard_summary():
    """
    Get full dashboard summary.
    Returns competitors, recent signals, and report counts.
    """
    competitors = get_all_competitors()
    summary = []

    for comp in competitors:
        signals   = get_signals_by_competitor(comp["id"])
        reports   = get_reports_by_competitor(comp["id"])
        snapshots = get_snapshots_by_competitor(comp["id"])

        high   = len([s for s in signals if _get_priority(s) == "HIGH"])
        medium = len([s for s in signals if _get_priority(s) == "MEDIUM"])
        low    = len([s for s in signals if _get_priority(s) == "LOW"])

        summary.append({
            "competitor": comp,
            "total_signals": len(signals),
            "high_priority": high,
            "medium_priority": medium,
            "low_priority": low,
            "total_reports": len(reports),
            "total_snapshots": len(snapshots),
            "latest_report": reports[0] if reports else None,
            "recent_signals": signals[:5],
        })

    return {
        "summary": summary,
        "total_competitors": len(competitors),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def _get_priority(signal: dict) -> str:
    """Get priority from signal type."""
    from models.signal import CHANGE_PRIORITY
    signal_type = signal.get("signal_type", "Unknown change")
    return CHANGE_PRIORITY.get(signal_type, "LOW")

# ─────────────────────────────────────────
# BATTLECARD ENDPOINTS
# ─────────────────────────────────────────

@app.post("/api/battlecards/{competitor_id}")
async def generate_battlecard_endpoint(competitor_id: int):
    """Generate a battlecard for a competitor."""
    competitor = get_competitor_by_id(competitor_id)
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")

    try:
        from phase5_reporter.battlecard_generator import generate_battlecard
        battlecard = generate_battlecard(competitor_id)

        if not battlecard:
            raise HTTPException(status_code=500, detail="Battlecard generation failed")

        return {
            "message": f"Battlecard generated for {competitor['name']}",
            "battlecard": battlecard.to_dict(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/battlecards/{competitor_id}")
async def get_battlecard_endpoint(competitor_id: int):
    """Get saved battlecard for a competitor."""
    competitor = get_competitor_by_id(competitor_id)
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")

    try:
        from phase5_reporter.battlecard_generator import get_battlecard
        battlecard = get_battlecard(competitor_id)

        if not battlecard:
            return {
                "message": "No battlecard yet — generate one first",
                "battlecard": None,
            }

        return {
            "message": "Battlecard retrieved",
            "battlecard": battlecard.to_dict(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/battlecards")
async def get_all_battlecards():
    """Get all saved battlecards."""
    try:
        from phase5_reporter.battlecard_generator import get_battlecard
        competitors = get_all_competitors()
        battlecards = []

        for comp in competitors:
            bc = get_battlecard(comp["id"])
            if bc:
                battlecards.append(bc.to_dict())

        return {
            "battlecards": battlecards,
            "count": len(battlecards),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─────────────────────────────────────────
# TIMELINE ENDPOINT
# ─────────────────────────────────────────

@app.get("/api/timeline/{competitor_id}")
async def get_timeline(competitor_id: int):
    """
    Get full change history timeline for a competitor.
    Combines signals and snapshots into chronological timeline.
    """
    competitor = get_competitor_by_id(competitor_id)
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")

    signals   = get_signals_by_competitor(competitor_id)
    snapshots = get_snapshots_by_competitor(competitor_id)

    # Build timeline events from signals
    events = []

    for signal in signals:
        evidence = signal.get("evidence", [])
        sources  = [e.get("source", "") for e in evidence]
        priority = _get_priority(signal)

        events.append({
            "type"       : "signal",
            "date"       : signal.get("detected_at", "")[:10],
            "datetime"   : signal.get("detected_at", ""),
            "title"      : signal.get("signal_type", "Unknown"),
            "confidence" : signal.get("confidence", 0),
            "priority"   : priority,
            "sources"    : sources,
            "evidence"   : evidence,
            "signal_id"  : signal.get("id"),
            "feedback"   : signal.get("feedback"),
        })

    # Group snapshots by date — show crawl activity
    crawl_dates = {}
    for snap in snapshots:
        date = snap.get("crawled_at", "")[:10]
        if date not in crawl_dates:
            crawl_dates[date] = []
        crawl_dates[date].append(snap.get("source", ""))

    for date, sources in crawl_dates.items():
        # Only add crawl event if no signal on same date
        signal_dates = [e["date"] for e in events]
        if date not in signal_dates:
            events.append({
                "type"      : "crawl",
                "date"      : date,
                "datetime"  : date + "T00:00:00",
                "title"     : "Pipeline run — no changes detected",
                "confidence": 0,
                "priority"  : "NONE",
                "sources"   : list(set(sources)),
                "evidence"  : [],
                "signal_id" : None,
                "feedback"  : None,
            })

    # Sort by date descending
    events.sort(key=lambda x: x["datetime"], reverse=True)

    return {
        "competitor"   : competitor["name"],
        "total_events" : len(events),
        "events"       : events,
    }
# ─────────────────────────────────────────
# RUN
# ─────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)