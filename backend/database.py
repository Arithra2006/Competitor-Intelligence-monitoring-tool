# backend/database.py
# SQLite database setup and all query functions
# Used by every phase to store and retrieve data

import sqlite3
import json
from datetime import datetime
from pathlib import Path

# Database file will be created in backend/ folder
DB_PATH = Path(__file__).parent / "intelligence.db"


def get_connection():
    """Get SQLite connection with row factory for dict-like access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _clean_github_org(value):
    """
    Accepts either a plain org name ('calcom') or a full GitHub URL
    ('https://github.com/calcom') and always returns just the org name.
    """
    if not value:
        return value

    value = value.strip()  # removes stray spaces

    if "github.com" in value:
        value = value.split("github.com/")[-1]
        value = value.strip("/").split("/")[0]

    return value

def init_db():
    """Create all tables if they don't exist. Run once on startup."""
    conn = get_connection()
    cursor = conn.cursor()

    # Competitors table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS competitors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            website_url TEXT NOT NULL,
            careers_url TEXT,
            github_org TEXT,
            reddit_keyword TEXT,
            frequency TEXT DEFAULT 'weekly',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Raw snapshots table — full page text saved every crawl
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            competitor_id INTEGER NOT NULL,
            source TEXT NOT NULL,
            url TEXT NOT NULL,
            raw_text TEXT,
            embedding TEXT,
            change_type TEXT,
            confidence INTEGER,
            crawled_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (competitor_id) REFERENCES competitors(id)
        )
    """)

    # Signals table — meaningful changes detected
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            competitor_id INTEGER NOT NULL,
            signal_type TEXT NOT NULL,
            confidence REAL,
            evidence TEXT,
            detected_at TEXT DEFAULT CURRENT_TIMESTAMP,
            feedback TEXT DEFAULT NULL,
            FOREIGN KEY (competitor_id) REFERENCES competitors(id)
        )
    """)

    # Reports table — full weekly briefings
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            competitor_id INTEGER NOT NULL,
            report_text TEXT,
            generated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (competitor_id) REFERENCES competitors(id)
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Database initialized successfully.")


# ─────────────────────────────────────────
# COMPETITOR QUERIES
# ─────────────────────────────────────────

def insert_competitor(name, website_url, careers_url=None,
                      github_org=None, reddit_keyword=None, frequency="weekly"):
    """Add a new competitor to track."""
    github_org = _clean_github_org(github_org)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO competitors (name, website_url, careers_url, github_org, reddit_keyword, frequency)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, website_url, careers_url, github_org, reddit_keyword, frequency))
    conn.commit()
    competitor_id = cursor.lastrowid
    conn.close()
    return competitor_id


def get_all_competitors():
    """Return all tracked competitors."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM competitors")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_competitor_by_id(competitor_id):
    """Return a single competitor by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM competitors WHERE id = ?", (competitor_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def delete_competitor(competitor_id):
    """Remove a competitor from tracking."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM competitors WHERE id = ?", (competitor_id,))
    conn.commit()
    conn.close()


# ─────────────────────────────────────────
# SNAPSHOT QUERIES
# ─────────────────────────────────────────

def insert_snapshot(competitor_id, source, url, raw_text,
                    embedding=None, change_type=None, confidence=None):
    """Save a full page snapshot after every crawl."""
    conn = get_connection()
    cursor = conn.cursor()
    embedding_str = json.dumps(embedding) if embedding else None
    cursor.execute("""
        INSERT INTO snapshots (competitor_id, source, url, raw_text, embedding, change_type, confidence)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (competitor_id, source, url, raw_text, embedding_str, change_type, confidence))
    conn.commit()
    snapshot_id = cursor.lastrowid
    conn.close()
    return snapshot_id


