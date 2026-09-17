# backend/phase4_scorer/evidence_aggregator.py
# Aggregates evidence across all sources for a competitor
# Groups signals by change type, corroborates across sources
# Output feeds into confidence scorer

import sys
import os
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reliability_weights import SOURCE_RELIABILITY, CHANGE_TYPE_STRENGTH
try:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from weight_adjuster import get_current_weights
    SOURCE_RELIABILITY = get_current_weights()
except Exception:
    pass  # Fall back to defaults
from models.signal import ClassifiedSignal


# ─────────────────────────────────────────
# MAIN AGGREGATOR FUNCTION
# ─────────────────────────────────────────

def aggregate_evidence(signals: list[ClassifiedSignal]) -> list[dict]:
    """
    Aggregate classified signals into grouped evidence bundles.
    Groups signals by change type and corroborates across sources.
    
    This is what makes the confidence scoring rigorous —
    same change detected on website + careers + github = higher confidence
    than single source alone.

    Args:
        signals: List of ClassifiedSignal objects from Phase 3

    Returns:
        List of evidence bundle dicts — one per unique change type
    """
    if not signals:
        return []

    print(f"📊 Aggregating evidence from {len(signals)} signal(s)...")

    # Group signals by change type
    grouped = _group_by_change_type(signals)

    # Build evidence bundle for each change type
    evidence_bundles = []
    for change_type, type_signals in grouped.items():
        bundle = _build_evidence_bundle(change_type, type_signals)
        evidence_bundles.append(bundle)
        print(f"   ✅ {change_type} — {len(type_signals)} source(s) corroborating")

    # Sort by confidence descending
    evidence_bundles.sort(key=lambda x: x["raw_confidence"], reverse=True)

    return evidence_bundles


# ─────────────────────────────────────────
# INTERNAL HELPERS
# ─────────────────────────────────────────

def _group_by_change_type(signals: list[ClassifiedSignal]) -> dict:
    """
    Group signals by their change type.
    Multiple sources detecting same change = corroboration.
    """
    grouped = {}
    for signal in signals:
        change_type = signal.change_type
        if change_type not in grouped:
            grouped[change_type] = []
        grouped[change_type].append(signal)
    return grouped


def _build_evidence_bundle(
    change_type: str,
    signals: list[ClassifiedSignal],
) -> dict:
    """
    Build a structured evidence bundle for one change type.
    Contains all sources that detected this change type.

    Args:
        change_type: The type of change detected
        signals: All signals of this change type

    Returns:
        Structured evidence bundle dict
    """
    # Build individual evidence items
    evidence_items = []
    for signal in signals:
        reliability = SOURCE_RELIABILITY.get(signal.source, 0.5)
        evidence_items.append({
            "source": signal.source,
            "reliability": reliability,
            "detail": signal.metadata.get("key_evidence", "")[:300],
            "reasoning": signal.metadata.get("reasoning", ""),
            "url": signal.url,
            "similarity_score": signal.similarity_score,
            "groq_confidence": signal.metadata.get("confidence", 50),
            "change_magnitude": signal.metadata.get("change_magnitude", "MINOR"),
            "source_excerpt": signal.metadata.get("source_excerpt"),
        })

    # Calculate source agreement score
    source_agreement = _calculate_source_agreement(signals)

    # Calculate average source reliability
    avg_reliability = _calculate_avg_reliability(signals)

    # Calculate signal strength
    signal_strength = _calculate_signal_strength(change_type, signals)

    # Raw confidence before final formula (used for sorting)
    raw_confidence = (
        0.4 * source_agreement +
        0.4 * avg_reliability +
        0.2 * signal_strength
    ) * 100

    # Get priority from first signal
    priority = signals[0].priority() if signals else "LOW"

    return {
        "change_type": change_type,
        "signal": change_type,
        "sources_count": len(signals),
        "sources": [s.source for s in signals],
        "evidence": evidence_items,
        "source_agreement": round(source_agreement, 3),
        "avg_reliability": round(avg_reliability, 3),
        "signal_strength": round(signal_strength, 3),
        "raw_confidence": round(raw_confidence, 1),
        "priority": priority,
        "detected_at": datetime.now(timezone.utc).isoformat(),
    }


