# backend/phase3_classifier/snapshot_store.py
# Saves classified snapshots and signals to SQLite
# Called after every successful classification
# Enables before/after comparisons in dashboard

import json
import sys
import os
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import insert_snapshot, insert_signal, get_latest_snapshot
from models.signal import ClassifiedSignal


# ─────────────────────────────────────────
# MAIN FUNCTIONS
# ─────────────────────────────────────────

def save_classified_snapshot(signal: ClassifiedSignal) -> dict:
    """
    Save a classified signal to SQLite.
    Stores both the snapshot and the signal record.
    This enables before/after comparisons in the dashboard.

    Args:
        signal: ClassifiedSignal object from Phase 3 classifier

    Returns:
        Dict with snapshot_id and signal_id
    """
    print(f"💾 Saving classified snapshot — {signal.source}: {signal.change_type}")

    # Build structured evidence for signal
    evidence = _build_evidence(signal)

    # Save snapshot with classification metadata
    snapshot_id = insert_snapshot(
        competitor_id=signal.competitor_id,
        source=signal.source,
        url=signal.url,
        raw_text=signal.new_text,
        change_type=signal.change_type,
        confidence=signal.metadata.get("confidence", 0),
    )

    # Save signal with full evidence
    signal_id = insert_signal(
        competitor_id=signal.competitor_id,
        signal_type=signal.change_type,
        confidence=signal.metadata.get("confidence", 0),
        evidence=evidence,
    )

    print(f"   ✅ Snapshot saved — ID: {snapshot_id}")
    print(f"   ✅ Signal saved   — ID: {signal_id}")

    return {
        "snapshot_id": snapshot_id,
        "signal_id": signal_id,
    }


def save_classified_snapshots_batch(signals: list[ClassifiedSignal]) -> list[dict]:
    """
    Save multiple classified signals to SQLite.

    Args:
        signals: List of ClassifiedSignal objects

    Returns:
        List of dicts with snapshot_id and signal_id
    """
    if not signals:
        print("⚠️  No signals to save")
        return []

    print(f"\n💾 Saving {len(signals)} classified signal(s)...")
    results = []

    for signal in signals:
        try:
            result = save_classified_snapshot(signal)
            results.append(result)
        except Exception as e:
            print(f"❌ Failed to save signal for {signal.source}: {e}")
            continue

    print(f"✅ Saved {len(results)}/{len(signals)} signals to database")
    return results


def get_before_after_comparison(competitor_id: int, source: str) -> dict | None:
    """
    Get before/after text comparison for dashboard display.
    Retrieves the two most recent snapshots for a source.

    Args:
        competitor_id: ID of the competitor
        source: Data source ('website', 'careers', etc.)

    Returns:
        Dict with before/after text and metadata, or None
    """
    from database import get_snapshots_by_competitor

    snapshots = get_snapshots_by_competitor(competitor_id)

    # Filter by source
    source_snapshots = [
        s for s in snapshots
        if s["source"] == source
    ]

    if len(source_snapshots) < 2:
        return None

    # Most recent = after, second most recent = before
    after  = source_snapshots[0]
    before = source_snapshots[1]

    return {
        "source": source,
        "before": {
            "text": before["raw_text"][:1000],
            "crawled_at": before["crawled_at"],
            "change_type": before.get("change_type"),
        },
        "after": {
            "text": after["raw_text"][:1000],
            "crawled_at": after["crawled_at"],
            "change_type": after.get("change_type"),
        },
        "change_type": after.get("change_type", "Unknown"),
        "confidence": after.get("confidence", 0),
    }


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────

def _build_evidence(signal: ClassifiedSignal) -> list:
    """
    Build structured evidence list from classified signal.
    This is what the scorer and reporter use.
    """
    from phase4_scorer.reliability_weights import SOURCE_RELIABILITY

    reliability = SOURCE_RELIABILITY.get(signal.source, 0.5)

    evidence = [
        {
            "source": signal.source,
            "reliability": reliability,
            "change_type": signal.change_type,
            "detail": signal.metadata.get("key_evidence", "")[:300],
            "reasoning": signal.metadata.get("reasoning", ""),
            "url": signal.url,
            "similarity_score": signal.similarity_score,
            "confidence": signal.metadata.get("confidence", 0),
        }
    ]

    return evidence


# ─────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────

if __name__ == "__main__":
    from database import init_db
    from models.signal import ClassifiedSignal

    init_db()

    print("🧪 Testing snapshot store...\n")

    # Create a test signal
    test_signal = ClassifiedSignal(
        competitor_id=1,
        source="website",
        url="https://notion.so",
        change_type="AI positioning added",
        old_text="Our platform provides analytics and reporting tools.",
        new_text="Our AI-powered platform provides predictive analytics and ML forecasting.",
        similarity_score=0.62,
        raw_classification='{"change_type": "AI positioning added", "confidence": 95}',
        metadata={
            "confidence": 95,
            "reasoning": "AI and ML language added to homepage",
            "key_evidence": "AI-powered platform, ML forecasting",
            "change_magnitude": "MODERATE",
        }
    )

    # Save it
    print("Saving classified signal...")
    result = save_classified_snapshot(test_signal)
    print(f"\nResult: {result}")

    # Test before/after comparison
    print("\nTesting before/after comparison...")
    comparison = get_before_after_comparison(1, "website")
    if comparison:
        print(f"✅ Before/after comparison available")
        print(f"   Change type : {comparison['change_type']}")
        print(f"   Confidence  : {comparison['confidence']}%")
        print(f"   Before      : {comparison['before']['text'][:100]}...")
        print(f"   After       : {comparison['after']['text'][:100]}...")
    else:
        print("⚠️  Not enough snapshots for comparison yet — need 2+ crawls")

    print("\n✅ Snapshot store test complete!")