# backend/phase5_reporter/battlecard_generator.py
# Generates competitive battlecards using Groq AI
# Combines intelligence signals with company context
# Produces sales-ready battlecards automatically

import json
import sys
import os
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from phase3_classifier.groq_client import call_groq_reporter
from models.battlecard import Battlecard
from database import get_signals_by_competitor, get_competitor_by_id


# ─────────────────────────────────────────
# COMPANY CONTEXT
# ─────────────────────────────────────────

OUR_COMPANY    = os.getenv("YOUR_COMPANY_NAME", "IntelliStart")
OUR_STRENGTHS  = os.getenv(
    "YOUR_COMPANY_STRENGTHS",
    "Affordable pricing, fast onboarding, open source, no vendor lock-in, lightweight and customizable"
)
OUR_WEAKNESSES = os.getenv(
    "YOUR_COMPANY_WEAKNESSES",
    "Smaller team, less brand recognition, fewer integrations than enterprise tools"
)


# ─────────────────────────────────────────
# SYSTEM PROMPT
# ─────────────────────────────────────────

BATTLECARD_SYSTEM_PROMPT = """
You are a competitive intelligence analyst creating sales battlecards.
A battlecard helps sales reps win deals against a specific competitor.

You must respond ONLY with a valid JSON object.
No markdown, no explanation, no extra text — just the JSON.

The JSON must have exactly these keys:
{
    "our_strengths": ["list of our strengths vs this competitor"],
    "our_weaknesses": ["list of our weaknesses vs this competitor"],
    "their_strengths": ["list of competitor strengths"],
    "their_weaknesses": ["list of competitor weaknesses to exploit"],
    "recent_moves": ["list of recent competitor moves detected"],
    "how_to_win": ["list of specific tactics to win deals against them"],
    "watch_out_for": ["list of things to watch for from this competitor"],
    "key_differentiators": ["list of key reasons to choose us over them"]
}

Each list should have 3-5 items maximum.
Be specific, actionable, and concise.
Base recent_moves on the intelligence signals provided.
""".strip()


# ─────────────────────────────────────────
# MAIN GENERATOR FUNCTION
# ─────────────────────────────────────────

def generate_battlecard(competitor_id: int) -> Battlecard | None:
    """
    Generate a competitive battlecard for a competitor.
    Uses existing intelligence signals + Groq AI.

    Args:
        competitor_id: ID of the competitor

    Returns:
        Battlecard object or None on failure
    """
    competitor = get_competitor_by_id(competitor_id)
    if not competitor:
        print(f"❌ Competitor {competitor_id} not found")
        return None

    competitor_name = competitor["name"]
    print(f"\n🃏 Generating battlecard for: {competitor_name}")

    # Get all signals for this competitor
    signals = get_signals_by_competitor(competitor_id)

    # Build context from signals
    signal_context = _build_signal_context(signals)

    # Calculate average confidence
    avg_confidence = 0.0
    if signals:
        avg_confidence = sum(s.get("confidence", 0) for s in signals) / len(signals)

    # Generate battlecard using Groq
    battlecard_data = _generate_with_groq(
        competitor_name=competitor_name,
        signal_context=signal_context,
    )

    if not battlecard_data:
        print(f"❌ Failed to generate battlecard for {competitor_name}")
        return None

    # Build Battlecard object
    battlecard = Battlecard(
        competitor_id=competitor_id,
        competitor_name=competitor_name,
        our_company=OUR_COMPANY,
        our_strengths=battlecard_data.get("our_strengths", []),
        our_weaknesses=battlecard_data.get("our_weaknesses", []),
        their_strengths=battlecard_data.get("their_strengths", []),
        their_weaknesses=battlecard_data.get("their_weaknesses", []),
        recent_moves=battlecard_data.get("recent_moves", []),
        how_to_win=battlecard_data.get("how_to_win", []),
        watch_out_for=battlecard_data.get("watch_out_for", []),
        key_differentiators=battlecard_data.get("key_differentiators", []),
        confidence_score=round(avg_confidence, 1),
        raw_battlecard=json.dumps(battlecard_data),
        metadata={
            "signals_used": len(signals),
            "our_company": OUR_COMPANY,
            "our_strengths_input": OUR_STRENGTHS,
            "our_weaknesses_input": OUR_WEAKNESSES,
        }
    )

    # Save to database
    _save_battlecard(battlecard)

    print(f"✅ Battlecard generated for {competitor_name}")
    print(f"   Signals used    : {len(signals)}")
    print(f"   Confidence      : {avg_confidence:.1f}%")
    print(f"   How to win tips : {len(battlecard.how_to_win)}")

    return battlecard


