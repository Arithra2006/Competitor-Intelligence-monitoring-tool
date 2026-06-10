# backend/phase5_reporter/briefing_generator.py
# Generates analyst-style intelligence briefings using Groq
# Takes scored signals from Phase 4 and writes professional briefings
# This is the visible output of the entire pipeline

import sys
import os
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from phase3_classifier.groq_client import call_groq_reporter
from models.signal import ScoredSignal
from models.report import IntelligenceReport


# ─────────────────────────────────────────
# SYSTEM PROMPT
# ─────────────────────────────────────────

BRIEFING_SYSTEM_PROMPT = """
You are a senior competitive intelligence analyst writing weekly briefings 
for startup CEOs and product leaders.

Your writing style:
- Direct and concise — no fluff
- Evidence-based — every claim backed by data
- Forward-looking — what does this mean for the future
- Executive-level — busy leaders need the key point fast

You write in plain text with clear sections.
Never use markdown headers with # symbols.
Use CAPS for section labels.
Keep each insight to 2-3 sentences maximum.
""".strip()


# ─────────────────────────────────────────
# MAIN FUNCTION
# ─────────────────────────────────────────

def generate_briefing(
    competitor_name: str,
    scored_signals: list[ScoredSignal],
    competitor_id: int,
) -> IntelligenceReport:
    """
    Generate a full weekly intelligence briefing for one competitor.
    Uses Groq to write analyst-style insights for each signal.

    Args:
        competitor_name: Name of the competitor
        scored_signals: List of ScoredSignal objects from Phase 4
        competitor_id: ID of the competitor

    Returns:
        IntelligenceReport object with full briefing text
    """
    print(f"\n📝 Generating briefing for: {competitor_name}")
    print(f"   Signals to report: {len(scored_signals)}")

    # Separate signals by priority
    high   = [s for s in scored_signals if s.priority == "HIGH"]
    medium = [s for s in scored_signals if s.priority == "MEDIUM"]
    low    = [s for s in scored_signals if s.priority == "LOW"]

    # Generate briefing text for each signal
    high_briefings   = _generate_signal_briefings(high, competitor_name)
    medium_briefings = _generate_signal_briefings(medium, competitor_name)
    low_briefings    = _generate_signal_briefings(low, competitor_name)

    # Build full report text
    report_text = _build_report_text(
        competitor_name=competitor_name,
        high_briefings=high_briefings,
        medium_briefings=medium_briefings,
        low_briefings=low_briefings,
        high_signals=high,
        medium_signals=medium,
        low_signals=low,
    )

    # Build IntelligenceReport object
    report = IntelligenceReport(
        competitor_id=competitor_id,
        competitor_name=competitor_name,
        report_text=report_text,
        high_priority=high_briefings,
        medium_priority=medium_briefings,
        low_priority=low_briefings,
        metadata={
            "total_signals": len(scored_signals),
            "high_count": len(high),
            "medium_count": len(medium),
            "low_count": len(low),
        }
    )

    print(f"✅ Briefing generated for {competitor_name}")
    return report


# ─────────────────────────────────────────
# INTERNAL HELPERS
# ─────────────────────────────────────────

def _generate_signal_briefings(
    signals: list[ScoredSignal],
    competitor_name: str,
) -> list[dict]:
    """
    Generate analyst briefing for each signal.
    Returns list of briefing dicts with text and metadata.
    """
    briefings = []

    for signal in signals:
        print(f"   ✍️  Writing briefing for: {signal.signal_type}")

        # Generate main insight
        insight = _generate_insight(signal, competitor_name)

        briefings.append({
            "signal_type": signal.signal_type,
            "confidence": signal.confidence,
            "priority": signal.priority,
            "sources": signal.metadata.get("sources", []),
            "insight": insight,
            "evidence": signal.evidence,
            "metadata": signal.metadata,
        })

    return briefings


def _generate_insight(signal: ScoredSignal, competitor_name: str) -> str:
    """
    Use Groq to generate a 2-3 sentence analyst insight for one signal.
    """
    # Build evidence summary
    evidence_summary = _summarize_evidence(signal.evidence)

    prompt = f"""
Write a 2-3 sentence competitive intelligence insight about this signal.

Competitor: {competitor_name}
Signal: {signal.signal_type}
Confidence: {signal.confidence:.1f}%
Evidence: {evidence_summary}

Write from the perspective of a senior analyst briefing a CEO.
Be specific about what was detected and what it suggests.
Do not start with "I" or "We".
""".strip()

    response = call_groq_reporter(
        prompt=prompt,
        system_prompt=BRIEFING_SYSTEM_PROMPT,
    )

    if not response:
        return f"{competitor_name} shows signals of {signal.signal_type.lower()} based on {', '.join(signal.metadata.get('sources', ['multiple sources']))}."

    return response


def _summarize_evidence(evidence: list) -> str:
    """Build a concise evidence summary string."""
    if not evidence:
        return "No specific evidence available"

    parts = []
    for e in evidence[:3]:  # Max 3 evidence items
        source = e.get("source", "unknown")
        detail = e.get("detail", "")[:100]
        reliability = e.get("reliability", 0.5)
        parts.append(f"{source} (reliability {reliability}): {detail}")

    return " | ".join(parts)


