# backend/phase5_reporter/why_it_matters.py
# Generates "Why it matters" + forecasting insights for each signal
# This is what turns monitoring into actual intelligence
# Incorporates Event Detection + Rule-Based Forecasting

import sys
import os
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from phase3_classifier.groq_client import call_groq_reporter
from models.signal import ScoredSignal


# ─────────────────────────────────────────
# SYSTEM PROMPT
# ─────────────────────────────────────────

WHY_IT_MATTERS_SYSTEM_PROMPT = """
You are a senior competitive intelligence analyst specializing in 
forward-looking business assessments for startups.

Your job is to explain WHY a competitor signal matters and 
WHAT might happen next based on the evidence.

Rules:
- Be specific — reference the actual signal detected
- Be forward-looking — what should we watch for next
- Give a timeframe when possible (next 30/60/90 days)
- Never make up facts — only reason from evidence provided
- Keep it to 3 bullet points maximum
- Start each bullet with an action verb
- No markdown, no headers, just plain bullet points with -
""".strip()


# ─────────────────────────────────────────
# RULE-BASED FORECASTING PATTERNS
# ─────────────────────────────────────────

# Pattern rules — combinations of signals that suggest future actions
# This is the Rule-Based Forecasting Engine from the spec
FORECAST_RULES = {
    "AI positioning added": {
        "watch_for": [
            "AI product launch within 60-90 days",
            "Pricing restructure to monetize AI features",
            "Enterprise sales push targeting AI-forward buyers",
        ],
        "timeframe": "60-90 days",
        "strategic_implication": "competitor is moving up-market with AI capabilities",
    },
    "New feature detected": {
        "watch_for": [
            "Marketing campaign highlighting new capability",
            "Pricing tier update to monetize new feature",
            "Competitor case studies featuring the new feature",
        ],
        "timeframe": "30-60 days",
        "strategic_implication": "product velocity is increasing",
    },
    "Pricing restructured": {
        "watch_for": [
            "Sales team expansion to close larger deals",
            "Enterprise customer announcements",
            "Churn from price-sensitive existing customers",
        ],
        "timeframe": "30-60 days",
        "strategic_implication": "moving toward enterprise monetization",
    },
    "Messaging shifted": {
        "watch_for": [
            "New marketing campaigns with updated positioning",
            "Changes in target audience on ads",
            "Updated sales collateral and pitch decks",
        ],
        "timeframe": "30 days",
        "strategic_implication": "repositioning in response to market pressure",
    },
    "New market targeted": {
        "watch_for": [
            "Industry-specific partnerships or integrations",
            "Compliance certifications for new vertical",
            "Dedicated sales team for new market",
        ],
        "timeframe": "90 days",
        "strategic_implication": "geographic or vertical expansion in progress",
    },
    "Hiring surge detected": {
        "watch_for": [
            "Product or feature launch 3-6 months after hiring",
            "New market entry following regional hiring",
            "Leadership announcements for new divisions",
        ],
        "timeframe": "3-6 months",
        "strategic_implication": "significant growth or pivot underway",
    },
    "Funding signal": {
        "watch_for": [
            "Aggressive pricing cuts to gain market share",
            "Rapid hiring across all departments",
            "Major product announcements within 90 days",
        ],
        "timeframe": "90 days",
        "strategic_implication": "war chest being deployed for growth",
    },
    "Product launch": {
        "watch_for": [
            "Customer acquisition push targeting your users",
            "Pricing promotion around launch period",
            "Press and analyst coverage amplifying reach",
        ],
        "timeframe": "30 days",
        "strategic_implication": "direct competitive pressure increasing",
    },
    "Leadership change": {
        "watch_for": [
            "Strategic pivot reflecting new leader's background",
            "Team restructuring within 60-90 days",
            "Updated company messaging and positioning",
        ],
        "timeframe": "60-90 days",
        "strategic_implication": "strategy shift likely under new leadership",
    },
    "Competitive threat": {
        "watch_for": [
            "Direct feature parity with your product",
            "Competitive pricing targeting your customers",
            "Sales team trained on your weaknesses",
        ],
        "timeframe": "30-60 days",
        "strategic_implication": "direct competitive attack in progress",
    },
}


