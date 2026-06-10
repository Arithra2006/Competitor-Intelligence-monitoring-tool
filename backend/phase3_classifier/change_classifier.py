# backend/phase3_classifier/change_classifier.py
# Classifies what KIND of change happened using Groq API
# This is the core intelligence of Phase 3
# Turns raw text diffs into structured change types

import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from groq_client import call_groq
from models.signal import ClassifiedSignal, CHANGE_TYPES
from models.snapshot import DetectedChange


# ─────────────────────────────────────────
# SYSTEM PROMPT
# ─────────────────────────────────────────

CLASSIFIER_SYSTEM_PROMPT = """
You are a competitive intelligence analyst specializing in detecting 
meaningful business changes from website and content updates.

Your job is to classify what TYPE of change occurred between two versions 
of a competitor's content.

You must respond ONLY with a valid JSON object. No explanation, no markdown,
no extra text — just the JSON.

Change types you can classify:
- "AI positioning added"      → AI/ML language added to messaging
- "New feature detected"      → New product feature or capability mentioned
- "Pricing restructured"      → Pricing page or tier changes
- "Messaging shifted"         → Target audience or value prop language changed
- "New market targeted"       → New vertical, geography, or segment mentioned
- "Hiring surge detected"     → Significant increase in job postings
- "Leadership change"         → Executive hire, departure, or role change
- "Funding signal"            → Investment, funding round, or financial news
- "Product launch"            → New product or major release announced
- "Competitive threat"        → Direct competitive positioning against others
- "Unknown change"            → Change detected but type unclear

Respond with this exact JSON format:
{
    "change_type": "one of the change types above",
    "confidence": 85,
    "reasoning": "one sentence explaining why",
    "key_evidence": "the specific text that shows this change"
}
""".strip()


# ─────────────────────────────────────────
# MAIN CLASSIFIER FUNCTION
# ─────────────────────────────────────────

def classify_change(detected_change: DetectedChange) -> ClassifiedSignal | None:
    """
    Classify what kind of change happened using Groq API.
    This is the portfolio-worthy function — not just 'something changed'
    but 'what kind of change and why it matters'.

    Args:
        detected_change: DetectedChange object from Phase 2

    Returns:
        ClassifiedSignal object with change type and confidence, or None on failure
    """
    print(f"🧠 Classifying change — source: {detected_change.source}")

    # Build the classification prompt
    prompt = _build_classification_prompt(detected_change)

    # Call Groq API
    raw_response = call_groq(
        prompt=prompt,
        system_prompt=CLASSIFIER_SYSTEM_PROMPT,
        max_tokens=500,
        temperature=0.1,   # Low temperature = consistent, focused output
    )

    if not raw_response:
        print(f"❌ Groq returned empty response for {detected_change.source}")
        return None

    # Parse JSON response
    classification = _parse_classification_response(raw_response)

    if not classification:
        print(f"❌ Could not parse Groq response for {detected_change.source}")
        return None

    change_type = classification.get("change_type", "Unknown change")
    confidence  = classification.get("confidence", 50)
    reasoning   = classification.get("reasoning", "")
    key_evidence = classification.get("key_evidence", "")

    # Validate change type
    if change_type not in CHANGE_TYPES:
        print(f"⚠️  Unknown change type '{change_type}' — defaulting to 'Unknown change'")
        change_type = "Unknown change"

    print(f"   ✅ Classified as: {change_type}")
    print(f"   Confidence     : {confidence}%")
    print(f"   Reasoning      : {reasoning}")

    # Build ClassifiedSignal
    signal = ClassifiedSignal(
        competitor_id=detected_change.competitor_id,
        source=detected_change.source,
        url=detected_change.url,
        change_type=change_type,
        old_text=detected_change.old_text,
        new_text=detected_change.new_text,
        similarity_score=detected_change.similarity_score,
        raw_classification=raw_response,
        metadata={
            "confidence": confidence,
            "reasoning": reasoning,
            "key_evidence": key_evidence,
            "similarity_score": detected_change.similarity_score,
            "change_magnitude": detected_change.change_magnitude(),
        }
    )

    return signal


