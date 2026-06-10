# 🕵️ Competitor Intelligence Agent

> Your always-on AI analyst that detects what competitors are doing, why it matters, and how confident we are — before you even ask.

![Tech Stack](https://img.shields.io/badge/Stack-FastAPI%20%7C%20Next.js%20%7C%20Groq-blue)
![Cost](https://img.shields.io/badge/Monthly%20Cost-%240-green)
![Python](https://img.shields.io/badge/Python-3.13-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 📌 Overview

An autonomous pipeline system that monitors competitors across the web, detects meaningful changes using semantic analysis, scores intelligence with weighted confidence levels, and delivers analyst-quality briefings — automatically, every week.

**The problem it solves:**
- Hiring a market analyst costs $60k–$100k/year
- Tools like Crayon and Klue cost $15k–$40k/year, enterprise-only
- Manual tracking is inconsistent and time-consuming
- Small teams skip it entirely — and get blindsided

**This pipeline does it autonomously, at zero ongoing cost.**

---

## ✨ Features

### 🔍 Collector
Monitors these free sources per competitor:
- **Company website** — Playwright + BeautifulSoup
- **Careers page** — detects hiring surges and expansion signals
- **Google News RSS** — leadership, funding, product signals
- **GitHub public API** — commit frequency, AI-related repos

### 🧠 Detector (Core Intelligence)
Not just detecting that something changed — detecting **what kind** of change happened and **why it matters**.
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
### 📊 Weighted Confidence Scoring
Every insight is scored using a weighted formula.

### 📈 Temporal Trend Analysis
Tracks signals over time — not just point-in-time snapshots.

### 📝 Reporter with "Why It Matters"
Powered by Groq API — generates analyst-style briefings with:
- Priority classification (🔴 HIGH / 🟡 MEDIUM / 🟢 LOW)
- Evidence trail for every signal
- Forward-looking "Why it matters" section
- Watch for predictions with timeframes

### 🃏 Sales Battlecards
Auto-generated competitive battlecards — what Crayon charges $15k/year for:
- Our strengths vs competitor
- Their weaknesses to exploit
- How to win talking points
- Watch out for alerts

### 👍 Human Feedback Loop
Users rate signals as **Useful** or **Irrelevant** — system automatically adjusts source reliability weights over time.

### 🖥️ Dashboard
Clean Next.js + Tailwind UI:
- Add / remove competitors
- View current and past reports
- Change history timeline
- Trend graphs (Recharts)
- Evidence cards
- Sales battlecards
- Signal feedback buttons

### ⏰ Scheduler
APScheduler triggers full pipeline automatically:
- **Daily** competitors run every day
- **Weekly** competitors run every Monday
- **Monthly** competitors run on 1st of month

---

## 🏗️ Architecture
User Input (competitors list)
↓
[ Scheduler ]           ← APScheduler triggers based on frequency
↓
[ Collector ]           ← Playwright, BS4, RSS, GitHub API
↓
[ Detector ]            ← Sentence Transformers + ChromaDB cosine diff
↓
[ Threshold Filter ]    ← Only meaningful changes pass forward
↓
[ Classifier ]          ← Groq classify_change()
↓
[ Snapshot Store ]      ← Full page snapshot saved to SQLite
↓
[ Scorer ]              ← Weighted confidence formula
↓
[ Reporter ]            ← Groq writes briefing + "Why it matters"
↓
Email / Slack / Dashboard
↑
Human Feedback Loop → Weight Adjuster
---

## 🛠️ Tech Stack — $0/month

| Layer | Tool | Cost |
|-------|------|------|
| Web Scraping | Playwright + BeautifulSoup | ✅ Free |
| News Collection | Google News RSS | ✅ Free |
| Developer Signal | GitHub public API | ✅ Free |
| LLM | Groq API (cloud) | ✅ Free tier |
| Embeddings | Sentence Transformers (local) | ✅ Free |
| Vector Storage | ChromaDB (local) | ✅ Free |
| Database | SQLite | ✅ Free |
| Scheduler | APScheduler | ✅ Free |
| Email | Resend free tier | ✅ Free |
| Backend | FastAPI | ✅ Free |
| Frontend | Next.js + Tailwind | ✅ Free |
| Charts | Recharts | ✅ Free |

**Total monthly cost: $0**

---

## 🚀 Getting Started

### Prerequisites
- Python 3.13+
- Node.js 18+
- Git

### 1. Clone the repository
```bash
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
Groq classifies change type
4
Scorer
Weighted confidence formula
5
Reporter
Groq writes analyst briefing
6
Delivery
Email + Slack delivery
7
Dashboard
Next.js frontend
8
Scheduler
APScheduler weekly automation
📁 Project Structure
competitor-intelligence/
│
├── backend/
│   ├── main.py                  ← FastAPI entry point
│   ├── scheduler.py             ← APScheduler
│   ├── database.py              ← SQLite setup
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
│   │   └── battlecards/         ← Sales battlecards
│   └── components/              ← Reusable components
│
├── requirements.txt
├── .env
└── README.md

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