# ─────────────────────────────────────────
# STRUCTURED EVENT DETECTION
# ─────────────────────────────────────────

def detect_structured_event(signal: ScoredSignal) -> dict:
    """
    Convert a scored signal into a structured business event.
    This is the Event Detection Module from the spec.

    Args:
        signal: ScoredSignal object from Phase 4

    Returns:
        Structured event dict with type, entity, source, date, confidence
    """
    # Map change types to structured event types
    event_type_map = {
        "AI positioning added":   "AI_POSITIONING_ADDED",
        "New feature detected":   "FEATURE_ADDED",
        "Pricing restructured":   "PRICING_RESTRUCTURED",
        "Hiring surge detected":  "HIRING_SURGE",
        "New market targeted":    "MARKET_EXPANSION",
        "Messaging shifted":      "MESSAGING_SHIFT",
        "Funding signal":         "FUNDING_DETECTED",
        "Product launch":         "PRODUCT_LAUNCHED",
        "Leadership change":      "LEADERSHIP_CHANGE",
        "Competitive threat":     "COMPETITIVE_THREAT",
        "Unknown change":         "UNKNOWN_EVENT",
    }

    # Extract entity from evidence
    entity = _extract_entity(signal)

    event = {
        "event_type": event_type_map.get(signal.change_type, "UNKNOWN_EVENT"),
        "entity": entity,
        "source": ", ".join(signal.metadata.get("sources", ["unknown"])),
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "confidence": round(signal.confidence, 1),
        "priority": signal.priority,
        "signal_type": signal.signal_type,
    }

    return event


def _extract_entity(signal: ScoredSignal) -> str:
    """Extract the main entity/subject from signal evidence."""
    if signal.evidence:
        detail = signal.evidence[0].get("detail", "")
        if detail:
            # Return first 50 chars of key evidence as entity
            return detail[:50].strip()
    return signal.signal_type


# ─────────────────────────────────────────
# MAIN FUNCTION
# ─────────────────────────────────────────

def generate_why_it_matters(signal: ScoredSignal, competitor_name: str) -> dict:
    """
    Generate "Why it matters" analysis for a single signal.
    Combines rule-based forecasting + Groq analysis.

    Args:
        signal: ScoredSignal object from Phase 4
        competitor_name: Name of the competitor

    Returns:
        Dict with why_it_matters text, forecast, and structured event
    """
    print(f"   💡 Generating 'Why it matters' for: {signal.signal_type}")

    # Get rule-based forecast
    forecast_rule = FORECAST_RULES.get(signal.signal_type, {})

    # Detect structured event
    structured_event = detect_structured_event(signal)

    # Generate Groq-powered "Why it matters"
    why_text = _generate_why_text(signal, competitor_name, forecast_rule)

    return {
        "why_it_matters": why_text,
        "watch_for": forecast_rule.get("watch_for", []),
        "timeframe": forecast_rule.get("timeframe", "Unknown"),
        "strategic_implication": forecast_rule.get("strategic_implication", ""),
        "structured_event": structured_event,
    }


def generate_why_it_matters_batch(
    signals: list[ScoredSignal],
    competitor_name: str,
) -> list[dict]:
    """
    Generate "Why it matters" for all signals.

    Args:
        signals: List of ScoredSignal objects
        competitor_name: Name of the competitor

    Returns:
        List of why_it_matters dicts
    """
    results = []
    for signal in signals:
        try:
            result = generate_why_it_matters(signal, competitor_name)
            results.append(result)
        except Exception as e:
            print(f"❌ Why it matters failed for {signal.signal_type}: {e}")
            results.append({
                "why_it_matters": "Analysis unavailable.",
                "watch_for": [],
                "timeframe": "Unknown",
                "strategic_implication": "",
                "structured_event": detect_structured_event(signal),
            })
    return results


