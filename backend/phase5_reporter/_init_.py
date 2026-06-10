# Phase 5 — Reporter Package
# Generates analyst-style weekly briefings using Groq
# Adds "Why it matters" section to every signal
# Formats reports with priority levels

from .briefing_generator import generate_briefing
from .why_it_matters import generate_why_it_matters
from .report_formatter import format_report

_all_ = [
    "generate_briefing",
    "generate_why_it_matters",
    "format_report",
]