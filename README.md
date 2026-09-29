# 🕵️ Competitor Intelligence Agent

> Your always-on AI analyst that detects what competitors are doing, why it matters, and how confident we are — before you even ask.

![Tech Stack](https://img.shields.io/badge/Stack-FastAPI%20%7C%20Next.js%20%7C%20Groq-blue)
![Cost](https://img.shields.io/badge/Monthly%20Cost-%240-green)
![Python](https://img.shields.io/badge/Python-3.13-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 📌 Overview

An autonomous pipeline system that monitors competitors across the web, detects meaningful changes using semantic analysis, scores intelligence with weighted confidence levels, and delivers analyst-quality briefings — automatically, every week.
The problem it solves:
Hiring a market analyst costs $60k–$100k/year
Tools like Crayon and Klue cost $15k–$40k/year, enterprise-only
Manual tracking is inconsistent and time-consuming
Small teams skip it entirely — and get blindsided
This pipeline does it autonomously, at zero ongoing cost.

✨ Features
🔍 Collector
Monitors these free sources per competitor:
Company website — Playwright + BeautifulSoup
Careers page — detects hiring surges and expansion signals, using link-structure analysis (not just keyword matching) so job counts stay accurate across different careers page platforms (Greenhouse, Lever, Ashby, custom-built pages)
Google News RSS — leadership, funding, product signals, filtered with exact-phrase + context-keyword search and a post-fetch relevancy check so a competitor named after a common word (e.g. "Notion," "Linear") doesn't pull in unrelated articles
GitHub public API — commit frequency, AI-related repos (org names are auto-cleaned if a full URL is pasted instead of just the org name)
🧠 Detector (Core Intelligence)
Not just detecting that something changed — detecting what kind of change happened and why it matters.
Scrape page
↓
Generate embedding (Sentence Transformers)
↓
Compute cosine similarity vs stored embedding
↓
if similarity < threshold ← FILTER: ignore trivial changes
↓
Groq classify_change() ← Only meaningful changes reach Groq
↓
Store full page snapshot + structured JSON evidence
The classifier compares the actual differing sections of old vs. new content (not just the first N characters), so real changes further down a page aren't missed or misclassified.
📊 Weighted Confidence Scoring
Every insight is scored using a weighted formula combining source agreement, source reliability, and signal strength.
📈 Temporal Trend Analysis
Tracks signals over time — not just point-in-time snapshots.
📝 Reporter with "Why It Matters"
Powered by Groq API — generates analyst-style briefings with:
Priority classification (🔴 HIGH / 🟡 MEDIUM / 🟢 LOW)
Evidence trail for every signal
Source excerpts — when a signal comes from news or GitHub, the report quotes the actual matching article (title, summary, publication, link) or commit (repo, message, date), instead of only a short AI-paraphrased line
Forward-looking "Why it matters" section
Watch for predictions with timeframes
🃏 Sales Battlecards
Auto-generated competitive battlecards — what Crayon charges $15k/year for:
Our strengths vs competitor
Their weaknesses to exploit
How to win talking points
Watch out for alerts
👍 Human Feedback Loop
Users rate signals as Useful or Irrelevant — system automatically adjusts source reliability weights over time.
📋 Pipeline Activity Log
Every step of a pipeline run — scraping, similarity checks, classification, scoring, reporting, delivery — is now saved to the database and viewable in a dedicated Activity page on the dashboard, not just printed to a terminal you have to be watching live.
🖥️ Dashboard
Clean Next.js + Tailwind UI:
Add / remove competitors
View current and past reports
Change history timeline
Trend graphs (Recharts)
Evidence cards
Sales battlecards
Signal feedback buttons
Pipeline activity log (new)
⏰ Scheduler
APScheduler triggers full pipeline automatically:
Daily competitors run every day
Weekly competitors run every Monday
Monthly competitors run on 1st of month
🏗️ Architecture
User Input (competitors list)
↓
[ Scheduler ] ← APScheduler triggers based on frequency
↓
[ Collector ] ← Playwright, BS4, RSS, GitHub API
↓
[ Detector ] ← Sentence Transformers + ChromaDB cosine diff
↓
[ Threshold Filter ] ← Only meaningful changes pass forward
↓
[ Classifier ] ← Groq classify_change() (diff-aware prompt)
↓
[ Snapshot Store ] ← Full page snapshot saved to SQLite
↓
[ Scorer ] ← Weighted confidence formula
↓
[ Reporter ] ← Groq writes briefing + "Why it matters" + source excerpts
↓
Email / Slack / Dashboard
↑
Human Feedback Loop → Weight Adjuster

Every phase also writes to → [ Pipeline Activity Log ] → visible on dashboard
🛠️ Tech Stack — $0/month
Layer
Tool
Cost
Web Scraping
Playwright + BeautifulSoup
✅ Free
News Collection
Google News RSS
✅ Free
Developer Signal
GitHub public API
✅ Free
LLM
Groq API (cloud)
✅ Free tier
Embeddings
Sentence Transformers (local)
✅ Free
Vector Storage
ChromaDB (local)
✅ Free
Database
SQLite
✅ Free
Scheduler
APScheduler
✅ Free
Email
Resend free tier
✅ Free
Backend
FastAPI
✅ Free
Frontend
Next.js + Tailwind
✅ Free
Charts
Recharts
✅ Free
Total monthly cost: $0
🚀 Getting Started
Prerequisites
Python 3.13+
Node.js 18+
Git
1. Clone the repository
git clone https://github.com/yourusername/competitor-intelligence.git
cd competitor-intelligence
2. Set up environment variables
cp .env.example .env
Fill in your .env:
GROQ_API_KEY=your_groq_key
GITHUB_TOKEN=your_github_token (optional)
RESEND_API_KEY=your_resend_key
REPORT_EMAIL_TO=your@email.com
REPORT_EMAIL_FROM=onboarding@resend.dev
SLACK_WEBHOOK_URL=your_slack_webhook (optional)
YOUR_COMPANY_NAME=YourCompany
YOUR_COMPANY_STRENGTHS=Your strengths here
YOUR_COMPANY_WEAKNESSES=Your weaknesses here
Note on Groq models: Groq periodically retires and adds models. If you hit a model not found error, check console.groq.com for currently available models on your plan and update CLASSIFIER_MODEL / REPORTER_MODEL in backend/phase3_classifier/groq_client.py accordingly.
3. Install backend dependencies
cd backend
pip install -r requirements.txt
playwright install chromium
4. Install frontend dependencies
cd frontend
npm install
5. Run the project
Terminal 1 — Backend:
cd backend
uvicorn main:app --reload --port 8000
Terminal 2 — Frontend:
cd frontend
npm run dev
Terminal 3 — Scheduler (optional):
cd backend
python scheduler.py --mode daily
Open http://localhost:3000
📅 Pipeline Phases
Phase
Component
Description
1
Collector
Scrapes all sources, stores raw data
2
Detector
Embeddings + cosine similarity + threshold filter
3
Classifier
Groq classifies change type (diff-aware)
4
Scorer
Weighted confidence formula
5
Reporter
Groq writes analyst briefing + source excerpts
6
Delivery
Email + Slack delivery
7
Dashboard
Next.js frontend, incl. Activity Log
8
Scheduler
APScheduler weekly automation
📁 Project Structure
competitor-intelligence/
│
├── backend/
│   ├── main.py                  ← FastAPI entry point
│   ├── scheduler.py             ← APScheduler
│   ├── database.py              ← SQLite setup (incl. pipeline_logs table)
│   │
│   ├── phase1_collector/        ← Web scrapers
│   ├── phase2_detector/         ← Embeddings + similarity
│   ├── phase3_classifier/       ← Groq classifier
│   ├── phase4_scorer/           ← Confidence scoring
│   ├── phase5_reporter/         ← Report + battlecard generator
│   ├── phase6_delivery/         ← Email + Slack
│   └── models/                  ← Data models
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx             ← Dashboard
│   │   ├── competitors/         ← Manage competitors
│   │   ├── reports/             ← View reports
│   │   ├── trends/              ← Trend graphs + feedback
│   │   ├── timeline/            ← Change history
│   │   ├── battlecards/         ← Sales battlecards
│   │   └── activity/            ← Pipeline activity log
│   └── components/              ← Reusable components
│
├── requirements.txt
├── .env
└── README.md
⚠️ Known Limitations
Being upfront about what this project doesn't (yet) handle well:
Heavy JavaScript sites (e.g. Google, Amazon) may return minimal or no content. These sites render most content client-side and often employ bot detection that can serve stripped-down pages to automated browsers. The scraper works reliably on most small-to-mid-size company sites but is not designed to bypass enterprise-grade anti-bot protections. This is an intentional scope limitation — building robust evasion (stealth browser plugins, proxy rotation, CAPTCHA solving) was out of scope for this project.
Job counting on very slow-loading careers pages may still be incomplete. The careers scraper counts likely job postings by inspecting link structure rather than matching exact phrases, which works across most ATS platforms (Greenhouse, Lever, Ashby, custom pages). But if a page's job listings load very slowly via JavaScript, the count can still undercount.
News relevancy filtering isn't perfect for extremely generic or ambiguous company names. The news collector uses exact-phrase search plus a context-keyword filter and a post-fetch relevancy check, which eliminates the vast majority of false matches (e.g. a company called "Notion" no longer pulls in unrelated articles that happen to use the word "notion"). Very rare edge cases with generic names combined with tech-adjacent context words could still occasionally slip through.
Reddit monitoring is not yet implemented. It's stubbed out and gracefully skipped in the pipeline — this requires Reddit API approval, which is a manual, time-gated process not automated by this tool.
First-time crawls never produce signals. The very first time a competitor is added, the detector has nothing to compare against, so it always stores a baseline with zero signals. Real signals only appear from the second crawl onward.
GitHub API rate limits apply without a token. Without GITHUB_TOKEN set, GitHub requests are limited to 60/hour. Adding a personal access token raises this to 5,000/hour.
📄 License
MIT License — free to use, modify, and distribute.
🙏 Acknowledgements
Built with:
Groq — fast LLM inference
Sentence Transformers — local embeddings
ChromaDB — vector storage
FastAPI — backend framework
Next.js — frontend framework
Resend — email delivery
APScheduler — task scheduling