def _calculate_source_agreement(signals: list[ClassifiedSignal]) -> float:
    """
    Calculate how much sources agree on this change type.
    More sources = higher agreement score.

    Scale:
    1 source  = 0.4 (some evidence)
    2 sources = 0.7 (good corroboration)
    3 sources = 0.9 (strong corroboration)
    4+ sources = 1.0 (maximum agreement)
    """
    count = len(signals)
    if count == 1:
        return 0.4
    elif count == 2:
        return 0.7
    elif count == 3:
        return 0.9
    else:
        return 1.0


def _calculate_avg_reliability(signals: list[ClassifiedSignal]) -> float:
    """
    Calculate weighted average reliability across all sources.
    Uses SOURCE_RELIABILITY weights.
    Higher reliability sources count more.
    """
    if not signals:
        return 0.0

    total_reliability = sum(
        SOURCE_RELIABILITY.get(s.source, 0.5)
        for s in signals
    )
    return total_reliability / len(signals)


def _calculate_signal_strength(
    change_type: str,
    signals: list[ClassifiedSignal],
) -> float:
    """
    Calculate signal strength based on:
    - Change type importance (from CHANGE_TYPE_STRENGTH)
    - Average Groq confidence across signals
    - Average similarity score (lower = bigger change)

    Returns a float between 0.0 and 1.0
    """
    # Base strength from change type
    type_strength = CHANGE_TYPE_STRENGTH.get(change_type, 0.5)

    # Average Groq confidence (normalized to 0-1)
    avg_groq_confidence = sum(
        s.metadata.get("confidence", 50) for s in signals
    ) / len(signals) / 100.0

    # Average change magnitude from similarity scores
    # Lower similarity = bigger change = higher strength
    avg_similarity = sum(s.similarity_score for s in signals) / len(signals)
    magnitude_strength = 1.0 - avg_similarity  # Invert: lower sim = higher strength

    # Combine: 50% type, 30% groq confidence, 20% magnitude
    strength = (
        0.5 * type_strength +
        0.3 * avg_groq_confidence +
        0.2 * magnitude_strength
    )

    return min(1.0, max(0.0, strength))


# ─────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────

if __name__ == "__main__":
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from database import init_db
    from models.signal import ClassifiedSignal

    init_db()

    print("🧪 Testing evidence aggregator...\n")

    # Create test signals — simulating multiple sources
    # detecting same change type
    signal1 = ClassifiedSignal(
        competitor_id=1,
        source="website",
        url="https://notion.so",
        change_type="AI positioning added",
        old_text="Our analytics platform for teams.",
        new_text="Our AI-powered analytics platform for teams.",
        similarity_score=0.62,
        raw_classification="{}",
        metadata={
            "confidence": 95,
            "reasoning": "AI language added to homepage",
            "key_evidence": "AI-powered added to main headline",
            "change_magnitude": "MODERATE",
        }
    )

    signal2 = ClassifiedSignal(
        competitor_id=1,
        source="careers",
        url="https://notion.so/careers",
        change_type="AI positioning added",
        old_text="Software engineer roles available.",
        new_text="AI Engineer, ML Engineer, LLM Engineer roles available.",
        similarity_score=0.55,
        raw_classification="{}",
        metadata={
            "confidence": 88,
            "reasoning": "Multiple AI engineering roles posted",
            "key_evidence": "AI Engineer, ML Engineer, LLM Engineer",
            "change_magnitude": "MODERATE",
        }
    )

    signal3 = ClassifiedSignal(
        competitor_id=1,
        source="github",
        url="https://github.com/notionhq",
        change_type="AI positioning added",
        old_text="Recent commits: bug fixes and UI updates.",
        new_text="Recent commits: LLM integration, embedding pipeline, AI features.",
        similarity_score=0.48,
        raw_classification="{}",
        metadata={
            "confidence": 82,
            "reasoning": "AI-related commits in core repo",
            "key_evidence": "LLM integration, embedding pipeline",
            "change_magnitude": "MAJOR",
        }
    )

    # Test aggregation
    signals = [signal1, signal2, signal3]
    bundles = aggregate_evidence(signals)

    print("\n--- RESULTS ---")
    for bundle in bundles:
        print(f"\nChange Type     : {bundle['change_type']}")
        print(f"Sources         : {bundle['sources']}")
        print(f"Source Agreement: {bundle['source_agreement']}")
        print(f"Avg Reliability : {bundle['avg_reliability']}")
        print(f"Signal Strength : {bundle['signal_strength']}")
        print(f"Raw Confidence  : {bundle['raw_confidence']}%")
        print(f"Priority        : {bundle['priority']}")
        print(f"Evidence items  : {len(bundle['evidence'])}")

    print("\n✅ Evidence aggregator test complete!")