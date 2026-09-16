# backend/models/signal.py
# Signal data model — represents a classified, scored intelligence signal
# Output of Phase 3, input to Phase 4 scorer

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone


# ─────────────────────────────────────────
# CHANGE TYPES
# ─────────────────────────────────────────

CHANGE_TYPES = [
    "AI positioning added",
    "New feature detected",
    "Pricing restructured",
    "Messaging shifted",
    "New market targeted",
    "Hiring surge detected",
    "Leadership change",
    "Funding signal",
    "Product launch",
    "Competitive threat",
    "Unknown change",
]

# Priority mapping — used by reporter in Phase 5
CHANGE_PRIORITY = {
    "Pricing restructured":   "HIGH",
    "AI positioning added":   "HIGH",
    "Funding signal":         "HIGH",
    "Product launch":         "HIGH",
    "New feature detected":   "MEDIUM",
    "New market targeted":    "MEDIUM",
    "Hiring surge detected":  "MEDIUM",
    "Leadership change":      "MEDIUM",
    "Messaging shifted":      "LOW",
    "Competitive threat":     "LOW",
    "Unknown change":         "LOW",
}


@dataclass
class ClassifiedSignal:
    """
    Represents a change that has been classified by Groq.
    Output of Phase 3 — input to Phase 4 scorer.
    """
    competitor_id: int
    source: str
    url: str
    change_type: str            # One of CHANGE_TYPES
    old_text: str
    new_text: str
    similarity_score: float
    raw_classification: str     # Full Groq response
    detected_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: dict = field(default_factory=dict)

    def priority(self) -> str:
        """Return priority level based on change type."""
        return CHANGE_PRIORITY.get(self.change_type, "LOW")

    def priority_emoji(self) -> str:
        """Return emoji for priority level."""
        emojis = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}
        return emojis.get(self.priority(), "🟢")

    def to_dict(self) -> dict:
        """Convert to dictionary for storage and passing between phases."""
        return {
            "competitor_id": self.competitor_id,
            "source": self.source,
            "url": self.url,
            "change_type": self.change_type,
            "old_text": self.old_text,
            "new_text": self.new_text,
            "similarity_score": self.similarity_score,
            "raw_classification": self.raw_classification,
            "detected_at": self.detected_at,
            "priority": self.priority(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ClassifiedSignal":
        """Build a ClassifiedSignal from a dictionary."""
        return cls(
            competitor_id=data.get("competitor_id"),
            source=data.get("source"),
            url=data.get("url"),
            change_type=data.get("change_type", "Unknown change"),
            old_text=data.get("old_text", ""),
            new_text=data.get("new_text", ""),
            similarity_score=data.get("similarity_score", 1.0),
            raw_classification=data.get("raw_classification", ""),
            detected_at=data.get("detected_at"),
            metadata=data.get("metadata", {}),
        )

    def __repr__(self):
        return (
            f"ClassifiedSignal("
            f"competitor_id={self.competitor_id}, "
            f"source='{self.source}', "
            f"change_type='{self.change_type}', "
            f"priority='{self.priority()}'"
            f")"
        )


@dataclass
class ScoredSignal:
    """
    Represents a classified signal after confidence scoring.
    Output of Phase 4 scorer — input to Phase 5 reporter.
    """
    competitor_id: int
    signal_type: str
    confidence: float           # 0.0 to 100.0
    evidence: list              # List of evidence dicts
    change_type: str
    priority: str
    detected_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: dict = field(default_factory=dict)

    def confidence_label(self) -> str:
        """Human readable confidence label."""
        if self.confidence >= 80:
            return "HIGH"
        elif self.confidence >= 60:
            return "MEDIUM"
        else:
            return "LOW"

    def priority_emoji(self) -> str:
        """Return emoji for priority level."""
        emojis = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}
        return emojis.get(self.priority, "🟢")

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "competitor_id": self.competitor_id,
            "signal_type": self.signal_type,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "change_type": self.change_type,
            "priority": self.priority,
            "confidence_label": self.confidence_label(),
            "detected_at": self.detected_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ScoredSignal":
        """Build a ScoredSignal from a dictionary."""
        return cls(
            competitor_id=data.get("competitor_id"),
            signal_type=data.get("signal_type", ""),
            confidence=data.get("confidence", 0.0),
            evidence=data.get("evidence", []),
            change_type=data.get("change_type", "Unknown change"),
            priority=data.get("priority", "LOW"),
            detected_at=data.get("detected_at"),
            metadata=data.get("metadata", {}),
        )

    def __repr__(self):
        return (
            f"ScoredSignal("
            f"competitor_id={self.competitor_id}, "
            f"signal_type='{self.signal_type}', "
            f"confidence={self.confidence:.1f}%, "
            f"priority='{self.priority}'"
            f")"
        )