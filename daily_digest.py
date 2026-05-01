#!/usr/bin/env python3
"""
Daily AI & News Digest
Uses the local `claude` CLI for summarisation — no API key needed.
Sends via Resend. Run locally or via launchd at 7am weekdays.
"""
import os
import re
import html
import difflib
import subprocess
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

import feedparser
import resend
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Feed configuration
# ---------------------------------------------------------------------------
FEEDS = {
    "ai": [
        "https://techcrunch.com/category/artificial-intelligence/feed/",
        "https://venturebeat.com/category/ai/feed/",
        "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        "https://hnrss.org/newest?q=AI&points=50",
        "https://openai.com/news/rss.xml",
        "https://www.anthropic.com/rss.xml",
        "https://huggingface.co/blog/feed.xml",
    ],
    "podcast": [
        "https://lexfridman.com/feed/podcast/",
        "https://twimlai.com/feed/",
    ],
    "world": [
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "https://feeds.reuters.com/reuters/topNews",
        "https://www.theguardian.com/world/rss",
    ],
    "australia": [
        "https://www.abc.net.au/news/feed/51120/rss.xml",
        "https://www.smh.com.au/rss/feed.xml",
        "https://www.theguardian.com/australia-news/rss",
    ],
}

SIMILARITY_THRESHOLD = 0.75


# ---------------------------------------------------------------------------
# Fetch & deduplicate
# ---------------------------------------------------------------------------
def fetch_entries(feeds: dict) -> dict:
    cutoff_24 = datetime.now(timezone.utc) - timedelta(hours=24)
    cutoff_48 = datetime.now(timezone.utc) - timedelta(hours=48)
    results = {k: [] for k in feeds}

    for cat, urls in feeds.items():
        cutoff = cutoff_48 if cat == "podcast" else cutoff_24
        for url in urls:
            try:
                feed = feedparser.parse(url)
                source = feed.feed.get("title", url)
                for e in feed.entries:
                    dt = _parse_date(e)
                    if dt and dt >= cutoff:
                        results[cat].append({
                            "title": e.get("title", "").strip(),
                            "url": e.get("link", ""),
                            "source": source,
                        })
            except Exception as ex:
                print(f"  WARN {url}: {ex}")
        results[cat] = _dedupe(results[cat])
        print(f"  {cat}: {len(results[cat])} stories")

    return results


def _parse_date(entry):
    for attr in ("published", "updated"):
        raw = entry.get(attr)
        if raw:
            try:
                dt = parsedate_to_datetime(raw)
                return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
            except Exception:
                pass
    return None


def _dedupe(entries):
    seen, out = [], []
    for e in entries:
        t = e["title"].lower()
        if not any(difflib.SequenceMatcher(None, t, s).ratio() >= SIMILARITY_THRESHOLD for s in seen):
            seen.append(t)
            out.append(e)
    return out


# ---------------------------------------------------------------------------
# Claude CLI summarisation
# ---------------------------------------------------------------------------
def build_prompt(entries: dict) -> str:
    lines = [
        "You are producing a daily news digest for Australian business operators.",
        "Based on the stories below, produce output in EXACTLY this format — no extra text:\n",

        "BRIEFING_START",
        "Write a 600-word briefing with four bold headings: **AI & Technology**, **Australian Business & Finance**, **World Markets & Global Business**, **The Big Picture**.",
        "Tone: sharp, punchy, no jargon, short sentences, active voice. Every sentence must earn its place — no padding.",
        "No stage directions, no script labels. Flow as clean readable prose.",
        "End with 1 sentence pointing readers to the full digest below.",
        "BRIEFING_END\n",

        "AI_OVERVIEW_START",
        "2-sentence overview of the day in AI.",
        "AI_OVERVIEW_END\n",

        "Then for the 5 most important AI stories, each block formatted EXACTLY as:",
        "AI_STORY_START",
        "TITLE: <title>",
        "SOURCE: <source>",
        "TAG: <one of: Lab Announcement | Research | Industry News | Community | Business>",
        "URL: <url>",
        "SUMMARY: <2 sentences>",
        "AI_STORY_END\n",

        "Then for up to 3 podcast episodes (48hr window), each:",
        "PODCAST_START",
        "TITLE: <episode title>",
        "SHOW: <show name>",
        "URL: <url>",
        "SUMMARY: <1-2 sentences>",
        "PODCAST_END\n",

        "WORLD_OVERVIEW_START",
        "1-sentence snapshot of the biggest global story.",
        "WORLD_OVERVIEW_END\n",

        "Then for the 3 most important world stories:",
        "WORLD_STORY_START",
        "TITLE: <title>",
        "SOURCE: <source>",
        "URL: <url>",
        "SUMMARY: <2 sentences>",
        "WORLD_STORY_END\n",

        "AUS_OVERVIEW_START",
        "1-sentence snapshot of the biggest Australian story.",
        "AUS_OVERVIEW_END\n",

        "Then for the 3 most important Australian stories:",
        "AUS_STORY_START",
        "TITLE: <title>",
        "SOURCE: <source>",
        "URL: <url>",
        "SUMMARY: <2 sentences>",
        "AUS_STORY_END\n",

        "=== STORIES ===\n",
    ]

    for cat, items in entries.items():
        lines.append(f"--- {cat.upper()} ---")
        for item in items[:25]:
            lines.append(f"[{item['source']}] {item['title']}")
            lines.append(f"  {item['url']}")
        lines.append("")

    return "\n".join(lines)


