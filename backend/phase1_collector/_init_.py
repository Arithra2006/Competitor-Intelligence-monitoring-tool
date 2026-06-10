# Phase 1 — Collector Package
# This file makes phase1_collector a Python package
# and exposes the main collect_all() function

from .website_scraper import scrape_website
from .careers_scraper import scrape_careers
from .news_parser import parse_news
from .github_client import get_github_signals
from .reddit_client import get_reddit_signals

_all_ = [
    "scrape_website",
    "scrape_careers",
    "parse_news",
    "get_github_signals",
    "get_reddit_signals",
]