def get_latest_snapshot(competitor_id, source):
    """Get the most recent snapshot for a competitor + source combo."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM snapshots
        WHERE competitor_id = ? AND source = ?
        ORDER BY crawled_at DESC
        LIMIT 1
    """, (competitor_id, source))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_snapshots_by_competitor(competitor_id):
    """Get all snapshots for a competitor."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM snapshots
        WHERE competitor_id = ?
        ORDER BY crawled_at DESC
    """, (competitor_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ─────────────────────────────────────────
# SIGNAL QUERIES
# ─────────────────────────────────────────

def insert_signal(competitor_id, signal_type, confidence, evidence):
    """Save a detected signal with structured evidence."""
    conn = get_connection()
    cursor = conn.cursor()
    evidence_str = json.dumps(evidence)
    cursor.execute("""
        INSERT INTO signals (competitor_id, signal_type, confidence, evidence)
        VALUES (?, ?, ?, ?)
    """, (competitor_id, signal_type, confidence, evidence_str))
    conn.commit()
    signal_id = cursor.lastrowid
    conn.close()
    return signal_id


def get_signals_by_competitor(competitor_id):
    """Get all signals for a competitor."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM signals
        WHERE competitor_id = ?
        ORDER BY detected_at DESC
    """, (competitor_id,))
    rows = cursor.fetchall()
    conn.close()
    results = []
    for row in rows:
        r = dict(row)
        r["evidence"] = json.loads(r["evidence"]) if r["evidence"] else []
        results.append(r)
    return results


def update_signal_feedback(signal_id, feedback):
    """Save user feedback — 'useful' or 'irrelevant'."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE signals SET feedback = ? WHERE id = ?
    """, (feedback, signal_id))
    conn.commit()
    conn.close()


# ─────────────────────────────────────────
# REPORT QUERIES
# ─────────────────────────────────────────

def insert_report(competitor_id, report_text):
    """Save a generated weekly report."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO reports (competitor_id, report_text)
        VALUES (?, ?)
    """, (competitor_id, report_text))
    conn.commit()
    report_id = cursor.lastrowid
    conn.close()
    return report_id


def get_reports_by_competitor(competitor_id):
    """Get all reports for a competitor."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM reports
        WHERE competitor_id = ?
        ORDER BY generated_at DESC
    """, (competitor_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_feedback_stats_by_source() -> dict:
    """
    Analyze feedback patterns per source.
    Returns count of useful/irrelevant ratings per source.
    Used by weight adjuster to tune reliability weights.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM signals
        WHERE feedback IS NOT NULL
    """)
    rows = cursor.fetchall()
    conn.close()

    # Count feedback per source from evidence JSON
    stats = {}

    for row in rows:
        signal = dict(row)
        feedback = signal.get("feedback")
        evidence = json.loads(signal.get("evidence", "[]"))

        for e in evidence:
            source = e.get("source", "unknown")
            if source not in stats:
                stats[source] = {"useful": 0, "irrelevant": 0, "total": 0}
            stats[source][feedback] = stats[source].get(feedback, 0) + 1
            stats[source]["total"] += 1

    return stats


def get_adjusted_weights() -> dict:
    """
    Get current adjusted weights from database.
    Returns dict of source -> weight.
    Falls back to defaults if no adjustments stored.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Create weights table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS source_weights (
            source TEXT PRIMARY KEY,
            weight REAL NOT NULL,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

    cursor.execute("SELECT source, weight FROM source_weights")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return {}

    return {row["source"]: row["weight"] for row in rows}


def save_adjusted_weight(source: str, weight: float) -> None:
    """Save an adjusted weight for a source to database."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS source_weights (
            source TEXT PRIMARY KEY,
            weight REAL NOT NULL,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        INSERT INTO source_weights (source, weight, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(source) DO UPDATE SET
            weight = excluded.weight,
            updated_at = excluded.updated_at
    """, (source, weight))

    conn.commit()
    conn.close()


# Run init when this file is executed directly
if __name__ == "__main__":
    init_db()