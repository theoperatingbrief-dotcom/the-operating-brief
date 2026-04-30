#!/usr/bin/env python3
import os
import re
import html
import difflib
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

import feedparser
import anthropic
import resend
from dotenv import load_dotenv

load_dotenv()

FEEDS = [
    # AI News
    "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://venturebeat.com/category/ai/feed/",
    "https://hnrss.org/newest?q=AI&points=50",
    # Podcasts
    "https://lexfridman.com/feed/podcast/",
    "https://changelog.com/practicalai/feed",
    "https://feeds.simplecast.com/l2i9YnTd",          # Hard Fork (NYT)
    "https://twimlai.com/feed/",                       # This Week in ML & AI
    # World News
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://feeds.reuters.com/reuters/topNews",
    "https://feeds.npr.org/1001/rss.xml",
    "https://www.theguardian.com/world/rss",
    # Australian News
    "https://www.abc.net.au/news/feed/51120/rss.xml",   # ABC News Australia
    "https://www.smh.com.au/rss/feed.xml",              # Sydney Morning Herald
    "https://www.theguardian.com/australia-news/rss",   # Guardian Australia
    "https://www.afr.com/rss",                          # Australian Financial Review
]

SIMILARITY_THRESHOLD = 0.75


def fetch_recent_entries(feed_url: str, cutoff: datetime) -> list[dict]:
    feed = feedparser.parse(feed_url)
    source = feed.feed.get("title", feed_url)
    entries = []
    for entry in feed.entries:
        published = None
        for attr in ("published", "updated"):
            raw = entry.get(attr)
            if raw:
                try:
                    published = parsedate_to_datetime(raw)
                    if published.tzinfo is None:
                        published = published.replace(tzinfo=timezone.utc)
                    break
                except Exception:
                    pass
        if published is None or published < cutoff:
            continue
        entries.append(
            {
                "title": entry.get("title", "").strip(),
                "url": entry.get("link", ""),
                "source": source,
                "published": published,
            }
        )
    return entries


def deduplicate(entries: list[dict]) -> list[dict]:
    seen_titles: list[str] = []
    unique: list[dict] = []
    for entry in entries:
        title = entry["title"].lower()
        is_dup = any(
            difflib.SequenceMatcher(None, title, seen).ratio() >= SIMILARITY_THRESHOLD
            for seen in seen_titles
        )
        if not is_dup:
            seen_titles.append(title)
            unique.append(entry)
    return unique


def build_prompt(entries: list[dict]) -> str:
    lines = ["Here are the AI news stories from the last 24 hours:\n"]
    for i, e in enumerate(entries, 1):
        lines.append(f"{i}. [{e['source']}] {e['title']}\n   {e['url']}\n")
    lines.append(
        "\nPlease produce a digest with the following structure:\n\n"
        "1. A 3-sentence overview of the day in AI.\n\n"
        "2. The 10 most important stories, each formatted EXACTLY as:\n"
        "STORY: <title>\n"
        "SOURCE: <source>\n"
        "URL: <url>\n"
        "SUMMARY: <2-sentence summary>\n"
        "---\n\n"
        "Focus on significance, novelty, and broad impact when ranking."
    )
    return "".join(lines)


def call_claude(entries: list[dict]) -> str:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    prompt = build_prompt(entries)
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def parse_digest(raw: str) -> tuple[str, list[dict]]:
    # Split overview from stories
    story_block_start = re.search(r"^STORY:", raw, re.MULTILINE)
    if story_block_start:
        overview = raw[: story_block_start.start()].strip()
        stories_raw = raw[story_block_start.start():]
    else:
        overview = raw.strip()
        stories_raw = ""

    stories = []
    for chunk in re.split(r"\n---+\n?", stories_raw):
        chunk = chunk.strip()
        if not chunk:
            continue
        story: dict[str, str] = {}
        for line in chunk.splitlines():
            for key in ("STORY", "SOURCE", "URL", "SUMMARY"):
                if line.startswith(f"{key}:"):
                    story[key.lower()] = line[len(key) + 1:].strip()
        if story.get("story"):
            stories.append(story)

    return overview, stories[:10]


