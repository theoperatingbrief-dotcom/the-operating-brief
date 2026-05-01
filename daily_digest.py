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
from supabase import create_client

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

    limits = {"ai": 15, "podcast": 3, "world": 12, "australia": 12}
    for cat, items in entries.items():
        lines.append(f"--- {cat.upper()} ---")
        for item in items[:limits.get(cat, 12)]:
            lines.append(f"[{item['source']}] {item['title']}")
            lines.append(f"  {item['url']}")
        lines.append("")

    return "\n".join(lines)


def call_claude(prompt: str) -> str:
    print("  Calling claude CLI...")
    result = subprocess.run(
        ["claude", "-p", prompt],
        capture_output=True, text=True, timeout=600
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


def _story_card(i: int, item: dict, link_color: str = "#111") -> str:
    tag = item.get("tag", "")
    tag_html = (
        f'&nbsp;<span style="font-size:11px;color:#888;font-family:Arial,sans-serif;">· {_e(tag)}</span>'
    ) if tag else ""
    return f"""
<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:20px;">
  <tr><td style="padding-bottom:16px;border-bottom:1px solid #eee;">
    <p style="margin:0 0 4px;font-size:11px;color:#888;font-family:Arial,sans-serif;text-transform:uppercase;letter-spacing:.05em;">{_e(item.get('source',''))}{tag_html}</p>
    <p style="margin:0 0 6px;font-size:17px;font-weight:700;color:#111;line-height:1.35;font-family:Georgia,serif;"><a href="{_e(item.get('url',''))}" style="color:#111;text-decoration:none;">{_e(item.get('title',''))}</a></p>
    <p style="margin:0;font-size:14px;color:#444;line-height:1.6;font-family:Arial,sans-serif;">{_e(item.get('summary',''))}</p>
  </td></tr>
</table>"""


def _podcast_card(item: dict) -> str:
    return f"""
<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:20px;">
  <tr><td style="padding-bottom:16px;border-bottom:1px solid #eee;">
    <p style="margin:0 0 4px;font-size:11px;color:#888;font-family:Arial,sans-serif;text-transform:uppercase;letter-spacing:.05em;">{_e(item.get('show',''))}</p>
    <p style="margin:0 0 6px;font-size:17px;font-weight:700;color:#111;line-height:1.35;font-family:Georgia,serif;"><a href="{_e(item.get('url',''))}" style="color:#111;text-decoration:none;">{_e(item.get('title',''))}</a></p>
    <p style="margin:0;font-size:14px;color:#444;line-height:1.6;font-family:Arial,sans-serif;">{_e(item.get('summary',''))}</p>
  </td></tr>
</table>"""


def render_html(d: dict, date_str: str) -> str:
    ai_stories_html = "".join(_story_card(i+1, s) for i, s in enumerate(d["ai_stories"][:5]))
    podcast_html = (
        "".join(_podcast_card(p) for p in d["podcasts"])
        if d["podcasts"] else '<p style="font-size:14px;color:#888;font-family:Arial,sans-serif;">No new episodes today.</p>'
    )
    world_stories_html = "".join(_story_card(i+1, s) for i, s in enumerate(d["world_stories"][:3]))
    aus_stories_html = "".join(_story_card(i+1, s) for i, s in enumerate(d["aus_stories"][:3]))

    # Convert **Heading** to styled section headers, then paragraphs
    briefing_raw = d["briefing"]
    briefing_raw = re.sub(
        r'\*\*(.+?)\*\*',
        r'</p><h3 style="margin:24px 0 8px;font-size:14px;font-weight:700;color:#111;text-transform:uppercase;letter-spacing:.08em;font-family:Arial,sans-serif;border-left:3px solid #111;padding-left:10px;">\1</h3><p style="margin:0 0 16px;font-size:16px;color:#222;line-height:1.75;font-family:Georgia,serif;">',
        briefing_raw
    )
    briefing_html = f'<p style="margin:0 0 16px;font-size:16px;color:#222;line-height:1.75;font-family:Georgia,serif;">{briefing_raw}</p>'
    briefing_html = briefing_html.replace("\n\n", '</p><p style="margin:0 0 16px;font-size:16px;color:#222;line-height:1.75;font-family:Georgia,serif;">')

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>The Operating Brief – {date_str}</title></head>
<body style="margin:0;padding:0;background:#f5f4f0;font-family:Georgia,serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f4f0;padding:40px 16px;">
<tr><td align="center">
<table width="620" cellpadding="0" cellspacing="0" style="max-width:620px;width:100%;background:#fff;">

  <!-- Header -->
  <tr><td style="padding:40px 48px 24px;border-bottom:3px solid #111;">
    <p style="margin:0 0 6px;font-size:11px;color:#888;letter-spacing:.15em;text-transform:uppercase;font-family:Arial,sans-serif;">{date_str}</p>
    <h1 style="margin:0;font-size:40px;font-weight:700;color:#111;font-family:Georgia,serif;letter-spacing:-1px;line-height:1;">The Operating Brief</h1>
    <p style="margin:8px 0 0;font-size:13px;color:#555;font-family:Arial,sans-serif;">For Australian business operators</p>
  </td></tr>

  <!-- Briefing -->
  <tr><td style="padding:32px 48px 0;">
    <p style="margin:0 0 20px;font-size:11px;color:#888;letter-spacing:.12em;text-transform:uppercase;font-family:Arial,sans-serif;">Today's Briefing</p>
    {briefing_html}
  </td></tr>

  <tr><td style="padding:0 48px;"><hr style="border:none;border-top:1px solid #ddd;margin:8px 0 32px;"></td></tr>

  <!-- AI -->
  <tr><td style="padding:0 48px 32px;">
    <p style="margin:0 0 20px;font-size:11px;color:#888;letter-spacing:.12em;text-transform:uppercase;font-family:Arial,sans-serif;">AI Stories</p>
    <h2 style="margin:0 0 10px;font-size:14px;font-weight:700;color:#111;text-transform:uppercase;letter-spacing:.08em;font-family:Arial,sans-serif;border-left:3px solid #111;padding-left:10px;">Overview</h2>
    <p style="margin:0 0 24px;font-size:16px;color:#222;line-height:1.75;font-family:Georgia,serif;">{_e(d['ai_overview'])}</p>
    {ai_stories_html}
  </td></tr>

  <tr><td style="padding:0 48px;"><hr style="border:none;border-top:1px solid #ddd;margin:0 0 32px;"></td></tr>

  <!-- Podcasts -->
  <tr><td style="padding:0 48px 32px;">
    <p style="margin:0 0 20px;font-size:11px;color:#888;letter-spacing:.12em;text-transform:uppercase;font-family:Arial,sans-serif;">Podcast Picks</p>
    {podcast_html}
  </td></tr>

  <tr><td style="padding:0 48px;"><hr style="border:none;border-top:1px solid #ddd;margin:0 0 32px;"></td></tr>

  <!-- World -->
  <tr><td style="padding:0 48px 32px;">
    <p style="margin:0 0 20px;font-size:11px;color:#888;letter-spacing:.12em;text-transform:uppercase;font-family:Arial,sans-serif;">World News</p>
    <h2 style="margin:0 0 10px;font-size:14px;font-weight:700;color:#111;text-transform:uppercase;letter-spacing:.08em;font-family:Arial,sans-serif;border-left:3px solid #111;padding-left:10px;">Global Snapshot</h2>
    <p style="margin:0 0 24px;font-size:16px;color:#222;line-height:1.75;font-family:Georgia,serif;">{_e(d['world_overview'])}</p>
    {world_stories_html}
  </td></tr>

  <tr><td style="padding:0 48px;"><hr style="border:none;border-top:1px solid #ddd;margin:0 0 32px;"></td></tr>

  <!-- Australia -->
  <tr><td style="padding:0 48px 32px;">
    <p style="margin:0 0 20px;font-size:11px;color:#888;letter-spacing:.12em;text-transform:uppercase;font-family:Arial,sans-serif;">Australian News</p>
    <h2 style="margin:0 0 10px;font-size:14px;font-weight:700;color:#111;text-transform:uppercase;letter-spacing:.08em;font-family:Arial,sans-serif;border-left:3px solid #111;padding-left:10px;">Australia Snapshot</h2>
    <p style="margin:0 0 24px;font-size:16px;color:#222;line-height:1.75;font-family:Georgia,serif;">{_e(d['aus_overview'])}</p>
    {aus_stories_html}
  </td></tr>

  <!-- Footer -->
  <tr><td style="padding:24px 48px;border-top:2px solid #111;">
    <table width="100%" cellpadding="0" cellspacing="0">
      <tr>
        <td><p style="margin:0;font-size:12px;color:#888;font-family:Arial,sans-serif;">Your daily AI-powered business briefing</p></td>
        <td align="right">
          <a href="mailto:hello@theoperatingbrief.com?subject=Subscribe%20to%20The%20Operating%20Brief" style="font-size:11px;color:#111;font-family:Arial,sans-serif;text-decoration:none;border-bottom:1px solid #111;padding-bottom:1px;margin-right:16px;">Subscribe</a>
          <a href="mailto:hello@theoperatingbrief.com?subject=Unsubscribe%20from%20The%20Operating%20Brief" style="font-size:11px;color:#888;font-family:Arial,sans-serif;text-decoration:none;border-bottom:1px solid #ccc;padding-bottom:1px;">Unsubscribe</a>
        </td>
      </tr>
    </table>
  </td></tr>

</table></td></tr></table>
</body></html>"""


# ---------------------------------------------------------------------------
# Supabase
# ---------------------------------------------------------------------------
def get_supabase():
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])


def load_recipients() -> list[str]:
    sb = get_supabase()
    result = sb.table("subscribers").select("email").eq("active", True).execute()
    emails = [row["email"] for row in result.data]
    print(f"  {len(emails)} active subscriber(s) from Supabase")
    return emails


def log_send(subject: str, recipient_count: int, resend_id: str) -> None:
    try:
        sb = get_supabase()
        sb.table("send_log").insert({
            "subject": subject,
            "recipient_count": recipient_count,
            "resend_id": resend_id,
        }).execute()
    except Exception as ex:
        print(f"  WARN: could not log send: {ex}")


# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------
def send_email(to: list[str], subject: str, html_body: str) -> str:
    resend.api_key = os.environ["RESEND_API_KEY"]
    params: resend.Emails.SendParams = {
        "from": os.environ.get("FROM_EMAIL", "brief@theoperatingbrief.com"),
        "to": to,
        "reply_to": os.environ.get("REPLY_TO_EMAIL", "hello@theoperatingbrief.com"),
        "subject": subject,
        "html": html_body,
    }
    resp = resend.Emails.send(params)
    resend_id = resp.get("id", str(resp))
    print(f"  Email sent! ID: {resend_id}")
    return resend_id


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    date_str = datetime.now(timezone.utc).strftime("%B %d, %Y")
    subject = f"The Operating Brief – {date_str}"

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
    if not recipients:
        print("No active subscribers. Exiting.")
        return

    print(f"  Sending to {len(recipients)} recipient(s)")
    resend_id = send_email(recipients, subject, html_body)
    log_send(subject, len(recipients), resend_id)
    print("Done! ✅")


if __name__ == "__main__":
    main()