def call_claude(prompt: str) -> str:
    print("  Calling claude CLI...")
    result = subprocess.run(
        ["claude", "-p", prompt],
        capture_output=True, text=True, timeout=300
    )
    if result.returncode != 0:
        raise RuntimeError(f"claude CLI error: {result.stderr}")
    return result.stdout


# ---------------------------------------------------------------------------
# Parse Claude response
# ---------------------------------------------------------------------------
def _extract(text: str, tag: str) -> str:
    m = re.search(rf"{tag}_START\n(.*?)\n{tag}_END", text, re.DOTALL)
    return m.group(1).strip() if m else ""


def _extract_blocks(text: str, tag: str) -> list[dict]:
    blocks = re.findall(rf"{tag}_START\n(.*?)\n{tag}_END", text, re.DOTALL)
    items = []
    for block in blocks:
        item = {}
        for line in block.strip().splitlines():
            for key in ("TITLE", "SOURCE", "TAG", "URL", "SUMMARY", "SHOW"):
                if line.startswith(f"{key}:"):
                    item[key.lower()] = line[len(key)+1:].strip()
        if item:
            items.append(item)
    return items


def parse_response(raw: str) -> dict:
    return {
        "briefing":       _extract(raw, "BRIEFING"),
        "ai_overview":    _extract(raw, "AI_OVERVIEW"),
        "ai_stories":     _extract_blocks(raw, "AI_STORY"),
        "podcasts":       _extract_blocks(raw, "PODCAST"),
        "world_overview": _extract(raw, "WORLD_OVERVIEW"),
        "world_stories":  _extract_blocks(raw, "WORLD_STORY"),
        "aus_overview":   _extract(raw, "AUS_OVERVIEW"),
        "aus_stories":    _extract_blocks(raw, "AUS_STORY"),
    }


# ---------------------------------------------------------------------------
# HTML rendering
# ---------------------------------------------------------------------------
def _e(s: str) -> str:
    return html.escape(s or "")


def _story_card(i: int, item: dict, link_color: str = "#1d4ed8") -> str:
    tag = item.get("tag", "")
    tag_html = (
        f'&nbsp;<span style="display:inline-block;padding:2px 8px;font-size:11px;'
        f'font-weight:600;border-radius:999px;background:#dbeafe;color:#1e40af;">{_e(tag)}</span>'
    ) if tag else ""
    return f"""
<div style="margin-bottom:24px;padding-bottom:20px;border-bottom:1px solid #e5e7eb;">
  <p style="margin:0 0 6px;">
    <span style="font-size:12px;color:#6b7280;text-transform:uppercase;letter-spacing:.05em;">{i}. {_e(item.get('source',''))}</span>{tag_html}
  </p>
  <h3 style="margin:0 0 8px;font-size:17px;font-weight:600;line-height:1.4;">
    <a href="{_e(item.get('url',''))}" style="color:{link_color};text-decoration:none;">{_e(item.get('title',''))}</a>
  </h3>
  <p style="margin:0;font-size:14px;color:#374151;line-height:1.6;">{_e(item.get('summary',''))}</p>
</div>"""


