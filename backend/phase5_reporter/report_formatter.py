# backend/phase5_reporter/report_formatter.py
# Formats the final intelligence report
# Combines briefings + why it matters into one polished output
# Ready for email, Slack, and dashboard delivery

import sys
import os
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.signal import ScoredSignal
from models.report import IntelligenceReport
from phase5_reporter.why_it_matters import generate_why_it_matters_batch, detect_structured_event


# ─────────────────────────────────────────
# MAIN FORMATTER FUNCTION
# ─────────────────────────────────────────

def format_report(
    report: IntelligenceReport,
    scored_signals: list[ScoredSignal],
    competitor_name: str,
) -> IntelligenceReport:
    """
    Enhance report with "Why it matters" sections and structured events.
    Returns enriched IntelligenceReport ready for delivery.

    Args:
        report: IntelligenceReport from briefing_generator
        scored_signals: List of ScoredSignal objects from Phase 4
        competitor_name: Name of the competitor

    Returns:
        Enriched IntelligenceReport with full formatted text
    """
    print(f"\n📋 Formatting final report for: {competitor_name}")

    if not scored_signals:
        print("⚠️  No signals — returning empty report")
        return report

    # Generate why it matters for all signals
    why_results = generate_why_it_matters_batch(scored_signals, competitor_name)

    # Build structured events list
    structured_events = [
        detect_structured_event(s) for s in scored_signals
    ]

    # Build enriched report text
    enriched_text = _build_enriched_report(
        report=report,
        scored_signals=scored_signals,
        why_results=why_results,
        structured_events=structured_events,
        competitor_name=competitor_name,
    )

    # Update report
    report.report_text = enriched_text
    report.metadata["structured_events"] = structured_events
    report.metadata["why_results"] = why_results

    print(f"✅ Report formatted — {len(enriched_text)} characters")
    return report


def format_slack_message(report: IntelligenceReport) -> str:
    """
    Format report as a concise Slack message.
    Slack has character limits — keep it punchy.

    Args:
        report: IntelligenceReport object

    Returns:
        Formatted Slack message string
    """
    lines = []
    lines.append(f"*🕵️ Weekly Intel Brief — {report.competitor_name}*")
    lines.append(f"_{report.week_of}_")
    lines.append("")

    total = report.total_signals()
    if total == 0:
        lines.append("✅ No significant changes detected this week.")
        return "\n".join(lines)

    lines.append(f"*{report.priority_summary()}*")
    lines.append("")

    # High priority only in Slack
    for b in report.high_priority[:3]:
        lines.append(f"🔴 *{b['signal_type']}* — {b['confidence']:.0f}% confidence")
        # First sentence of insight only
        insight = b.get("insight", "")
        first_sentence = insight.split(".")[0] + "." if insight else ""
        if first_sentence:
            lines.append(f"   {first_sentence}")
        lines.append("")

    for b in report.medium_priority[:2]:
        lines.append(f"🟡 *{b['signal_type']}* — {b['confidence']:.0f}% confidence")
        lines.append("")

    lines.append("_Full report available in dashboard._")
    return "\n".join(lines)


