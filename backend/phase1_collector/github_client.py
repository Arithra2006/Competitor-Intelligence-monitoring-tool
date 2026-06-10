# backend/phase1_collector/github_client.py
# Fetches public GitHub activity for a competitor's organization
# Uses GitHub public API — no API key required for basic use
# With GITHUB_TOKEN in .env — higher rate limits (5000 req/hour vs 60)

import requests
from datetime import datetime, timezone
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import insert_snapshot
from models.competitor import RawScrapedData


# ─────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────

GITHUB_API_BASE = "https://api.github.com"
MAX_REPOS = 10        # Top 10 most active repos
MAX_COMMITS = 20      # Last 20 commits per org

# AI/ML related keywords in commit messages and repo names
AI_COMMIT_KEYWORDS = [
    "ai", "ml", "llm", "gpt", "embedding", "vector", "neural",
    "model", "inference", "fine-tune", "rag", "agent", "prompt"
]

# Load GitHub token from environment if available
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


# ─────────────────────────────────────────
# MAIN CLIENT FUNCTION
# ─────────────────────────────────────────

def get_github_signals(competitor_id: int, github_org: str) -> RawScrapedData | None:
    """
    Fetch public GitHub activity for a competitor organization.
    Detects: commit frequency, AI-related work, new repos, activity trends.

    Args:
        competitor_id: ID of the competitor in the database
        github_org: GitHub organization name e.g. 'notionhq'

    Returns:
        RawScrapedData object with GitHub signals, or None on failure
    """
    print(f"🐙 Fetching GitHub signals for org: {github_org}")

    headers = _build_headers()
    repos, repo_metadata = _fetch_repos(github_org, headers)

    if not repos:
        print(f"⚠️  No public repos found for {github_org} — skipping.")
        return None

    commits, commit_metadata = _fetch_recent_commits(github_org, repos, headers)
    raw_text = _build_raw_text(github_org, repos, commits)
    metadata = {**repo_metadata, **commit_metadata, "github_org": github_org}

    # Save snapshot to SQLite
    url = f"https://github.com/{github_org}"
    insert_snapshot(
        competitor_id=competitor_id,
        source="github",
        url=url,
        raw_text=raw_text,
    )

    print(f"✅ GitHub signals fetched — {len(repos)} repos, {len(commits)} commits for {github_org}")

    return RawScrapedData(
        competitor_id=competitor_id,
        source="github",
        url=url,
        raw_text=raw_text,
        metadata=metadata,
    )


# ─────────────────────────────────────────
# INTERNAL HELPERS
# ─────────────────────────────────────────

