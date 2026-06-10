# backend/models/battlecard.py
# Battlecard data model
# Represents a competitive battlecard for one competitor

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone


@dataclass
class Battlecard:
    """
    Represents a competitive battlecard.
    Generated from intelligence signals using Groq.
    Used by sales teams to win deals against this competitor.
    """
    competitor_id: int
    competitor_name: str
    our_company: str

    # Core battlecard sections
    our_strengths: list = field(default_factory=list)
    our_weaknesses: list = field(default_factory=list)
    their_strengths: list = field(default_factory=list)
    their_weaknesses: list = field(default_factory=list)
    recent_moves: list = field(default_factory=list)
    how_to_win: list = field(default_factory=list)
    watch_out_for: list = field(default_factory=list)
    key_differentiators: list = field(default_factory=list)

    # Metadata
    confidence_score: float = 0.0
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    last_updated: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    raw_battlecard: str = ""
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for storage and API response."""
        return {
            "competitor_id": self.competitor_id,
            "competitor_name": self.competitor_name,
            "our_company": self.our_company,
            "our_strengths": self.our_strengths,
            "our_weaknesses": self.our_weaknesses,
            "their_strengths": self.their_strengths,
            "their_weaknesses": self.their_weaknesses,
            "recent_moves": self.recent_moves,
            "how_to_win": self.how_to_win,
            "watch_out_for": self.watch_out_for,
            "key_differentiators": self.key_differentiators,
            "confidence_score": self.confidence_score,
            "generated_at": self.generated_at,
            "last_updated": self.last_updated,
            "raw_battlecard": self.raw_battlecard,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Battlecard":
        """Build a Battlecard from a dictionary."""
        return cls(
            competitor_id=data.get("competitor_id", 0),
            competitor_name=data.get("competitor_name", ""),
            our_company=data.get("our_company", ""),
            our_strengths=data.get("our_strengths", []),
            our_weaknesses=data.get("our_weaknesses", []),
            their_strengths=data.get("their_strengths", []),
            their_weaknesses=data.get("their_weaknesses", []),
            recent_moves=data.get("recent_moves", []),
            how_to_win=data.get("how_to_win", []),
            watch_out_for=data.get("watch_out_for", []),
            key_differentiators=data.get("key_differentiators", []),
            confidence_score=data.get("confidence_score", 0.0),
            generated_at=data.get("generated_at", ""),
            last_updated=data.get("last_updated", ""),
            raw_battlecard=data.get("raw_battlecard", ""),
            metadata=data.get("metadata", {}),
        )

    def format_text(self) -> str:
        """Format battlecard as clean readable text."""
        now = datetime.now(timezone.utc).strftime("%B %Y")
        lines = []

        lines.append("=" * 60)
        lines.append(f"BATTLECARD — COMPETING AGAINST: {self.competitor_name.upper()}")
        lines.append(f"Your Company: {self.our_company}")
        lines.append(f"Last Updated: {now}")
        lines.append(f"Confidence: {self.confidence_score:.0f}%")
        lines.append("=" * 60)

        if self.recent_moves:
            lines.append("\n🔴 THEIR RECENT MOVES")
            for move in self.recent_moves:
                lines.append(f"  • {move}")

        if self.our_strengths:
            lines.append("\n✅ OUR STRENGTHS vs THEM")
            for s in self.our_strengths:
                lines.append(f"  • {s}")

        if self.their_weaknesses:
            lines.append("\n⚠️  THEIR WEAKNESSES")
            for w in self.their_weaknesses:
                lines.append(f"  • {w}")

        if self.how_to_win:
            lines.append("\n🏆 HOW TO WIN")
            for tip in self.how_to_win:
                lines.append(f"  • {tip}")

        if self.watch_out_for:
            lines.append("\n👀 WATCH OUT FOR")
            for w in self.watch_out_for:
                lines.append(f"  • {w}")

        if self.key_differentiators:
            lines.append("\n💡 KEY DIFFERENTIATORS")
            for d in self.key_differentiators:
                lines.append(f"  • {d}")

        lines.append("\n" + "=" * 60)
        return "\n".join(lines)

    def __repr__(self):
        return (
            f"Battlecard("
            f"competitor='{self.competitor_name}', "
            f"confidence={self.confidence_score:.0f}%"
            f")"
        )