# ─────────────────────────────────────────
# INTERNAL HELPERS
# ─────────────────────────────────────────

def _build_signal_context(signals: list) -> str:
    """
    Build a concise signal summary for the Groq prompt.
    Includes signal types, confidence, and evidence details.
    """
    if not signals:
        return "No intelligence signals detected yet for this competitor."

    lines = [f"INTELLIGENCE SIGNALS ({len(signals)} total):"]

    for signal in signals[:10]:  # Max 10 signals
        signal_type = signal.get("signal_type", "Unknown")
        confidence  = signal.get("confidence", 0)
        evidence    = signal.get("evidence", [])
        detected_at = signal.get("detected_at", "")[:10]

        lines.append(f"\n• {signal_type} (confidence: {confidence:.0f}%)")
        lines.append(f"  Detected: {detected_at}")

        for e in evidence[:2]:  # Max 2 evidence items per signal
            detail = e.get("detail", "")[:100]
            source = e.get("source", "")
            if detail:
                lines.append(f"  Evidence [{source}]: {detail}")

    return "\n".join(lines)


def _generate_with_groq(
    competitor_name: str,
    signal_context: str,
) -> dict | None:
    """
    Call Groq to generate battlecard content.
    Returns parsed JSON dict or None on failure.
    """
    prompt = f"""
Generate a competitive battlecard for our sales team.

OUR COMPANY: {OUR_COMPANY}
OUR STRENGTHS: {OUR_STRENGTHS}
OUR WEAKNESSES: {OUR_WEAKNESSES}

COMPETITOR: {competitor_name}

LATEST INTELLIGENCE:
{signal_context}

Generate the battlecard JSON now.
""".strip()

    response = call_groq_reporter(
        prompt=prompt,
        system_prompt=BATTLECARD_SYSTEM_PROMPT,
    )

    if not response:
        return None

    # Parse JSON response
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        # Try to extract JSON
        try:
            start = response.find("{")
            end   = response.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(response[start:end])
        except Exception:
            pass
        print(f"⚠️  Could not parse battlecard JSON: {response[:200]}")
        return None


