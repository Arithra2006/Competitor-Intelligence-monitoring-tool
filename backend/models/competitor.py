# backend/models/competitor.py
# Competitor data model — used across all phases
# Defines the structure of a competitor object

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class Competitor:
    """
    Represents a competitor being tracked.
    This is the core data object passed through the pipeline.
    """
    name: str
    website_url: str
    careers_url: Optional[str] = None
    github_org: Optional[str] = None
    reddit_keyword: Optional[str] = None
    frequency: str = "weekly"
    id: Optional[int] = None
    created_at: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for database storage."""
        return {
            "id": self.id,
            "name": self.name,
            "website_url": self.website_url,
            "careers_url": self.careers_url,
            "github_org": self.github_org,
            "reddit_keyword": self.reddit_keyword,
            "frequency": self.frequency,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Competitor":
        """Build a Competitor object from a database row dict."""
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            website_url=data.get("website_url"),
            careers_url=data.get("careers_url"),
            github_org=data.get("github_org"),
            reddit_keyword=data.get("reddit_keyword"),
            frequency=data.get("frequency", "weekly"),
            created_at=data.get("created_at"),
        )

    def __repr__(self):
        return (
            f"Competitor("
            f"id={self.id}, "
            f"name='{self.name}', "
            f"website='{self.website_url}'"
            f")"
        )


@dataclass
class RawScrapedData:
    """
    Represents raw data collected from one source
    during a single crawl. Output of Phase 1.
    """
    competitor_id: int
    source: str          # 'website', 'careers', 'news', 'github', 'reddit'
    url: str
    raw_text: str
    scraped_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for database storage."""
        return {
            "competitor_id": self.competitor_id,
            "source": self.source,
            "url": self.url,
            "raw_text": self.raw_text,
            "scraped_at": self.scraped_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RawScrapedData":
        """Build a RawScrapedData object from a dict."""
        return cls(
            competitor_id=data.get("competitor_id"),
            source=data.get("source"),
            url=data.get("url"),
            raw_text=data.get("raw_text", ""),
            scraped_at=data.get("scraped_at", datetime.utcnow().isoformat()),
            metadata=data.get("metadata", {}),
        )

    def __repr__(self):
        return (
            f"RawScrapedData("
            f"competitor_id={self.competitor_id}, "
            f"source='{self.source}', "
            f"url='{self.url}', "
            f"text_length={len(self.raw_text)}"
            f")"
        )