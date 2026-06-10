# backend/phase4_scorer/confidence_scorer.py
# Applies weighted confidence formula to evidence bundles
# Produces final ScoredSignal objects for Phase 5 reporter
#
# Formula:
# confidence = 0.4 × source_agreement
#            + 0.4 × source_reliability
#            + 0.2 × signal_strength

import sys
import os
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reliability_weights import MIN_CONFIDENCE_THRESHOLD
from models.signal import ScoredSignal, CHANGE_PRIORITY


# ─────────────────────────────────────────
# MAIN SCORER FUNCTION
# ─────────────────────────────────────────

def calculate_confidence(evidence_bundles: list[dict]) -> list[ScoredSignal]:
    """
    Apply weighted confidence formula to evidence bundles.
    Filters out low confidence signals.
    Returns list of ScoredSignal objects for Phase 5.

    Formula:
    confidence = (0.4 × source_agreement
               +  0.4 × avg_reliability
               +  0.2 × signal_strength) × 100

    Args:
        evidence_bundles: List of evidence bundle dicts from aggregator

    Returns:
        List of ScoredSignal objects above confidence threshold
    """
    if not evidence_bundles:
        print("⚠️  No evidence bundles to score")
        return []

    print(f"\n📊 Scoring {len(evidence_bundles)} evidence bundle(s)...")

    scored_signals = []

    for bundle in evidence_bundles:
        scored = _score_bundle(bundle)
        if scored:
            scored_signals.append(scored)

    # Sort by confidence descending
    scored_signals.sort(key=lambda x: x.confidence, reverse=True)

    print(f"✅ Scoring complete — {len(scored_signals)} signals above threshold")
    return scored_signals


def _score_bundle(bundle: dict) -> ScoredSignal | None:
    """
    Score a single evidence bundle using weighted formula.
    Returns ScoredSignal if above threshold, None if below.

    Args:
        bundle: Evidence bundle dict from aggregator

    Returns:
        ScoredSignal object or None
    """
    change_type      = bundle.get("change_type", "Unknown change")
    source_agreement = bundle.get("source_agreement", 0.0)
    avg_reliability  = bundle.get("avg_reliability", 0.0)
    signal_strength  = bundle.get("signal_strength", 0.0)
    evidence         = bundle.get("evidence", [])
    priority         = bundle.get("priority", "LOW")

    # ── Apply weighted formula ──────────────────────────
    confidence = (
        0.4 * source_agreement +
        0.4 * avg_reliability  +
        0.2 * signal_strength
    ) * 100

    confidence = round(confidence, 1)

    # ── Log scoring breakdown ───────────────────────────
    print(f"\n   Signal: {change_type}")
    print(f"   ├── Source agreement  (×0.4): {source_agreement:.3f} → {0.4 * source_agreement * 100:.1f}pts")
    print(f"   ├── Avg reliability   (×0.4): {avg_reliability:.3f} → {0.4 * avg_reliability * 100:.1f}pts")
    print(f"   ├── Signal strength   (×0.2): {signal_strength:.3f} → {0.2 * signal_strength * 100:.1f}pts")
    print(f"   └── Final confidence        : {confidence}%")

    # ── Filter below threshold ──────────────────────────
    if confidence < MIN_CONFIDENCE_THRESHOLD:
        print(f"   ⏭️  Below threshold ({MIN_CONFIDENCE_THRESHOLD}%) — filtered out")
        return None

    print(f"   ✅ Above threshold — included in report")

    # ── Build ScoredSignal ──────────────────────────────
    return ScoredSignal(
        competitor_id=_extract_competitor_id(evidence),
        signal_type=change_type,
        confidence=confidence,
        evidence=evidence,
        change_type=change_type,
        priority=priority,
        detected_at=bundle.get("detected_at", datetime.now(timezone.utc).isoformat()),
        metadata={
            "source_agreement": source_agreement,
            "avg_reliability": avg_reliability,
            "signal_strength": signal_strength,
            "sources_count": bundle.get("sources_count", 0),
            "sources": bundle.get("sources", []),
            "formula_breakdown": {
                "agreement_contribution": round(0.4 * source_agreement * 100, 1),
                "reliability_contribution": round(0.4 * avg_reliability * 100, 1),
                "strength_contribution": round(0.2 * signal_strength * 100, 1),
            }
        }
    )