def classify_changes_batch(
    detected_changes: list[DetectedChange],
) -> list[ClassifiedSignal]:
    """
    Classify multiple detected changes.
    Processes one by one to avoid Groq rate limits.

    Args:
        detected_changes: List of DetectedChange objects from Phase 2

    Returns:
        List of ClassifiedSignal objects
    """
    if not detected_changes:
        print("⚠️  No changes to classify")
        return []

    print(f"\n🧠 Classifying {len(detected_changes)} detected change(s)...")
    classified = []

    for i, change in enumerate(detected_changes, 1):
        print(f"\n── Change {i}/{len(detected_changes)} ──")
        try:
            signal = classify_change(change)
            if signal:
                classified.append(signal)
        except Exception as e:
            print(f"❌ Classification failed for {change.source}: {e}")
            continue

    print(f"\n✅ Classification complete — {len(classified)}/{len(detected_changes)} classified")
    return classified


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────

def _build_classification_prompt(change: DetectedChange) -> str:
    """
    Build the classification prompt for Groq.
    Includes old text, new text, source, and similarity score.
    """
    # Truncate texts to avoid token limits
    old_preview = change.old_text[:1500] if change.old_text else "No previous version"
    new_preview = change.new_text[:1500] if change.new_text else "No new content"

    return f"""
Analyze this competitor content change and classify it.

SOURCE: {change.source}
URL: {change.url}
SIMILARITY SCORE: {change.similarity_score:.2f} (lower = more different)
CHANGE MAGNITUDE: {change.change_magnitude()}

PREVIOUS VERSION:
{old_preview}

NEW VERSION:
{new_preview}

Classify this change and respond with the JSON format specified.
""".strip()


def _parse_classification_response(raw_response: str) -> dict | None:
    """
    Parse Groq's JSON response safely.
    Handles cases where model adds extra text around JSON.
    """
    try:
        # Try direct JSON parse first
        return json.loads(raw_response)
    except json.JSONDecodeError:
        pass

    # Try to extract JSON from response if model added extra text
    try:
        start = raw_response.find("{")
        end = raw_response.rfind("}") + 1
        if start != -1 and end > start:
            json_str = raw_response[start:end]
            return json.loads(json_str)
    except json.JSONDecodeError:
        pass

    print(f"⚠️  Could not parse JSON from response: {raw_response[:200]}")
    return None


# ─────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────

if __name__ == "__main__":
    from database import init_db
    from models.snapshot import DetectedChange

    init_db()

    print("🧪 Testing change classifier...\n")

    # Test 1 — AI positioning change
    print("=== TEST 1 — AI Positioning ===")
    change1 = DetectedChange(
        competitor_id=1,
        source="website",
        url="https://notion.so",
        old_text="Our platform provides analytics and reporting tools for business teams.",
        new_text="Our AI-powered platform provides predictive analytics, ML forecasting, and automated reporting for enterprise teams.",
        similarity_score=0.62,
    )
    signal1 = classify_change(change1)
    if signal1:
        print(f"   Change type : {signal1.change_type}")
        print(f"   Priority    : {signal1.priority_emoji()} {signal1.priority()}")

    # Test 2 — Pricing change
    print("\n=== TEST 2 — Pricing Change ===")
    change2 = DetectedChange(
        competitor_id=1,
        source="website",
        url="https://notion.so/pricing",
        old_text="Simple pricing: Free plan and Pro plan at $10/month.",
        new_text="Flexible pricing: Free, Pro at $10/month, Business at $25/month, and Enterprise with custom pricing. New team add-ons available.",
        similarity_score=0.58,
    )
    signal2 = classify_change(change2)
    if signal2:
        print(f"   Change type : {signal2.change_type}")
        print(f"   Priority    : {signal2.priority_emoji()} {signal2.priority()}")

    # Test 3 — New market
    print("\n=== TEST 3 — New Market ===")
    change3 = DetectedChange(
        competitor_id=1,
        source="website",
        url="https://notion.so",
        old_text="The workspace for your team. Organize notes, tasks and wikis.",
        new_text="The workspace for your team. Built for healthcare, legal, and financial services teams. HIPAA compliant.",
        similarity_score=0.71,
    )
    signal3 = classify_change(change3)
    if signal3:
        print(f"   Change type : {signal3.change_type}")
        print(f"   Priority    : {signal3.priority_emoji()} {signal3.priority()}")

    print("\n✅ Change classifier test complete!")