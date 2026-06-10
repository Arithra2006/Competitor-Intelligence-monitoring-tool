# backend/phase6_delivery/slack_sender.py
# Sends weekly intelligence reports via Slack webhook
# Slack incoming webhooks are completely free
# Skip if no Slack workspace — email is sufficient

import sys
import os
import json
import requests
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from models.report import IntelligenceReport
from phase5_reporter.report_formatter import format_slack_message


# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")


# ─────────────────────────────────────────
# MAIN FUNCTION
# ─────────────────────────────────────────

def send_slack_report(report: IntelligenceReport) -> bool:
    """
    Send weekly intelligence report via Slack webhook.

    Args:
        report: IntelligenceReport object from Phase 5

    Returns:
        True if sent successfully, False otherwise
    """
    if not SLACK_WEBHOOK_URL:
        print("⏭️  No SLACK_WEBHOOK_URL found — skipping Slack delivery")
        return False

    print(f"💬 Sending Slack report for: {report.competitor_name}")

    try:
        # Format message for Slack
        slack_text = format_slack_message(report)

        # Build Slack payload
        payload = _build_slack_payload(report, slack_text)

        # Send to Slack
        response = requests.post(
            SLACK_WEBHOOK_URL,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=15,
        )

        if response.status_code == 200:
            print(f"✅ Slack message sent successfully")
            return True
        else:
            print(f"❌ Slack returned status {response.status_code}: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Slack sending failed: {e}")
        return False


def send_slack_reports_batch(reports: dict) -> dict:
    """
    Send Slack reports for multiple competitors.

    Args:
        reports: {competitor_id: IntelligenceReport}

    Returns:
        {competitor_id: bool}
    """
    results = {}
    for competitor_id, report in reports.items():
        success = send_slack_report(report)
        results[competitor_id] = success
    return results


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────

def _build_slack_payload(report: IntelligenceReport, text: str) -> dict:
    """
    Build Slack Block Kit payload for rich formatting.
    Falls back to plain text if no signals.
    """
    total = report.total_signals()
    high  = len(report.high_priority)

    # Header block
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"🕵️ Weekly Intel — {report.competitor_name}",
            }
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Week of {report.week_of}  |  {report.priority_summary()}"
                }
            ]
        },
        {"type": "divider"},
    ]

    if total == 0:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "✅ *No significant changes detected this week.*\nAll monitored sources remain stable.",
            }
        })
    else:
        # High priority signals
        for b in report.high_priority[:3]:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"🔴 *{b['signal_type']}*\n"
                        f"Confidence: {b['confidence']:.0f}%  |  "
                        f"Sources: {', '.join(b.get('sources', []))}\n"
                        f"{b.get('insight', '')[:200]}"
                    )
                }
            })
            blocks.append({"type": "divider"})

        # Medium priority signals
        for b in report.medium_priority[:2]:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"🟡 *{b['signal_type']}*\n"
                        f"Confidence: {b['confidence']:.0f}%  |  "
                        f"Sources: {', '.join(b.get('sources', []))}"
                    )
                }
            })
            blocks.append({"type": "divider"})

        # Low priority
        for b in report.low_priority[:2]:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"🟢 *{b['signal_type']}*\n"
                        f"Confidence: {b['confidence']:.0f}%"
                    )
                }
            })

    # Footer
    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": "_Competitor Intelligence Agent — $0/month_"
            }
        ]
    })

    return {
        "text": f"Weekly Intel Brief — {report.competitor_name}",
        "blocks": blocks,
    }


# ─────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────

if __name__ == "__main__":
    from database import init_db
    from models.signal import ScoredSignal
    from phase5_reporter.briefing_generator import generate_briefing
    from phase5_reporter.report_formatter import format_report

    init_db()

    print("🧪 Testing Slack sender...\n")

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
            ],
            metadata={
                "sources": ["website"],
                "sources_count": 1,
            }
        ),
    ]

    report = generate_briefing(
        competitor_name="Notion",
        scored_signals=test_signals,
        competitor_id=1,
    )
    report = format_report(report, test_signals, "Notion")

    if not SLACK_WEBHOOK_URL:
        print("⏭️  No SLACK_WEBHOOK_URL in .env — Slack delivery skipped")
        print("   To enable: add SLACK_WEBHOOK_URL to .env")
        print("   Get free webhook at: https://api.slack.com/messaging/webhooks")
        print("\n✅ Slack sender code is ready — just needs webhook URL")
    else:
        success = send_slack_report(report)
        if success:
            print("✅ Slack test passed!")
        else:
            print("❌ Slack test failed")