def format_email_html(report: IntelligenceReport) -> str:
    """
    Format report as HTML for email delivery via Resend.

    Args:
        report: IntelligenceReport object

    Returns:
        HTML string for email body
    """
    now = datetime.now(timezone.utc).strftime("%B %d, %Y")

    html = f"""
<!DOCTYPE html>
<html>
<head>
<style>
  body {{ font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto; color: #333; }}
  .header {{ background: #1a1a2e; color: white; padding: 20px; border-radius: 8px; }}
  .header h1 {{ margin: 0; font-size: 20px; }}
  .header p {{ margin: 5px 0 0; color: #aaa; font-size: 13px; }}
  .section {{ margin: 20px 0; }}
  .signal {{ background: #f8f9fa; border-left: 4px solid #ccc; padding: 15px; margin: 10px 0; border-radius: 4px; }}
  .signal.high {{ border-left-color: #e74c3c; }}
  .signal.medium {{ border-left-color: #f39c12; }}
  .signal.low {{ border-left-color: #27ae60; }}
  .signal h3 {{ margin: 0 0 8px; font-size: 15px; }}
  .signal p {{ margin: 5px 0; font-size: 14px; line-height: 1.5; }}
  .meta {{ font-size: 12px; color: #888; }}
  .why {{ background: #fff3cd; padding: 10px; border-radius: 4px; margin-top: 10px; font-size: 13px; }}
  .footer {{ text-align: center; color: #aaa; font-size: 12px; margin-top: 30px; }}
  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: bold; }}
  .badge.high {{ background: #fde8e8; color: #e74c3c; }}
  .badge.medium {{ background: #fef3cd; color: #f39c12; }}
  .badge.low {{ background: #d4edda; color: #27ae60; }}
</style>
</head>
<body>

<div class="header">
  <h1>🕵️ Weekly Intelligence Brief — {report.competitor_name}</h1>
  <p>Week of {report.week_of} &nbsp;|&nbsp; Generated {now}</p>
</div>

<div class="section">
  <p><strong>Signals detected:</strong> {report.total_signals()} &nbsp;|&nbsp; {report.priority_summary()}</p>
</div>
"""

    # High priority signals
    if report.high_priority:
        html += "<div class='section'><h2>🔴 High Priority</h2>"
        for b in report.high_priority:
            html += f"""
<div class='signal high'>
  <h3>{b['signal_type']} <span class='badge high'>HIGH</span></h3>
  <p class='meta'>Confidence: {b['confidence']:.1f}% &nbsp;|&nbsp; Sources: {', '.join(b.get('sources', []))}</p>
  <p>{b.get('insight', '')}</p>
</div>"""
        html += "</div>"

    # Medium priority signals
    if report.medium_priority:
        html += "<div class='section'><h2>🟡 Medium Priority</h2>"
        for b in report.medium_priority:
            html += f"""
<div class='signal medium'>
  <h3>{b['signal_type']} <span class='badge medium'>MEDIUM</span></h3>
  <p class='meta'>Confidence: {b['confidence']:.1f}% &nbsp;|&nbsp; Sources: {', '.join(b.get('sources', []))}</p>
  <p>{b.get('insight', '')}</p>
</div>"""
        html += "</div>"

    # Low priority signals
    if report.low_priority:
        html += "<div class='section'><h2>🟢 Watch List</h2>"
        for b in report.low_priority:
            html += f"""
<div class='signal low'>
  <h3>{b['signal_type']} <span class='badge low'>LOW</span></h3>
  <p class='meta'>Confidence: {b['confidence']:.1f}% &nbsp;|&nbsp; Sources: {', '.join(b.get('sources', []))}</p>
  <p>{b.get('insight', '')}</p>
</div>"""
        html += "</div>"

    html += """
<div class='footer'>
  <p>Generated by Competitor Intelligence Agent &nbsp;|&nbsp; $0/month</p>
</div>

</body>
</html>"""

    return html


# ─────────────────────────────────────────
# INTERNAL HELPERS
# ─────────────────────────────────────────

def _build_enriched_report(
    report: IntelligenceReport,
    scored_signals: list[ScoredSignal],
    why_results: list[dict],
    structured_events: list[dict],
    competitor_name: str,
) -> str:
    """
    Build the full enriched report text with
    briefings + why it matters + structured events.
    """
    now = datetime.now(timezone.utc)
    lines = []

    # Header
    lines.append("=" * 60)
    lines.append(f"WEEKLY INTELLIGENCE BRIEF — {competitor_name.upper()}")
    lines.append(f"Week of {now.strftime('%B %d, %Y')}")
    lines.append(f"Generated: {now.strftime('%Y-%m-%d %H:%M')} UTC")
    lines.append("=" * 60)

    total = report.total_signals()
    if total == 0:
        lines.append("\nNO SIGNIFICANT CHANGES DETECTED THIS WEEK")
        lines.append("All monitored sources remain stable.")
        lines.append("\n" + "=" * 60)
        return "\n".join(lines)

    lines.append(f"\nSIGNALS THIS WEEK: {total} detected")
    lines.append(report.priority_summary())

    # Build signal sections with why it matters
    signal_why_pairs = list(zip(scored_signals, why_results))

    # HIGH priority
    high_pairs = [(s, w) for s, w in signal_why_pairs if s.priority == "HIGH"]
    if high_pairs:
        lines.append("\n" + "─" * 60)
        lines.append("🔴 HIGH PRIORITY")
        lines.append("─" * 60)
        for signal, why in high_pairs:
            lines.extend(_format_signal_section(signal, why, report))

    # MEDIUM priority
    medium_pairs = [(s, w) for s, w in signal_why_pairs if s.priority == "MEDIUM"]
    if medium_pairs:
        lines.append("\n" + "─" * 60)
        lines.append("🟡 MEDIUM PRIORITY")
        lines.append("─" * 60)
        for signal, why in medium_pairs:
            lines.extend(_format_signal_section(signal, why, report))

    # LOW priority
    low_pairs = [(s, w) for s, w in signal_why_pairs if s.priority == "LOW"]
    if low_pairs:
        lines.append("\n" + "─" * 60)
        lines.append("🟢 WATCH LIST")
        lines.append("─" * 60)
        for signal, why in low_pairs:
            lines.extend(_format_signal_section(signal, why, report))

    # Structured events section
    if structured_events:
        lines.append("\n" + "─" * 60)
        lines.append("📋 STRUCTURED EVENTS LOG")
        lines.append("─" * 60)
        for event in structured_events:
            lines.append(
                f"  [{event['event_type']}] "
                f"{event['entity'][:40]} | "
                f"Source: {event['source']} | "
                f"Confidence: {event['confidence']}% | "
                f"Date: {event['date']}"
            )

    # Footer
    lines.append("\n" + "=" * 60)
    lines.append("END OF BRIEF")
    lines.append("=" * 60)

    return "\n".join(lines)


