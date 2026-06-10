# backend/phase4_scorer/weight_adjuster.py
# Automatically adjusts source reliability weights based on user feedback
# Called after every feedback submission
# Makes the intelligence system smarter over time

import sys
import os
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_feedback_stats_by_source, get_adjusted_weights, save_adjusted_weight
from reliability_weights import SOURCE_RELIABILITY


# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────

# Minimum feedback needed before adjusting weights
MIN_FEEDBACK_TO_ADJUST = 3

# How much to adjust per threshold breach
PENALTY_AMOUNT  = 0.1   # Lower weight for irrelevant signals
REWARD_AMOUNT   = 0.05  # Raise weight for useful signals

# Hard limits — never go outside these bounds
MIN_WEIGHT = 0.2
MAX_WEIGHT = 1.0

# Irrelevant ratio that triggers penalty
IRRELEVANT_THRESHOLD = 0.6   # 60%+ irrelevant → lower weight

# Useful ratio that triggers reward
USEFUL_THRESHOLD = 0.7       # 70%+ useful → raise weight


# ─────────────────────────────────────────
# MAIN FUNCTION
# ─────────────────────────────────────────

def adjust_weights_from_feedback() -> dict:
    """
    Analyze feedback patterns and adjust source reliability weights.
    Called after every feedback submission.

    Returns:
        Dict of adjusted weights with reasoning
    """
    print("\n🔧 Running weight adjuster...")

    # Get feedback stats per source
    stats = get_feedback_stats_by_source()

    if not stats:
        print("   No feedback data yet — weights unchanged")
        return {}

    # Get current weights (adjusted or defaults)
    current_weights = _get_current_weights()

    adjustments = {}

    for source, feedback_counts in stats.items():
        total      = feedback_counts.get("total", 0)
        useful     = feedback_counts.get("useful", 0)
        irrelevant = feedback_counts.get("irrelevant", 0)

        # Skip if not enough feedback
        if total < MIN_FEEDBACK_TO_ADJUST:
            print(f"   ⏭️  {source}: only {total} feedback(s) — need {MIN_FEEDBACK_TO_ADJUST} to adjust")
            continue

        current_weight = current_weights.get(source, SOURCE_RELIABILITY.get(source, 0.5))
        new_weight     = current_weight
        reason         = ""

        irrelevant_ratio = irrelevant / total if total > 0 else 0
        useful_ratio     = useful / total if total > 0 else 0

        # Apply penalty if too many irrelevant
        if irrelevant_ratio >= IRRELEVANT_THRESHOLD:
            new_weight = max(MIN_WEIGHT, current_weight - PENALTY_AMOUNT)
            reason = f"⬇️  Penalized — {irrelevant_ratio:.0%} irrelevant signals"

        # Apply reward if mostly useful
        elif useful_ratio >= USEFUL_THRESHOLD:
            new_weight = min(MAX_WEIGHT, current_weight + REWARD_AMOUNT)
            reason = f"⬆️  Rewarded — {useful_ratio:.0%} useful signals"

        else:
            reason = f"➡️  No change — mixed feedback ({useful} useful, {irrelevant} irrelevant)"

        # Save if changed
        if new_weight != current_weight:
            save_adjusted_weight(source, new_weight)
            print(f"   {source:<10}: {current_weight:.2f} → {new_weight:.2f} | {reason}")
        else:
            print(f"   {source:<10}: {current_weight:.2f} (unchanged) | {reason}")

        adjustments[source] = {
            "old_weight":       current_weight,
            "new_weight":       new_weight,
            "useful":           useful,
            "irrelevant":       irrelevant,
            "total":            total,
            "useful_ratio":     round(useful_ratio, 2),
            "irrelevant_ratio": round(irrelevant_ratio, 2),
            "reason":           reason,
        }

    print("✅ Weight adjustment complete\n")
    return adjustments


def get_current_weights() -> dict:
    """
    Get current effective weights for all sources.
    Returns adjusted weights where available, defaults otherwise.
    Public function for use by scorer.
    """
    return _get_current_weights()


def _get_current_weights() -> dict:
    """
    Internal — merge default weights with any saved adjustments.
    Adjusted weights override defaults.
    """
    # Start with defaults
    weights = dict(SOURCE_RELIABILITY)

    # Override with any saved adjustments
    adjusted = get_adjusted_weights()
    weights.update(adjusted)

    return weights


def reset_weights() -> None:
    """
    Reset all weights back to defaults.
    Useful for testing or if adjustments go wrong.
    """
    from database import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM source_weights")
    conn.commit()
    conn.close()
    print("✅ All weights reset to defaults")


# ─────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────

if __name__ == "__main__":
    from database import init_db

    init_db()

    print("🧪 Testing weight adjuster...\n")

    # Show current weights
    print("Current weights:")
    weights = get_current_weights()
    for source, weight in weights.items():
        default = SOURCE_RELIABILITY.get(source, 0.5)
        status = "adjusted" if weight != default else "default"
        print(f"   {source:<10}: {weight:.2f} ({status})")

    # Run adjustment
    print("\nRunning adjustment based on feedback...")
    adjustments = adjust_weights_from_feedback()

    if adjustments:
        print("\nAdjustments made:")
        for source, adj in adjustments.items():
            print(f"   {source}: {adj['old_weight']:.2f} → {adj['new_weight']:.2f}")
            print(f"   Reason: {adj['reason']}")
    else:
        print("No adjustments made yet — need more feedback data")

    print("\n✅ Weight adjuster test complete!")