def _podcast_card(item: dict) -> str:
    return f"""
<div style="margin-bottom:16px;padding:16px;background:#faf5ff;border-radius:8px;border:1px solid #e9d5ff;">
  <p style="margin:0 0 4px;font-size:12px;font-weight:600;color:#7c3aed;">{_e(item.get('show',''))}</p>
  <h3 style="margin:0 0 8px;font-size:16px;font-weight:600;line-height:1.4;">
    <a href="{_e(item.get('url',''))}" style="color:#6d28d9;text-decoration:none;">{_e(item.get('title',''))}</a>
  </h3>
  <p style="margin:0;font-size:14px;color:#374151;line-height:1.6;">{_e(item.get('summary',''))}</p>
</div>"""


def render_html(d: dict, date_str: str) -> str:
    ai_stories_html = "".join(_story_card(i+1, s) for i, s in enumerate(d["ai_stories"][:5]))
    podcast_html = (
        "".join(_podcast_card(p) for p in d["podcasts"])
        if d["podcasts"] else '<p style="color:#6b7280;font-size:14px;">No new episodes today.</p>'
    )
    world_stories_html = "".join(_story_card(i+1, s, "#059669") for i, s in enumerate(d["world_stories"][:3]))
    aus_stories_html = "".join(_story_card(i+1, s, "#dc2626") for i, s in enumerate(d["aus_stories"][:3]))

    # Convert **Heading** to styled section headers, then paragraphs
    briefing_raw = d["briefing"]
    briefing_raw = re.sub(
        r'\*\*(.+?)\*\*',
        r'</p><h3 style="margin:20px 0 8px;font-size:16px;font-weight:700;color:#1e3a8a;border-bottom:1px solid #fde68a;padding-bottom:4px;">\1</h3><p style="margin:0 0 14px;">',
        briefing_raw
    )
    briefing_html = f'<p style="margin:0 0 14px;">{briefing_raw}</p>'
    briefing_html = briefing_html.replace("\n\n", '</p><p style="margin:0 0 14px;">')

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Daily Digest – {date_str}</title></head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f3f4f6;padding:32px 16px;">
<tr><td align="center">
<table width="640" cellpadding="0" cellspacing="0" style="max-width:640px;width:100%;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.08);">

  <!-- Header -->
  <tr><td style="background:linear-gradient(135deg,#1e3a8a 0%,#1d4ed8 100%);padding:36px 40px;">
    <p style="margin:0 0 4px;font-size:12px;color:#93c5fd;text-transform:uppercase;letter-spacing:.1em;">Daily Briefing</p>
    <h1 style="margin:0;font-size:28px;font-weight:700;color:#fff;">Your Daily Digest</h1>
    <p style="margin:8px 0 0;font-size:14px;color:#bfdbfe;">{date_str}</p>
  </td></tr>

  <!-- Briefing -->
  <tr><td style="padding:32px 40px 28px;">
    <p style="margin:0 0 4px;font-size:11px;font-weight:700;color:#d97706;text-transform:uppercase;letter-spacing:.12em;">🎙️ Daily Business Briefing</p>
    <h2 style="margin:0 0 4px;font-size:20px;font-weight:700;color:#111827;">Your 10-Minute Read</h2>
    <p style="margin:0 0 20px;font-size:13px;color:#6b7280;">For Australian business operators · Full digest below</p>
    <div style="background:#fffbeb;border:1px solid #fde68a;border-radius:8px;padding:24px 28px;font-size:15px;color:#1f2937;line-height:1.8;font-family:Georgia,serif;">
      <p style="margin:0 0 14px;">{briefing_html}</p>
    </div>
  </td></tr>

  <tr><td style="padding:0 40px;"><hr style="border:none;border-top:2px solid #e5e7eb;margin:0;"></td></tr>

  <!-- AI -->
  <tr><td style="padding:32px 40px 8px;">
    <p style="margin:0 0 4px;font-size:11px;font-weight:700;color:#1d4ed8;text-transform:uppercase;letter-spacing:.12em;">🤖 Artificial Intelligence</p>
    <h2 style="margin:0 0 16px;font-size:20px;font-weight:700;color:#111827;">AI Overview</h2>
    <p style="margin:0 0 24px;font-size:16px;color:#1f2937;line-height:1.7;padding:20px;background:#eff6ff;border-left:4px solid #1d4ed8;border-radius:0 8px 8px 0;">{_e(d['ai_overview'])}</p>
    {ai_stories_html}
  </td></tr>

  <tr><td style="padding:0 40px;"><hr style="border:none;border-top:2px solid #e5e7eb;margin:0;"></td></tr>

  <!-- Podcasts -->
  <tr><td style="padding:32px 40px 8px;">
    <p style="margin:0 0 4px;font-size:11px;font-weight:700;color:#7c3aed;text-transform:uppercase;letter-spacing:.12em;">🎙️ Podcast Picks</p>
    {podcast_html}
  </td></tr>

  <tr><td style="padding:0 40px;"><hr style="border:none;border-top:2px solid #e5e7eb;margin:0;"></td></tr>

  <!-- World -->
  <tr><td style="padding:32px 40px 8px;">
    <p style="margin:0 0 4px;font-size:11px;font-weight:700;color:#059669;text-transform:uppercase;letter-spacing:.12em;">🌍 World News</p>
    <h2 style="margin:0 0 16px;font-size:20px;font-weight:700;color:#111827;">Global Snapshot</h2>
    <p style="margin:0 0 24px;font-size:16px;color:#1f2937;line-height:1.7;padding:20px;background:#ecfdf5;border-left:4px solid #059669;border-radius:0 8px 8px 0;">{_e(d['world_overview'])}</p>
    {world_stories_html}
  </td></tr>

  <tr><td style="padding:0 40px;"><hr style="border:none;border-top:2px solid #e5e7eb;margin:0;"></td></tr>

  <!-- Australia -->
  <tr><td style="padding:32px 40px 8px;">
    <p style="margin:0 0 4px;font-size:11px;font-weight:700;color:#dc2626;text-transform:uppercase;letter-spacing:.12em;">🇦🇺 Australian News</p>
    <h2 style="margin:0 0 16px;font-size:20px;font-weight:700;color:#111827;">Australia Snapshot</h2>
    <p style="margin:0 0 24px;font-size:16px;color:#1f2937;line-height:1.7;padding:20px;background:#fef2f2;border-left:4px solid #dc2626;border-radius:0 8px 8px 0;">{_e(d['aus_overview'])}</p>
    {aus_stories_html}
  </td></tr>

  <!-- Footer -->
  <tr><td style="padding:24px 40px 32px;background:#f9fafb;border-top:1px solid #e5e7eb;">
    <p style="margin:0;font-size:13px;color:#9ca3af;text-align:center;">Your daily AI-powered business briefing</p>
  </td></tr>

