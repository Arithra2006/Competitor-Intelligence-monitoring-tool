# Phase 4 — Scorer Package
# Aggregates evidence across all sources
# Applies weighted confidence formula
# Builds structured JSON evidence for reporter

from .reliability_weights import SOURCE_RELIABILITY
from .evidence_aggregator import aggregate_evidence
from .confidence_scorer import calculate_confidence

_all_ = [
    "SOURCE_RELIABILITY",
    "aggregate_evidence",
    "calculate_confidence",
]