def _save_battlecard(battlecard: Battlecard) -> None:
    """Save battlecard to SQLite database."""
    from database import get_connection
    conn = get_connection()
    cursor = conn.cursor()

    # Create battlecards table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS battlecards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            competitor_id INTEGER NOT NULL,
            competitor_name TEXT NOT NULL,
            our_company TEXT,
            our_strengths TEXT,
            our_weaknesses TEXT,
            their_strengths TEXT,
            their_weaknesses TEXT,
            recent_moves TEXT,
            how_to_win TEXT,
            watch_out_for TEXT,
            key_differentiators TEXT,
            confidence_score REAL,
            raw_battlecard TEXT,
            metadata TEXT,
            generated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (competitor_id) REFERENCES competitors(id)
        )
    """)

    # Upsert — one battlecard per competitor (update if exists)
    cursor.execute("""
        SELECT id FROM battlecards WHERE competitor_id = ?
    """, (battlecard.competitor_id,))
    existing = cursor.fetchone()

    if existing:
        cursor.execute("""
            UPDATE battlecards SET
                our_strengths = ?,
                our_weaknesses = ?,
                their_strengths = ?,
                their_weaknesses = ?,
                recent_moves = ?,
                how_to_win = ?,
                watch_out_for = ?,
                key_differentiators = ?,
                confidence_score = ?,
                raw_battlecard = ?,
                metadata = ?,
                generated_at = CURRENT_TIMESTAMP
            WHERE competitor_id = ?
        """, (
            json.dumps(battlecard.our_strengths),
            json.dumps(battlecard.our_weaknesses),
            json.dumps(battlecard.their_strengths),
            json.dumps(battlecard.their_weaknesses),
            json.dumps(battlecard.recent_moves),
            json.dumps(battlecard.how_to_win),
            json.dumps(battlecard.watch_out_for),
            json.dumps(battlecard.key_differentiators),
            battlecard.confidence_score,
            battlecard.raw_battlecard,
            json.dumps(battlecard.metadata),
            battlecard.competitor_id,
        ))
    else:
        cursor.execute("""
            INSERT INTO battlecards (
                competitor_id, competitor_name, our_company,
                our_strengths, our_weaknesses,
                their_strengths, their_weaknesses,
                recent_moves, how_to_win, watch_out_for,
                key_differentiators, confidence_score,
                raw_battlecard, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            battlecard.competitor_id,
            battlecard.competitor_name,
            battlecard.our_company,
            json.dumps(battlecard.our_strengths),
            json.dumps(battlecard.our_weaknesses),
            json.dumps(battlecard.their_strengths),
            json.dumps(battlecard.their_weaknesses),
            json.dumps(battlecard.recent_moves),
            json.dumps(battlecard.how_to_win),
            json.dumps(battlecard.watch_out_for),
            json.dumps(battlecard.key_differentiators),
            battlecard.confidence_score,
            battlecard.raw_battlecard,
            json.dumps(battlecard.metadata),
        ))

    conn.commit()
    conn.close()


def get_battlecard(competitor_id: int) -> Battlecard | None:
    """Retrieve saved battlecard for a competitor."""
    from database import get_connection
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS battlecards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            competitor_id INTEGER NOT NULL,
            competitor_name TEXT NOT NULL,
            our_company TEXT,
            our_strengths TEXT,
            our_weaknesses TEXT,
            their_strengths TEXT,
            their_weaknesses TEXT,
            recent_moves TEXT,
            how_to_win TEXT,
            watch_out_for TEXT,
            key_differentiators TEXT,
            confidence_score REAL,
            raw_battlecard TEXT,
            metadata TEXT,
            generated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        SELECT * FROM battlecards WHERE competitor_id = ?
    """, (competitor_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    row = dict(row)
    return Battlecard(
        competitor_id=row["competitor_id"],
        competitor_name=row["competitor_name"],
        our_company=row.get("our_company", OUR_COMPANY),
        our_strengths=json.loads(row.get("our_strengths", "[]")),
        our_weaknesses=json.loads(row.get("our_weaknesses", "[]")),
        their_strengths=json.loads(row.get("their_strengths", "[]")),
        their_weaknesses=json.loads(row.get("their_weaknesses", "[]")),
        recent_moves=json.loads(row.get("recent_moves", "[]")),
        how_to_win=json.loads(row.get("how_to_win", "[]")),
        watch_out_for=json.loads(row.get("watch_out_for", "[]")),
        key_differentiators=json.loads(row.get("key_differentiators", "[]")),
        confidence_score=row.get("confidence_score", 0.0),
        raw_battlecard=row.get("raw_battlecard", ""),
        generated_at=row.get("generated_at", ""),
        metadata=json.loads(row.get("metadata", "{}")),
    )


# ─────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────

if __name__ == "__main__":
    from database import init_db, get_all_competitors

    init_db()

    print("🧪 Testing battlecard generator...\n")
    print(f"Our company  : {OUR_COMPANY}")
    print(f"Our strengths: {OUR_STRENGTHS}")

    competitors = get_all_competitors()
    if not competitors:
        print("❌ No competitors in database")
        exit(1)

    competitor = competitors[-1]
    print(f"\nGenerating battlecard for: {competitor['name']}")

    battlecard = generate_battlecard(competitor["id"])

    if battlecard:
        print("\n" + "="*60)
        print(battlecard.format_text())
        print("="*60)
    else:
        print("❌ Battlecard generation failed")