</table></td></tr></table>
</body></html>"""


# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------
def load_recipients(path: str = "recipients.txt") -> list[str]:
    with open(path) as f:
        return [l.strip() for l in f if l.strip() and not l.startswith("#")]


def send_email(to: list[str], subject: str, html_body: str) -> None:
    resend.api_key = os.environ["RESEND_API_KEY"]
    params: resend.Emails.SendParams = {
        "from": os.environ.get("FROM_EMAIL", "onboarding@resend.dev"),
        "to": to,
        "subject": subject,
        "html": html_body,
    }
    resp = resend.Emails.send(params)
    print(f"  Email sent! ID: {resp.get('id', resp)}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    date_str = datetime.now(timezone.utc).strftime("%B %d, %Y")
    subject = f"Your Daily Digest – {date_str}"

    print("Fetching RSS feeds…")
    entries = fetch_entries(FEEDS)
    total = sum(len(v) for v in entries.values())
    print(f"  {total} stories total after deduplication")

    if total == 0:
        print("No stories found. Exiting.")
        return

    print("Summarising with Claude…")
    prompt = build_prompt(entries)
    raw = call_claude(prompt)

    print("Parsing response…")
    digest = parse_response(raw)

    print("Rendering HTML…")
    html_body = render_html(digest, date_str)

    print("Loading recipients…")
    recipients = load_recipients()
    print(f"  Sending to {len(recipients)} recipient(s)")

    send_email(recipients, subject, html_body)
    print("Done! ✅")


if __name__ == "__main__":
    main()
