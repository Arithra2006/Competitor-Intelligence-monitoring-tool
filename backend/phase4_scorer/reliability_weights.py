# backend/phase4_scorer/reliability_weights.py
# Source reliability weights used across Phase 3 and Phase 4
# These are starting defaults — adjust based on real data over time

SOURCE_RELIABILITY = {
    "website": 0.9,   # Direct source — highest reliability
    "careers": 0.8,   # Job postings — very reliable signal
    "github":  0.8,   # Public commits — very reliable signal
    "news":    0.7,   # Third party — good but not primary
    "reddit":  0.5,   # Community discussion — lowest reliability
}

# Signal strength weights by change type
CHANGE_TYPE_STRENGTH = {
    "Pricing restructured":   0.95,
    "AI positioning added":   0.90,
    "Funding signal":         0.90,
    "Product launch":         0.90,
    "New feature detected":   0.80,
    "New market targeted":    0.80,
    "Hiring surge detected":  0.75,
    "Leadership change":      0.75,
    "Messaging shifted":      0.65,
    "Competitive threat":     0.65,
    "Unknown change":         0.40,
}

# Minimum confidence threshold to include in report
MIN_CONFIDENCE_THRESHOLD = 50.0