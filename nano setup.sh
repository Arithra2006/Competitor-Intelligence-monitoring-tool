#!/bin/bash

# Root
mkdir -p competitor-intelligence

cd competitor-intelligence

# Backend folders
mkdir -p backend/phase1_collector
mkdir -p backend/phase2_detector
mkdir -p backend/phase3_classifier
mkdir -p backend/phase4_scorer
mkdir -p backend/phase5_reporter
mkdir -p backend/phase6_delivery
mkdir -p backend/models

# Frontend folders
mkdir -p frontend/app/competitors
mkdir -p frontend/app/reports
mkdir -p frontend/app/trends
mkdir -p frontend/components

# Backend root files
touch backend/main.py
touch backend/scheduler.py
touch backend/database.py

# Phase 1 - Collector
touch backend/phase1_collector/_init_.py
touch backend/phase1_collector/website_scraper.py
touch backend/phase1_collector/careers_scraper.py
touch backend/phase1_collector/news_parser.py
touch backend/phase1_collector/github_client.py
touch backend/phase1_collector/reddit_client.py

# Phase 2 - Detector
touch backend/phase2_detector/_init_.py
touch backend/phase2_detector/embedder.py
touch backend/phase2_detector/chroma_client.py
touch backend/phase2_detector/similarity_checker.py

# Phase 3 - Classifier
touch backend/phase3_classifier/_init_.py
touch backend/phase3_classifier/groq_client.py
touch backend/phase3_classifier/change_classifier.py
touch backend/phase3_classifier/snapshot_store.py

# Phase 4 - Scorer
touch backend/phase4_scorer/_init_.py
touch backend/phase4_scorer/evidence_aggregator.py
touch backend/phase4_scorer/reliability_weights.py
touch backend/phase4_scorer/confidence_scorer.py

# Phase 5 - Reporter
touch backend/phase5_reporter/_init_.py
touch backend/phase5_reporter/briefing_generator.py
touch backend/phase5_reporter/why_it_matters.py
touch backend/phase5_reporter/report_formatter.py

# Phase 6 - Delivery
touch backend/phase6_delivery/_init_.py
touch backend/phase6_delivery/email_sender.py
touch backend/phase6_delivery/slack_sender.py

# Models
touch backend/models/_init_.py
touch backend/models/competitor.py
touch backend/models/snapshot.py
touch backend/models/signal.py
touch backend/models/report.py

# Frontend files
touch frontend/app/page.tsx
touch frontend/app/competitors/page.tsx
touch frontend/app/reports/page.tsx
touch frontend/app/trends/page.tsx

touch frontend/components/EvidenceCard.tsx
touch frontend/components/BeforeAfterView.tsx
touch frontend/components/TrendChart.tsx
touch frontend/components/ReportCard.tsx
touch frontend/components/FeedbackButtons.tsx

# Root files
touch requirements.txt
touch .env
touch README.md

echo "✅ All folders and files created successfully!"