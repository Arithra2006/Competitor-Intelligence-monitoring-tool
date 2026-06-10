# backend/phase2_detector/similarity_checker.py
# Compares new embedding vs stored embedding
# Filters out trivial changes — only passes meaningful changes forward
# This is the critical filter that stops noise from reaching Groq

import sys
import os
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from embedder import generate_embedding, compute_cosine_similarity
from chroma_client import store_embedding, get_stored_embedding
from models.snapshot import DetectedChange


# ─────────────────────────────────────────
# THRESHOLDS
# ─────────────────────────────────────────

# Similarity below this = meaningful change → passes to classifier
# Similarity above this = trivial change → filtered out
#
# 0.85 means: "if pages are less than 85% similar, something changed"
# Adjust based on real data:
#   Lower (0.80) = more sensitive, more changes detected
#   Higher (0.90) = less sensitive, only major changes pass
SIMILARITY_THRESHOLD = 0.85

# Per-source thresholds — some sources change more naturally
SOURCE_THRESHOLDS = {
    "website": 0.85,   # Homepages change slowly — high threshold
    "careers": 0.80,   # Job pages change often — slightly lower
    "news": 0.70,      # News always different — lower threshold
    "github": 0.75,    # Commits change frequently — lower threshold
    "reddit": 0.70,    # Reddit always new posts — lower threshold
}


# ─────────────────────────────────────────
# MAIN FUNCTIONS
# ─────────────────────────────────────────

def check_similarity(
    competitor_id: int,
    source: str,
    url: str,
    new_text: str,
) -> tuple[float, bool]:
    """
    Compare new page text against stored embedding.
    Returns (similarity_score, is_meaningful_change).

    Flow:
    1. Generate embedding for new text
    2. Retrieve stored embedding from ChromaDB
    3. Compute cosine similarity
    4. Apply threshold filter
    5. Store new embedding (overwrites old)

    Args:
        competitor_id: ID of the competitor
        source: Data source ('website', 'careers', etc.)
        url: URL that was scraped
        new_text: Freshly scraped text

    Returns:
        Tuple of (similarity_score float, is_meaningful_change bool)
    """
    print(f"🔍 Checking similarity for competitor {competitor_id} — source: {source}")

    # Step 1 — Generate embedding for new text
    new_embedding = generate_embedding(new_text)

    # Step 2 — Retrieve stored embedding
    stored = get_stored_embedding(competitor_id, source)

    # Step 3 — First crawl ever? No comparison possible
    if stored is None:
        print(f"   📌 First crawl for {source} — storing baseline, no comparison yet")
        store_embedding(
            competitor_id=competitor_id,
            source=source,
            url=url,
            embedding=new_embedding,
            raw_text=new_text,
        )
        return 1.0, False  # 1.0 = identical to itself, not a change

    # Step 4 — Compute cosine similarity
    old_embedding = stored["embedding"]
    similarity = compute_cosine_similarity(old_embedding, new_embedding)

    # Step 5 — Apply threshold
    threshold = SOURCE_THRESHOLDS.get(source, SIMILARITY_THRESHOLD)
    is_meaningful = similarity < threshold

    # Log result
    status = "🔴 MEANINGFUL CHANGE" if is_meaningful else "✅ No significant change"
    print(f"   Similarity score : {similarity:.4f}")
    print(f"   Threshold        : {threshold}")
    print(f"   Result           : {status}")

    # Step 6 — Update stored embedding with new one
    store_embedding(
        competitor_id=competitor_id,
        source=source,
        url=url,
        embedding=new_embedding,
        raw_text=new_text,
    )

    return similarity, is_meaningful