def _extract_competitor_id(evidence: list) -> int:
    """Extract competitor_id from evidence list."""
    # Not stored in evidence bundle directly —
    # will be passed explicitly in scorer_runner
    return 0


def format_confidence_report(scored_signals: list[ScoredSignal]) -> str:
    """
    Format scored signals into a readable confidence report.
    Used for debugging and logging.
    """
    if not scored_signals:
        return "No signals above confidence threshold."

    lines = ["\n📊 CONFIDENCE SCORES", "=" * 45]

    for signal in scored_signals:
        emoji = signal.priority_emoji()
        label = signal.confidence_label()
        lines.append(
            f"{emoji} {signal.signal_type:<30} "
            f"| {signal.confidence:>5.1f}% [{label}]"
            f"| {signal.priority}"
        )
        # Show formula breakdown
        breakdown = signal.metadata.get("formula_breakdown", {})
        if breakdown:
            lines.append(
                f"   Agreement: {breakdown.get('agreement_contribution', 0):.1f}pt "
                f"+ Reliability: {breakdown.get('reliability_contribution', 0):.1f}pt "
                f"+ Strength: {breakdown.get('strength_contribution', 0):.1f}pt"
            )

    lines.append("=" * 45)
    return "\n".join(lines)


# ─────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────

if __name__ == "__main__":
    from database import init_db

    init_db()

    print("🧪 Testing confidence scorer...\n")

    # Test evidence bundles — simulating aggregator output
    test_bundles = [
        {
            # High confidence — 3 sources agree
            "change_type": "AI positioning added",
            "sources_count": 3,
            "sources": ["website", "careers", "github"],
            "source_agreement": 0.9,
            "avg_reliability": 0.833,
            "signal_strength": 0.805,
            "priority": "HIGH",
            "evidence": [
                {
                    "source": "website",
                    "reliability": 0.9,
                    "detail": "AI-powered added to homepage",
                    "reasoning": "Direct AI language added",
                },
                {
                    "source": "careers",
                    "reliability": 0.8,
                    "detail": "6 AI engineer openings",
                    "reasoning": "Hiring for AI roles",
                },
                {
                    "source": "github",
                    "reliability": 0.8,
                    "detail": "LLM integration commits",
                    "reasoning": "Active AI development",
                },
            ],
            "detected_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            # Medium confidence — 2 sources
            "change_type": "New market targeted",
            "sources_count": 2,
            "sources": ["website", "news"],
            "source_agreement": 0.7,
            "avg_reliability": 0.8,
            "signal_strength": 0.65,
            "priority": "MEDIUM",
            "evidence": [
                {
                    "source": "website",
                    "reliability": 0.9,
                    "detail": "Healthcare vertical mentioned",
                    "reasoning": "New industry page added",
                },
                {
                    "source": "news",
                    "reliability": 0.7,
                    "detail": "Press release about healthcare",
                    "reasoning": "Confirmed in news",
                },
            ],
            "detected_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            # Low confidence — single Reddit source
            "change_type": "Pricing restructured",
            "sources_count": 1,
            "sources": ["reddit"],
            "source_agreement": 0.4,
            "avg_reliability": 0.5,
            "signal_strength": 0.5,
            "priority": "HIGH",
            "evidence": [
                {
                    "source": "reddit",
                    "reliability": 0.5,
                    "detail": "Users complaining about price increase",
                    "reasoning": "Community discussion only",
                },
            ],
            "detected_at": datetime.now(timezone.utc).isoformat(),
        },
    ]

    # Score them
    scored = calculate_confidence(test_bundles)

    # Print formatted report
    print(format_confidence_report(scored))

    print(f"\n--- DETAILED RESULTS ---")
    for s in scored:
        print(f"\nSignal    : {s.signal_type}")
        print(f"Confidence: {s.confidence}% [{s.confidence_label()}]")
        print(f"Priority  : {s.priority_emoji()} {s.priority}")
        print(f"Sources   : {s.metadata.get('sources', [])}")

    print("\n✅ Confidence scorer test complete!")