# ─────────────────────────────────────────
# INTERNAL HELPERS
# ─────────────────────────────────────────

def _generate_why_text(
    signal: ScoredSignal,
    competitor_name: str,
    forecast_rule: dict,
) -> str:
    """
    Use Groq to generate "Why it matters" explanation.
    Combines evidence + rule-based patterns.
    """
    watch_for = forecast_rule.get("watch_for", [])
    timeframe = forecast_rule.get("timeframe", "next quarter")
    implication = forecast_rule.get("strategic_implication", "")

    evidence_summary = _summarize_evidence(signal.evidence)

    prompt = f"""
Generate a "Why it matters" analysis for this competitive signal.

Competitor: {competitor_name}
Signal detected: {signal.signal_type}
Confidence: {signal.confidence:.1f}%
Evidence: {evidence_summary}
Strategic implication: {implication}
Watch for in {timeframe}: {', '.join(watch_for[:2]) if watch_for else 'further developments'}

Write exactly 3 bullet points explaining:
1. Why this change matters right now
2. What it signals about their strategy  
3. What to watch for in the next {timeframe}

Start each bullet with -
Be specific and actionable.
""".strip()

    response = call_groq_reporter(
        prompt=prompt,
        system_prompt=WHY_IT_MATTERS_SYSTEM_PROMPT,
    )

    if not response:
        return _fallback_why_text(signal, competitor_name, forecast_rule)

    return response


def _fallback_why_text(
    signal: ScoredSignal,
    competitor_name: str,
    forecast_rule: dict,
) -> str:
    """Fallback if Groq fails — use rule-based text."""
    watch_for = forecast_rule.get("watch_for", [])
    timeframe = forecast_rule.get("timeframe", "next quarter")
    implication = forecast_rule.get("strategic_implication", "a strategic shift")

    lines = [
        f"- {competitor_name} is showing signs of {implication}.",
        f"- This signal was detected across {len(signal.evidence)} source(s) with {signal.confidence:.1f}% confidence.",
        f"- Watch for {watch_for[0] if watch_for else 'further developments'} within {timeframe}.",
    ]
    return "\n".join(lines)


def _summarize_evidence(evidence: list) -> str:
    """Build concise evidence summary."""
    if not evidence:
        return "No specific evidence"
    parts = []
    for e in evidence[:3]:
        source = e.get("source", "unknown")
        detail = e.get("detail", "")[:80]
        parts.append(f"{source}: {detail}")
    return " | ".join(parts)


# ─────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────

if __name__ == "__main__":
    from database import init_db
    from models.signal import ScoredSignal

    init_db()

    print("🧪 Testing why_it_matters generator...\n")

    test_signal = ScoredSignal(
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
                "reasoning": "Direct AI language in main value prop",
            },
            {
                "source": "careers",
                "reliability": 0.8,
                "detail": "6 AI engineer openings posted",
                "reasoning": "Hiring confirms AI investment",
            },
        ],
        metadata={
            "sources": ["website", "careers"],
            "sources_count": 2,
        }
    )

    result = generate_why_it_matters(test_signal, "Notion")

    print("\n--- RESULTS ---")
    print(f"\nWHY IT MATTERS:")
    print(result["why_it_matters"])
    print(f"\nWATCH FOR (in {result['timeframe']}):")
    for w in result["watch_for"]:
        print(f"  • {w}")
    print(f"\nSTRATEGIC IMPLICATION:")
    print(f"  {result['strategic_implication']}")
    print(f"\nSTRUCTURED EVENT:")
    for k, v in result["structured_event"].items():
        print(f"  {k}: {v}")

    print("\n✅ Why it matters test complete!")