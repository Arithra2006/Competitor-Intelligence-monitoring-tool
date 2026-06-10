# backend/models/snapshot.py
# Snapshot and DetectedChange data models
# Used across Phase 2, 3, and 4

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone


@dataclass
class Snapshot:
    """
    Represents a full page snapshot stored after every crawl.
    Contains raw text, embedding, and change metadata.
    """
    competitor_id: int
    source: str          # 'website', 'careers', 'news', 'github', 'reddit'
    url: str
    raw_text: str
    embedding: Optional[list] = None
    change_type: Optional[str] = None
    confidence: Optional[int] = None
    id: Optional[int] = None
    crawled_at: Optional[str] = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict:
        """Convert to dictionary for database storage."""
        return {
            "id": self.id,
            "competitor_id": self.competitor_id,
            "source": self.source,
            "url": self.url,
            "raw_text": self.raw_text,
            "embedding": self.embedding,
            "change_type": self.change_type,
            "confidence": self.confidence,
            "crawled_at": self.crawled_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Snapshot":
        """Build a Snapshot object from a database row dict."""
        return cls(
            id=data.get("id"),
            competitor_id=data.get("competitor_id"),
            source=data.get("source"),
            url=data.get("url"),
            raw_text=data.get("raw_text", ""),
            embedding=data.get("embedding"),
            change_type=data.get("change_type"),
            confidence=data.get("confidence"),
            crawled_at=data.get("crawled_at"),
        )

    def _repr_(self):
        return (
            f"Snapshot("
            f"id={self.id}, "
            f"competitor_id={self.competitor_id}, "
            f"source='{self.source}', "
            f"change_type='{self.change_type}'"
            f")"
        )


@dataclass
class DetectedChange:
    """
    Represents a meaningful change detected by Phase 2.
    Output of the detector — input to the classifier (Phase 3).
    """
    competitor_id: int
    source: str
    url: str
    old_text: str
    new_text: str
    similarity_score: float      # 0.0 to 1.0 — lower = more different
    detected_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    change_type: Optional[str] = None        # Filled by Phase 3 classifier
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "competitor_id": self.competitor_id,
            "source": self.source,
            "url": self.url,
            "old_text": self.old_text,
            "new_text": self.new_text,
            "similarity_score": self.similarity_score,
            "detected_at": self.detected_at,
            "change_type": self.change_type,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DetectedChange":
        """Build a DetectedChange object from a dict."""
        return cls(
            competitor_id=data.get("competitor_id"),
            source=data.get("source"),
            url=data.get("url"),
            old_text=data.get("old_text", ""),
            new_text=data.get("new_text", ""),
            similarity_score=data.get("similarity_score", 1.0),
            detected_at=data.get("detected_at"),
            change_type=data.get("change_type"),
            metadata=data.get("metadata", {}),
        )

    def similarity_percent(self) -> int:
        """Return similarity as a percentage."""
        return int(self.similarity_score * 100)

    def change_magnitude(self) -> str:
        """
        Describe how significant the change is
        based on similarity score.
        """
        if self.similarity_score < 0.5:
            return "MAJOR"
        elif self.similarity_score < 0.7:
            return "MODERATE"
        elif self.similarity_score < 0.85:
            return "MINOR"
        else:
            return "TRIVIAL"

    def _repr_(self):
        return (
            f"DetectedChange("
            f"competitor_id={self.competitor_id}, "
            f"source='{self.source}', "
            f"similarity={self.similarity_score:.2f}, "
            f"magnitude='{self.change_magnitude()}'"
            f")"
        )