def _format_signal_section(
    signal: ScoredSignal,
    why: dict,
    report: IntelligenceReport,
) -> list[str]:
    """Format a single signal section with insight + why it matters."""
    lines = []

    lines.append(f"\n→ {signal.signal_type}")
    lines.append(
        f"  Confidence: {signal.confidence:.1f}%  |  "
        f"Sources: {', '.join(signal.metadata.get('sources', []))}"
    )

    # Find matching briefing insight
    all_briefings = (
        report.high_priority +
        report.medium_priority +
        report.low_priority
    )
    insight = ""
    for b in all_briefings:
        if b.get("signal_type") == signal.signal_type:
            insight = b.get("insight", "")
            break

    if insight:
        lines.append(f"\n  INSIGHT")
        lines.append(f"  {insight}")

    # Source excerpt — the actual article or commit that triggered this,
    # when available (news and github sources only)
    excerpt_lines = _format_source_excerpts(signal)
    if excerpt_lines:
        lines.extend(excerpt_lines)

    # Why it matters
    why_text = why.get("why_it_matters", "")
    if why_text:
        lines.append(f"\n  WHY IT MATTERS")
        for line in why_text.split("\n"):
            lines.append(f"  {line}")

    # Watch for
    watch_for = why.get("watch_for", [])
    if watch_for:
        lines.append(f"\n  WATCH FOR (next {why.get('timeframe', 'quarter')})")
        for w in watch_for:
            lines.append(f"  • {w}")

    return lines


def _format_source_excerpts(signal: ScoredSignal) -> list[str]:
    """
    Build the "SOURCE ARTICLE" / "SOURCE COMMIT" block for any evidence
    item that has a source_excerpt attached (news articles, github commits).
    Returns an empty list if no evidence on this signal has an excerpt.
    """
    lines = []

    for item in signal.evidence:
        excerpt = item.get("source_excerpt")
        if not excerpt:
            continue

        if excerpt.get("kind") == "article":
            lines.append(f"\n  SOURCE ARTICLE")
            title = excerpt.get("title", "")
            source_name = excerpt.get("source_name", "Unknown")
            published = excerpt.get("published", "")
            lines.append(f"  \"{title}\" — {source_name}, {published}")
            summary = excerpt.get("summary", "")
            if summary:
                lines.append(f"  {summary[:250]}")
            link = excerpt.get("link", "")
            if link:
                lines.append(f"  {link}")

        elif excerpt.get("kind") == "commit":
            lines.append(f"\n  SOURCE COMMIT")
            repo = excerpt.get("repo", "")
            date = excerpt.get("date", "")[:10]
            message = excerpt.get("message", "")
            lines.append(f"  [{repo}] {date} — {message}")

    return lines


# ─────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────

if __name__ == "__main__":
    from database import init_db
    from models.signal import ScoredSignal
    from models.report import IntelligenceReport
    from briefing_generator import generate_briefing

    init_db()

    print("🧪 Testing report formatter...\n")

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
                    "detail": "AI-powered added to homepage headline",
                    "reasoning": "Direct AI language added",
                },
                {
                    "source": "careers",
                    "reliability": 0.8,
                    "detail": "6 AI engineer openings posted",
                    "reasoning": "Hiring confirms AI investment",
                },
            ],
            metadata={
                "sources": ["website", "careers"],
                "sources_count": 2,
            }
        ),
        ScoredSignal(
            competitor_id=1,
            signal_type="New market targeted",
            confidence=73.0,
            change_type="New market targeted",
            priority="MEDIUM",
            evidence=[
                {
                    "source": "website",
                    "reliability": 0.9,
                    "detail": "Healthcare vertical page added",
                    "reasoning": "New industry landing page",
                },
            ],
            metadata={
                "sources": ["website"],
                "sources_count": 1,
            }
        ),
    ]

    # Generate base briefing
    report = generate_briefing(
        competitor_name="Notion",
        scored_signals=test_signals,
        competitor_id=1,
    )

    # Format full report
    formatted = format_report(report, test_signals, "Notion")

    # Print full report
    print("\n" + "="*60)
    print("FULL FORMATTED REPORT:")
    print("="*60)
    print(formatted.report_text)

    # Test Slack format
    print("\n" + "="*60)
    print("SLACK FORMAT:")
    print("="*60)
    print(format_slack_message(formatted))

    print("\n✅ Report formatter test complete!")