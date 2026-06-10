# backend/phase6_delivery/email_sender.py
# Sends weekly intelligence reports via email using Resend
# Resend free tier: 100 emails/day, 3000/month — plenty for this project

import sys
import os
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

import resend
from models.report import IntelligenceReport
from phase5_reporter.report_formatter import format_email_html


# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────

RESEND_API_KEY   = os.getenv("RESEND_API_KEY")
EMAIL_TO         = os.getenv("REPORT_EMAIL_TO")
EMAIL_FROM       = os.getenv("REPORT_EMAIL_FROM", "onboarding@resend.dev")


# ─────────────────────────────────────────
# MAIN FUNCTION
# ─────────────────────────────────────────

def send_email_report(report: IntelligenceReport) -> bool:
    """
    Send weekly intelligence report via email using Resend.

    Args:
        report: IntelligenceReport object from Phase 5

    Returns:
        True if sent successfully, False otherwise
    """
    if not RESEND_API_KEY:
        print("⚠️  No RESEND_API_KEY found — skipping email delivery")
        return False

    if not EMAIL_TO:
        print("⚠️  No REPORT_EMAIL_TO found — skipping email delivery")
        return False

    print(f"📧 Sending email report for: {report.competitor_name}")
    print(f"   To  : {EMAIL_TO}")
    print(f"   From: {EMAIL_FROM}")

    try:
        # Set API key
        resend.api_key = RESEND_API_KEY

        # Build email subject
        subject = _build_subject(report)

        # Build HTML body
        html_body = format_email_html(report)

        # Build plain text fallback
        text_body = _build_text_fallback(report)

        # Send via Resend
        response = resend.Emails.send({
            "from": EMAIL_FROM,
            "to": [EMAIL_TO],
            "subject": subject,
            "html": html_body,
            "text": text_body,
        })

        if response and response.get("id"):
            print(f"✅ Email sent successfully — ID: {response['id']}")
            return True
        else:
            print(f"⚠️  Email sent but no ID returned: {response}")
            return True

    except Exception as e:
        print(f"❌ Email sending failed: {e}")
        return False


def send_email_reports_batch(reports: dict) -> dict:
    """
    Send email reports for multiple competitors.

    Args:
        reports: {competitor_id: IntelligenceReport}

    Returns:
        {competitor_id: bool} — True if sent successfully
    """
    results = {}
    for competitor_id, report in reports.items():
        success = send_email_report(report)
        results[competitor_id] = success
    return results


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────

def _build_subject(report: IntelligenceReport) -> str:
    """Build email subject line."""
    total = report.total_signals()
    high  = len(report.high_priority)

    if total == 0:
        return f"🕵️ Weekly Intel — {report.competitor_name} | No changes detected"
    elif high > 0:
        return f"🔴 Weekly Intel — {report.competitor_name} | {high} HIGH priority signal(s)"
    else:
        return f"🕵️ Weekly Intel — {report.competitor_name} | {total} signal(s) detected"


def _build_text_fallback(report: IntelligenceReport) -> str:
    """Plain text fallback for email clients that don't support HTML."""
    return report.report_text


# ─────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────

if __name__ == "__main__":
    from database import init_db
    from models.signal import ScoredSignal
    from models.report import IntelligenceReport
    from phase5_reporter.briefing_generator import generate_briefing
    from phase5_reporter.report_formatter import format_report

    init_db()

    print("🧪 Testing email sender...\n")

    # Create test signals
    test_signals = [
        ScoredSignal(
            competitor_id=1,
            signal_type="AI positioning added",
            confidence=85.4,
            change_type="AI positioning added",
            priority="HIGH",
            evidence=[
                {
                    "source": "website",
                    "reliability": 0.9,
                    "detail": "AI-powered added to homepage",
                    "reasoning": "Direct AI language added",
                },
                {
                    "source": "careers",
                    "reliability": 0.8,
                    "detail": "6 AI engineer openings",
                    "reasoning": "Hiring confirms AI investment",
                },
            ],
            metadata={
                "sources": ["website", "careers"],
                "sources_count": 2,
            }
        ),
    ]

    # Generate report
    report = generate_briefing(
        competitor_name="Notion",
        scored_signals=test_signals,
        competitor_id=1,
    )
    report = format_report(report, test_signals, "Notion")

    # Send email
    print(f"Sending test email to: {EMAIL_TO}")
    success = send_email_report(report)

    if success:
        print(f"\n✅ Email test passed — check {EMAIL_TO}")
    else:
        print("\n❌ Email test failed — check .env file")