def _build_headers() -> dict:
    """Build request headers. Use token if available for higher rate limits."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "CompetitorIntelligenceBot/1.0",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
        print("   🔑 Using GitHub token — higher rate limits active")
    else:
        print("   ⚠️  No GitHub token — limited to 60 requests/hour")
    return headers


def _fetch_repos(github_org: str, headers: dict) -> tuple:
    """
    Fetch public repositories for the organization.
    Sorted by most recently pushed — most active repos first.
    """
    try:
        url = f"{GITHUB_API_BASE}/orgs/{github_org}/repos"
        params = {
            "type": "public",
            "sort": "pushed",
            "direction": "desc",
            "per_page": MAX_REPOS,
        }
        response = requests.get(url, headers=headers, params=params, timeout=15)

        if response.status_code == 404:
            print(f"   ❌ GitHub org '{github_org}' not found")
            return [], {}

        if response.status_code == 403:
            print(f"   ❌ GitHub rate limit hit — add GITHUB_TOKEN to .env")
            return [], {}

        response.raise_for_status()
        repos = response.json()

        if not isinstance(repos, list):
            return [], {}

        repo_data = []
        total_stars = 0
        total_forks = 0

        for repo in repos[:MAX_REPOS]:
            repo_data.append({
                "name": repo.get("name", ""),
                "description": repo.get("description", "") or "",
                "stars": repo.get("stargazers_count", 0),
                "forks": repo.get("forks_count", 0),
                "language": repo.get("language", ""),
                "pushed_at": repo.get("pushed_at", ""),
                "topics": repo.get("topics", []),
            })
            total_stars += repo.get("stargazers_count", 0)
            total_forks += repo.get("forks_count", 0)

        # Detect AI repos by name, description, topics
        ai_repos = [
            r for r in repo_data
            if any(kw in (r["name"] + " " + r["description"]).lower()
                   for kw in AI_COMMIT_KEYWORDS)
        ]

        metadata = {
            "repo_count": len(repo_data),
            "total_stars": total_stars,
            "total_forks": total_forks,
            "ai_repos": [r["name"] for r in ai_repos],
            "ai_repo_detected": len(ai_repos) > 0,
            "repos": repo_data,
        }

        if ai_repos:
            print(f"   🤖 AI-related repos detected: {[r['name'] for r in ai_repos]}")

        return repo_data, metadata

    except Exception as e:
        print(f"❌ Error fetching repos for {github_org}: {e}")
        return [], {}


def _fetch_recent_commits(github_org: str, repos: list, headers: dict) -> tuple:
    """
    Fetch recent commits from the most active repos.
    Analyzes commit messages for AI/feature signals.
    """
    all_commits = []

    # Only check top 3 repos to stay within rate limits
    for repo in repos[:3]:
        repo_name = repo.get("name", "")
        try:
            url = f"{GITHUB_API_BASE}/repos/{github_org}/{repo_name}/commits"
            params = {"per_page": 10}
            response = requests.get(url, headers=headers, params=params, timeout=15)

            if response.status_code != 200:
                continue

            commits = response.json()
            if not isinstance(commits, list):
                continue

            for commit in commits:
                message = commit.get("commit", {}).get("message", "")
                author = commit.get("commit", {}).get("author", {})
                all_commits.append({
                    "repo": repo_name,
                    "message": message[:200],   # Cap length
                    "author": author.get("name", ""),
                    "date": author.get("date", ""),
                })

        except Exception as e:
            print(f"   ⚠️  Could not fetch commits for {repo_name}: {e}")
            continue

    # Analyze commit messages
    all_messages = " ".join([c["message"] for c in all_commits]).lower()
    ai_commits = [
        c for c in all_commits
        if any(kw in c["message"].lower() for kw in AI_COMMIT_KEYWORDS)
    ]

    # Calculate commit frequency — commits in last 7 days
    recent_commits = _count_recent_commits(all_commits, days=7)

    metadata = {
        "total_commits_fetched": len(all_commits),
        "ai_commit_count": len(ai_commits),
        "ai_commits_detected": len(ai_commits) > 0,
        "recent_commits_7d": recent_commits,
        "commits": all_commits[:MAX_COMMITS],
    }

    if ai_commits:
        print(f"   🤖 AI-related commits detected: {len(ai_commits)}")
    print(f"   📊 Commits in last 7 days: {recent_commits}")

    return all_commits, metadata


def _count_recent_commits(commits: list, days: int = 7) -> int:
    """Count commits made within the last N days."""
    now = datetime.now(timezone.utc)
    count = 0
    for commit in commits:
        date_str = commit.get("date", "")
        if not date_str:
            continue
        try:
            commit_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            delta = now - commit_date
            if delta.days <= days:
                count += 1
        except Exception:
            continue
    return count


def _build_raw_text(github_org: str, repos: list, commits: list) -> str:
    """
    Build a single text block from repos + commits.
    This is what gets embedded and compared in Phase 2.
    """
    parts = [f"GitHub Organization: {github_org}\n"]

    parts.append("=== REPOSITORIES ===")
    for repo in repos:
        parts.append(
            f"Repo: {repo['name']} | "
            f"Stars: {repo['stars']} | "
            f"Language: {repo['language']} | "
            f"Description: {repo['description']} | "
            f"Last pushed: {repo['pushed_at']}"
        )

    parts.append("\n=== RECENT COMMITS ===")
    for commit in commits[:MAX_COMMITS]:
        parts.append(
            f"[{commit['repo']}] {commit['date'][:10]} — {commit['message'][:100]}"
        )

    return "\n".join(parts)


# ─────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────

if __name__ == "__main__":
    from database import init_db

    init_db()

    if len(sys.argv) == 3:
        comp_id = int(sys.argv[1])
        github_org = sys.argv[2]
    else:
        comp_id = 1
        github_org = "notionhq"

    result = get_github_signals(comp_id, github_org)

    if result:
        print("\n--- RESULT ---")
        print(f"Source      : {result.source}")
        print(f"Chars       : {len(result.raw_text)}")
        print(f"Repos       : {result.metadata.get('repo_count', 0)}")
        print(f"AI Repos    : {result.metadata.get('ai_repos', [])}")
        print(f"AI Commits  : {result.metadata.get('ai_commit_count', 0)}")
        print(f"7d Commits  : {result.metadata.get('recent_commits_7d', 0)}")
        print(f"\nPreview:\n{result.raw_text[:400]}...")
    else:
        print("❌ GitHub fetch failed.")