def render_html(overview: str, stories: list[dict], date_str: str) -> str:
    story_html = ""
    for i, s in enumerate(stories, 1):
        title = html.escape(s.get("story", ""))
        source = html.escape(s.get("source", ""))
        url = html.escape(s.get("url", ""))
        summary = html.escape(s.get("summary", ""))
        story_html += f"""
        <div style="margin-bottom:28px; padding-bottom:20px; border-bottom:1px solid #e5e7eb;">
          <p style="margin:0 0 4px 0; font-size:13px; color:#6b7280; text-transform:uppercase; letter-spacing:.05em;">{i}. {source}</p>
          <h2 style="margin:0 0 8px 0; font-size:18px; font-weight:600; color:#111827; line-height:1.4;">
            <a href="{url}" style="color:#1d4ed8; text-decoration:none;">{title}</a>
          </h2>
          <p style="margin:0; font-size:15px; color:#374151; line-height:1.6;">{summary}</p>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>AI News Digest – {date_str}</title>
</head>
<body style="margin:0; padding:0; background:#f3f4f6; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f3f4f6; padding:32px 16px;">
    <tr><td align="center">
      <table width="640" cellpadding="0" cellspacing="0" style="max-width:640px; width:100%; background:#ffffff; border-radius:12px; overflow:hidden; box-shadow:0 2px 8px rgba(0,0,0,.08);">

        <!-- Header -->
        <tr><td style="background:linear-gradient(135deg,#1e3a8a 0%,#1d4ed8 100%); padding:36px 40px;">
          <p style="margin:0 0 4px 0; font-size:12px; color:#93c5fd; text-transform:uppercase; letter-spacing:.1em;">Daily Briefing</p>
          <h1 style="margin:0; font-size:28px; font-weight:700; color:#ffffff;">AI News Digest</h1>
          <p style="margin:8px 0 0 0; font-size:14px; color:#bfdbfe;">{date_str}</p>
        </td></tr>

        <!-- Overview -->
        <tr><td style="padding:32px 40px 24px;">
          <h2 style="margin:0 0 12px 0; font-size:13px; font-weight:600; color:#6b7280; text-transform:uppercase; letter-spacing:.08em;">Today's Overview</h2>
          <p style="margin:0; font-size:16px; color:#1f2937; line-height:1.7; padding:20px; background:#eff6ff; border-left:4px solid #1d4ed8; border-radius:0 8px 8px 0;">{html.escape(overview)}</p>
        </td></tr>

        <!-- Divider -->
        <tr><td style="padding:0 40px;"><hr style="border:none; border-top:1px solid #e5e7eb; margin:0;"></td></tr>

        <!-- Stories -->
        <tr><td style="padding:28px 40px 8px;">
          <h2 style="margin:0 0 24px 0; font-size:13px; font-weight:600; color:#6b7280; text-transform:uppercase; letter-spacing:.08em;">Top 10 Stories</h2>
          {story_html}
        </td></tr>

        <!-- Footer -->
        <tr><td style="padding:24px 40px 32px; background:#f9fafb; border-top:1px solid #e5e7eb;">
          <p style="margin:0; font-size:13px; color:#9ca3af; text-align:center;">Generated by AI News Digest &middot; Powered by Claude &amp; Resend</p>
        </td></tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""


def load_recipients(path: str = "recipients.txt") -> list[str]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Recipients file not found: {path}")
    recipients = []
    with open(path) as f:
        for line in f:
            addr = line.strip()
            if addr and not addr.startswith("#"):
                recipients.append(addr)
    if not recipients:
        raise ValueError("No recipients found in recipients.txt")
    return recipients


def send_email(to: list[str], subject: str, html_body: str) -> None:
    resend.api_key = os.environ["RESEND_API_KEY"]
    from_addr = os.environ.get("FROM_EMAIL", "AI Digest <digest@yourdomain.com>")
    params: resend.Emails.SendParams = {
        "from": from_addr,
        "to": to,
        "subject": subject,
        "html": html_body,
    }
    resp = resend.Emails.send(params)
    print(f"Email sent. ID: {resp.get('id', resp)}")


def main() -> None:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    date_str = datetime.now(timezone.utc).strftime("%B %d, %Y")
    subject = f"AI News Digest – {date_str}"

    print("Fetching RSS feeds…")
    all_entries: list[dict] = []
    for url in FEEDS:
        try:
            entries = fetch_recent_entries(url, cutoff)
            print(f"  {url}: {len(entries)} stories")
            all_entries.extend(entries)
        except Exception as e:
            print(f"  WARNING: failed to fetch {url}: {e}")

    if not all_entries:
        print("No stories found in the last 24 hours. Exiting.")
        return

    print(f"Deduplicating {len(all_entries)} stories…")
    unique = deduplicate(all_entries)
    print(f"  {len(unique)} unique stories after deduplication")

    print("Calling Claude for digest…")
    raw = call_claude(unique)

    overview, stories = parse_digest(raw)
    print(f"  Digest ready: {len(stories)} top stories")

    recipients = load_recipients()
    html_body = render_html(overview, stories, date_str)

    print(f"Sending email to {len(recipients)} recipient(s)…")
    send_email(recipients, subject, html_body)
    print("Done.")


if __name__ == "__main__":
    main()