def is_meaningful_change(
    competitor_id: int,
    source: str,
    url: str,
    new_text: str,
    old_text: str,
) -> DetectedChange | None:
    """
    Full check — returns a DetectedChange object if meaningful,
    or None if the change is trivial/not worth classifying.

    This is what Phase 3 classifier receives.

    Args:
        competitor_id: ID of the competitor
        source: Data source
        url: Scraped URL
        new_text: Freshly scraped text
        old_text: Previously stored text (from SQLite snapshot)

    Returns:
        DetectedChange object if meaningful, None if trivial
    """
    similarity, is_meaningful = check_similarity(
        competitor_id=competitor_id,
        source=source,
        url=url,
        new_text=new_text,
    )

    if not is_meaningful:
        return None

    # Build DetectedChange object for Phase 3
    change = DetectedChange(
        competitor_id=competitor_id,
        source=source,
        url=url,
        old_text=old_text,
        new_text=new_text,
        similarity_score=similarity,
        detected_at=datetime.now(timezone.utc).isoformat(),
        metadata={
            "threshold_used": SOURCE_THRESHOLDS.get(source, SIMILARITY_THRESHOLD),
            "similarity_percent": int(similarity * 100),
            "change_magnitude": _get_change_magnitude(similarity),
        }
    )

    print(f"   📦 DetectedChange created — magnitude: {change.change_magnitude()}")
    return change


def _get_change_magnitude(similarity: float) -> str:
    """Classify how big the change is based on similarity score."""
    if similarity < 0.5:
        return "MAJOR"
    elif similarity < 0.7:
        return "MODERATE"
    elif similarity < 0.85:
        return "MINOR"
    else:
        return "TRIVIAL"


def batch_check_similarities(
    competitor_id: int,
    scraped_data: list,
) -> list[DetectedChange]:
    """
    Run similarity checks for all scraped sources at once.
    Returns list of DetectedChange objects that passed the filter.

    Args:
        competitor_id: ID of the competitor
        scraped_data: List of RawScrapedData objects from Phase 1

    Returns:
        List of DetectedChange objects — only meaningful changes
    """
    detected_changes = []

    for data in scraped_data:
        try:
            # Get old text from stored snapshot for comparison
            from database import get_latest_snapshot
            old_snapshot = get_latest_snapshot(competitor_id, data.source)
            old_text = old_snapshot["raw_text"] if old_snapshot else ""

            change = is_meaningful_change(
                competitor_id=competitor_id,
                source=data.source,
                url=data.url,
                new_text=data.raw_text,
                old_text=old_text,
            )

            if change:
                detected_changes.append(change)
                print(f"   ✅ Change detected in {data.source} — passing to classifier")
            else:
                print(f"   ⏭️  No meaningful change in {data.source} — filtered out")

        except Exception as e:
            print(f"❌ Similarity check failed for {data.source}: {e}")
            continue

    return detected_changes


# ─────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────

if __name__ == "__main__":
    from database import init_db

    init_db()

    print("🧪 Testing similarity checker...\n")

    # Simulate first crawl — baseline
    print("=== CRAWL 1 — Baseline ===")
    text_v1 = "Our platform provides analytics and reporting tools for business teams."
    sim1, changed1 = check_similarity(
        competitor_id=99,
        source="website",
        url="https://test-competitor.com",
        new_text=text_v1,
    )
    print(f"First crawl result: similarity={sim1:.4f}, changed={changed1}\n")

    # Simulate second crawl — minor change
    print("=== CRAWL 2 — Minor change ===")
    text_v2 = "Our platform provides analytics and reporting tools for business teams. Now with dark mode."
    sim2, changed2 = check_similarity(
        competitor_id=99,
        source="website",
        url="https://test-competitor.com",
        new_text=text_v2,
    )
    print(f"Minor change result: similarity={sim2:.4f}, changed={changed2}\n")

    # Simulate third crawl — major change
    print("=== CRAWL 3 — Major change ===")
    text_v3 = "Our AI-powered platform provides predictive analytics, ML forecasting, and automated reporting. Trusted by 500+ enterprise customers."
    sim3, changed3 = check_similarity(
        competitor_id=99,
        source="website",
        url="https://test-competitor.com",
        new_text=text_v3,
    )
    print(f"Major change result: similarity={sim3:.4f}, changed={changed3}\n")

    # Simulate fourth crawl — no change
    print("=== CRAWL 4 — No change ===")
    sim4, changed4 = check_similarity(
        competitor_id=99,
        source="website",
        url="https://test-competitor.com",
        new_text=text_v3,  # Same text as before
    )
    print(f"No change result: similarity={sim4:.4f}, changed={changed4}\n")

    print("✅ Similarity checker test complete!")