def _build_report_text(
    competitor_name: str,
    high_briefings: list,
    medium_briefings: list,
    low_briefings: list,
    high_signals: list,
    medium_signals: list,
    low_signals: list,
) -> str:
    """
    Assemble the full weekly report text.
    """
    now = datetime.now(timezone.utc)
    week_of = now.strftime("%B %d, %Y")

    lines = []

    # ── Header ─────────────────────────────────────────
    lines.append("=" * 60)
    lines.append(f"WEEKLY INTELLIGENCE BRIEF — {competitor_name.upper()}")
    lines.append(f"Week of {week_of}")
    lines.append(f"Generated: {now.strftime('%Y-%m-%d %H:%M')} UTC")
    lines.append("=" * 60)

    total = len(high_briefings) + len(medium_briefings) + len(low_briefings)
    if total == 0:
        lines.append("\nNO SIGNIFICANT CHANGES DETECTED THIS WEEK")
        lines.append("All monitored sources remain stable.")
        lines.append("\n" + "=" * 60)
        return "\n".join(lines)

    lines.append(f"\nSIGNALS THIS WEEK: {total} detected")
    lines.append(
        f"🔴 {len(high_briefings)} HIGH  |  "
        f"🟡 {len(medium_briefings)} MEDIUM  |  "
        f"🟢 {len(low_briefings)} LOW"
    )

    # ── High Priority ───────────────────────────────────
    if high_briefings:
        lines.append("\n" + "─" * 60)
        lines.append("🔴 HIGH PRIORITY")
        lines.append("─" * 60)
        for b in high_briefings:
            lines.append(f"\n→ {b['signal_type']}")
            lines.append(f"  Confidence: {b['confidence']:.1f}%  |  Sources: {', '.join(b['sources'])}")
            lines.append(f"\n  {b['insight']}")

    # ── Medium Priority ─────────────────────────────────
    if medium_briefings:
        lines.append("\n" + "─" * 60)
        lines.append("🟡 MEDIUM PRIORITY")
        lines.append("─" * 60)
        for b in medium_briefings:
            lines.append(f"\n→ {b['signal_type']}")
            lines.append(f"  Confidence: {b['confidence']:.1f}%  |  Sources: {', '.join(b['sources'])}")
            lines.append(f"\n  {b['insight']}")

    # ── Low Priority ────────────────────────────────────
    if low_briefings:
        lines.append("\n" + "─" * 60)
        lines.append("🟢 WATCH LIST")
        lines.append("─" * 60)
        for b in low_briefings:
            lines.append(f"\n→ {b['signal_type']}")
            lines.append(f"  Confidence: {b['confidence']:.1f}%  |  Sources: {', '.join(b['sources'])}")
            lines.append(f"\n  {b['insight']}")

    # ── Footer ──────────────────────────────────────────
    lines.append("\n" + "=" * 60)
    lines.append("END OF BRIEF")
    lines.append("=" * 60)

    return "\n".join(lines)


# ─────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────

if __name__ == "__main__":
    from database import init_db
    from models.signal import ScoredSignal
    from datetime import timezone

    init_db()

    print("🧪 Testing briefing generator...\n")

    # Test scored signals
    test_signals = [
        ScoredSignal(
            competitor_id=1,
            signal_type="AI positioning added",
            confidence=85.4,
            change_type="AI positioning added",
            priority="HIGH",
            evidence=[
                {
                    "source": "website",
                    "reliability": 0.9,
                    "detail": "AI-powered added to homepage headline",
                    "reasoning": "Direct AI language added to main value prop",
                },
                {
                    "source": "careers",
                    "reliability": 0.8,
                    "detail": "6 AI engineer openings posted",
                    "reasoning": "Hiring for AI roles confirms investment",
                },
            ],
            metadata={
                "sources": ["website", "careers"],
                "sources_count": 2,
                "formula_breakdown": {
                    "agreement_contribution": 28.0,
                    "reliability_contribution": 34.0,
                    "strength_contribution": 16.1,
                }
            }
        ),
        ScoredSignal(
            competitor_id=1,
            signal_type="New market targeted",
            confidence=73.0,
            change_type="New market targeted",
            priority="MEDIUM",
            evidence=[
                {
                    "source": "website",
                    "reliability": 0.9,
                    "detail": "Healthcare vertical page added",
                    "reasoning": "New industry-specific landing page",
                },
            ],
            metadata={
                "sources": ["website"],
                "sources_count": 1,
                "formula_breakdown": {
                    "agreement_contribution": 16.0,
                    "reliability_contribution": 36.0,
                    "strength_contribution": 13.0,
                }
            }
        ),
    ]

    # Generate briefing
    report = generate_briefing(
        competitor_name="Notion",
        scored_signals=test_signals,
        competitor_id=1,
    )

    print("\n" + "="*60)
    print("GENERATED REPORT:")
    print("="*60)
    print(report.report_text)
    print(f"\nTotal signals: {report.total_signals()}")
    print(f"Priority summary: {report.priority_summary()}")

    print("\n✅ Briefing generator test complete!")