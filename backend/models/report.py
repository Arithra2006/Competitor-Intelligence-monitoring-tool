# backend/models/report.py
# Report data model — represents a full weekly intelligence briefing
# Output of Phase 5 reporter — input to Phase 6 delivery

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone


@dataclass
class IntelligenceReport:
    """
    Represents a complete weekly intelligence briefing
    for one competitor. Output of Phase 5 reporter.
    """
    competitor_id: int
    competitor_name: str
    report_text: str                    # Full formatted briefing text
    high_priority: list = field(default_factory=list)    # 🔴 signals
    medium_priority: list = field(default_factory=list)  # 🟡 signals
    low_priority: list = field(default_factory=list)     # 🟢 signals
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    week_of: str = field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%B %Y")
    )
    metadata: dict = field(default_factory=dict)

    def total_signals(self) -> int:
        """Total number of signals in this report."""
        return (
            len(self.high_priority) +
            len(self.medium_priority) +
            len(self.low_priority)
        )

    def has_high_priority(self) -> bool:
        """True if report contains any high priority signals."""
        return len(self.high_priority) > 0

    def priority_summary(self) -> str:
        """One line summary of signal counts by priority."""
        return (
            f"🔴 {len(self.high_priority)} HIGH | "
            f"🟡 {len(self.medium_priority)} MEDIUM | "
            f"🟢 {len(self.low_priority)} LOW"
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for database storage."""
        return {
            "competitor_id": self.competitor_id,
            "competitor_name": self.competitor_name,
            "report_text": self.report_text,
            "high_priority": self.high_priority,
            "medium_priority": self.medium_priority,
            "low_priority": self.low_priority,
            "total_signals": self.total_signals(),
            "generated_at": self.generated_at,
            "week_of": self.week_of,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "IntelligenceReport":
        """Build an IntelligenceReport from a dictionary."""
        return cls(
            competitor_id=data.get("competitor_id"),
            competitor_name=data.get("competitor_name", ""),
            report_text=data.get("report_text", ""),
            high_priority=data.get("high_priority", []),
            medium_priority=data.get("medium_priority", []),
            low_priority=data.get("low_priority", []),
            generated_at=data.get("generated_at"),
            week_of=data.get("week_of", ""),
            metadata=data.get("metadata", {}),
        )

    def _repr_(self):
        return (
            f"IntelligenceReport("
            f"competitor='{self.competitor_name}', "
            f"signals={self.total_signals()}, "
            f"week='{self.week_of}'"
            f")"
        )