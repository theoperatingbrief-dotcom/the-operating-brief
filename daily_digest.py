#!/usr/bin/env python3
"""
Daily AI & News Digest
Uses the local `claude` CLI for summarisation — no API key needed.
Sends via Resend. Run locally or via launchd at 7am weekdays.
"""
import os
import re
import sys
import html
import time
import difflib
import subprocess
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
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
        "https://www.technologyreview.com/feed/",
        "https://arstechnica.com/ai/feed/",
        "https://www.zdnet.com/topic/artificial-intelligence/rss.xml",
    ],
    "podcast": [
        "https://lexfridman.com/feed/podcast/",
        "https://twimlai.com/feed/",
        "https://anchor.fm/s/f7cac464/podcast/rss",   # The AI Daily Brief
        "https://feeds.megaphone.fm/nopriors",         # No Priors
        "https://feeds.megaphone.fm/RINTP3108857801",  # The Cognitive Revolution
        "https://api.substack.com/feed/podcast/1084089.rss",  # Latent Space
        "https://changelog.com/practicalai/feed",     # Practical AI
    ],
    "world": [
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "https://feeds.reuters.com/reuters/topNews",
        "https://www.theguardian.com/world/rss",
        "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
        "https://feeds.a.dj.com/rss/RSSWorldNews.xml",
        "https://feeds.skynews.com/feeds/rss/world.xml",
        "https://feeds.npr.org/1004/rss.xml",
    ],
    "australia": [
        "https://www.abc.net.au/news/feed/51120/rss.xml",
        "https://www.smh.com.au/rss/feed.xml",
        "https://www.theguardian.com/australia-news/rss",
        "https://www.afr.com/rss/feed.xml",
        "https://www.news.com.au/content-feeds/latest-news-national/",
        "https://7news.com.au/news/australia/rss",
        "https://www.abc.net.au/news/feed/45910/rss.xml",
        "https://www.rba.gov.au/rss/rss-cb-speeches.xml",        # RBA speeches
        "https://www.rba.gov.au/rss/rss-cb-media-releases.xml",  # RBA media releases
    ],
}

SIMILARITY_THRESHOLD = 0.75

# Weekly feeds — fetched on Mondays only with a 7-day lookback.
# These cover major tech/enterprise companies whose AI announcements matter
# but don't need daily monitoring. See SOURCES.md for the full source list.
WEEKLY_FEEDS = {
    "bigtech": [
        "https://news.microsoft.com/feed/",                        # Microsoft News
        "https://blogs.microsoft.com/ai/feed/",                    # Microsoft AI Blog
        "https://www.apple.com/newsroom/rss-feed.xml",             # Apple Newsroom
        "https://ai.meta.com/blog/rss/",                           # Meta AI Blog
        "https://about.fb.com/news/feed/",                         # Meta Newsroom
        "https://aws.amazon.com/blogs/aws/feed/",                  # Amazon AWS
        "https://www.aboutamazon.com/news/rss",                    # Amazon Newsroom
        "https://blog.google/technology/ai/rss/",                  # Google AI Blog
        "https://deepmind.google/blog/rss/",                       # Google DeepMind
        "https://blogs.oracle.com/rss",                            # Oracle Blog
        "https://blog.workday.com/en-us/feed.xml",                 # Workday Blog
        "https://www.salesforce.com/news/feed/",                   # Salesforce News
        "https://news.sap.com/feed/",                              # SAP News
    ],
}


# ---------------------------------------------------------------------------
# Fetch & deduplicate
# ---------------------------------------------------------------------------
def fetch_entries(feeds: dict) -> dict:
    now = datetime.now(timezone.utc)
    is_monday = now.weekday() == 0
    base_hours = 72 if is_monday else 24
    cutoff_base = now - timedelta(hours=base_hours)
    cutoff_podcast = now - timedelta(hours=max(base_hours, 48))
    cutoff_weekly = now - timedelta(days=7)

    all_feeds = dict(feeds)
    if is_monday:
        all_feeds.update(WEEKLY_FEEDS)

    results = {k: [] for k in all_feeds}

    for cat, urls in all_feeds.items():
        if cat == "podcast":
            cutoff = cutoff_podcast
        elif cat in WEEKLY_FEEDS:
            cutoff = cutoff_weekly
        else:
            cutoff = cutoff_base
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
def build_prompt(entries: dict, recent_topics: list[str] | None = None) -> str:
    recent_block = ""
    if recent_topics:
        topic_list = "\n".join(f"- {t}" for t in recent_topics[:30])
        recent_block = (
            f"ALREADY COVERED IN RECENT EDITIONS — do not repeat these topics or stories:\n{topic_list}\n"
            "If today's stories overlap with the above, skip them and prioritise fresh stories instead.\n\n"
        )
    lines = [
        "You are producing a daily news digest for Australian business operators.",
        recent_block,
        "Based on the stories below, produce output in EXACTLY this format — no extra text:\n",

        "BRIEFING_START",
        "Write a 600-word briefing with four bold headings: **AI & Technology**, **Australian Business & Finance**, **World Markets & Global Business**, **The Big Picture**.",
        "Tone: sharp, punchy, no jargon, short sentences, active voice. Every sentence must earn its place — no padding.",
        "No stage directions, no script labels. Flow as clean readable prose.",
        "IMPORTANT: Group related sentences into paragraphs of 2-4 sentences. Separate each paragraph with a blank line. Do not put every sentence on its own line.",
        "End with 1 sentence pointing readers to the full digest below.",
        "BRIEFING_END\n",

        "WTMFY_START",
        "Write 1 short paragraph (max 50 words). Do NOT include a label or heading — start directly with the insight.",
        "Audience: time-poor Australian white-collar workers worried about AI and cost of living.",
        "Tone: empowering and reassuring — like a smart friend translating today's news into one practical thing they should know or do.",
        "Draw from the most relevant story in today's digest. No jargon. Plain language only.",
        "WTMFY_END\n",

        "THE_NUMBER_START",
        "STAT: <the number only — short and punchy, max 4 words. Examples: '$900 million', '1 in 3', '47%', '$2.4 trillion'. NO full sentences. Just the figure.>",
        "CONTEXT: <one sentence explaining what this number is and why it matters to an Australian worker or household>",
        "THE_NUMBER_END\n",

        "SUBJECT_LINE_START",
        "Write one email subject line (max 55 characters) that would make a time-poor Australian open this email.",
        "Lead with the most compelling number or fact from today's stories. No clickbait. No exclamation marks.",
        "Format: <stat or hook> | The Operating Brief",
        "SUBJECT_LINE_END\n",

        "SOCIAL_CAPTION_START",
        "Write an Instagram/LinkedIn caption to accompany The Number card from today's digest.",
        "LINE1: <one punchy sentence using the stat — make the reader feel something>",
        "LINE2: <one sentence of Australian context — why does this matter here>",
        "LINE3: <one question directed at the reader — make it conversational, not rhetorical>",
        "CTA: Read the full brief at theoperatingbrief.com",
        "HASHTAGS: <10 hashtags — mix of Australian professional, AI, cost of living, and current affairs. e.g. #Australia #AINews #FutureOfWork #AustralianBusiness #AI #CostOfLiving #NRL #AFL #TechNews #TheOperatingBrief>",
        "SOCIAL_CAPTION_END\n",

        "AI_OVERVIEW_START",
        "2-3 sentences covering the most important AI developments today. Put each sentence on its own line.",
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
        "2-3 sentences covering the most important global stories today. Put each sentence on its own line.",
        "WORLD_OVERVIEW_END\n",

        "Then for the 3 most important world stories:",
        "WORLD_STORY_START",
        "TITLE: <title>",
        "SOURCE: <source>",
        "URL: <url>",
        "SUMMARY: <2 sentences>",
        "WORLD_STORY_END\n",

        "AUS_OVERVIEW_START",
        "2-3 sentences covering the most important Australian stories today. Put each sentence on its own line.",
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

    if "bigtech" in entries:
        lines += [
            "BIGTECH_OVERVIEW_START",
            "2-3 sentences covering the most important big-tech AI moves this week. Put each sentence on its own line.",
            "BIGTECH_OVERVIEW_END\n",
            "Then for up to 3 big-tech stories (Microsoft/Apple/Meta/Amazon/Google/Oracle/Workday/Salesforce/SAP), each:",
            "BIGTECH_STORY_START",
            "TITLE: <title>",
            "SOURCE: <source>",
            "TAG: <one of: Product Launch | Earnings | Partnership | Research | Strategy>",
            "URL: <url>",
            "SUMMARY: <2 sentences>",
            "BIGTECH_STORY_END\n",
        ]

    limits = {"ai": 15, "podcast": 3, "world": 12, "australia": 12, "bigtech": 20}
    for cat, items in entries.items():
        lines.append(f"--- {cat.upper()} ---")
        for item in items[:limits.get(cat, 12)]:
            lines.append(f"[{item['source']}] {item['title']}")
            lines.append(f"  {item['url']}")
        lines.append("")

    return "\n".join(lines)


def call_claude(prompt: str, retries: int = 3, timeout: int = 180) -> str:
    """Call the claude CLI, passing prompt via stdin."""
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    home = os.path.expanduser("~")

    for attempt in range(1, retries + 1):
        print(f"  Calling claude CLI (attempt {attempt}/{retries})...")
        try:
            result = subprocess.run(
                ["claude", "-p", "-", "--allowedTools", ""],
                input=prompt,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=timeout,
                env=env,
                cwd=home,
            )
            if result.returncode != 0:
                raise RuntimeError(f"claude CLI error (rc={result.returncode})")
            return result.stdout
        except subprocess.TimeoutExpired:
            print(f"  WARN: claude timed out after {timeout}s on attempt {attempt}")
            if attempt == retries:
                raise RuntimeError(f"claude CLI timed out after {retries} attempts")

    raise RuntimeError("claude CLI failed")


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
            for key in ("TITLE", "SOURCE", "TAG", "URL", "SUMMARY", "SHOW", "STAT", "CONTEXT", "LINE1", "LINE2", "LINE3", "CTA", "HASHTAGS"):
                if line.startswith(f"{key}:"):
                    item[key.lower()] = line[len(key)+1:].strip()
        if item:
            items.append(item)
    return items


def parse_response(raw: str) -> dict:
    the_number_block = _extract_blocks(raw, "THE_NUMBER")
    the_number = the_number_block[0] if the_number_block else {}
    social_block = _extract_blocks(raw, "SOCIAL_CAPTION")
    social = social_block[0] if social_block else {}
    return {
        "briefing":              _extract(raw, "BRIEFING"),
        "wtmfy":                 re.sub(r'^\*?\*?What This Means For You\*?\*?:?\s*', '', _extract(raw, "WTMFY"), flags=re.IGNORECASE),
        "the_number_stat":       the_number.get("stat", ""),
        "the_number_context":    the_number.get("context", ""),
        "subject_line":          _extract(raw, "SUBJECT_LINE"),
        "social_line1":          social.get("line1", ""),
        "social_line2":          social.get("line2", ""),
        "social_line3":          social.get("line3", ""),
        "social_cta":            social.get("cta", "Read the full brief at theoperatingbrief.com"),
        "social_hashtags":       social.get("hashtags", ""),
        "ai_overview":           _extract(raw, "AI_OVERVIEW"),
        "ai_stories":       _extract_blocks(raw, "AI_STORY"),
        "podcasts":         _extract_blocks(raw, "PODCAST"),
        "world_overview":   _extract(raw, "WORLD_OVERVIEW"),
        "world_stories":    _extract_blocks(raw, "WORLD_STORY"),
        "aus_overview":     _extract(raw, "AUS_OVERVIEW"),
        "aus_stories":      _extract_blocks(raw, "AUS_STORY"),
        "bigtech_overview": _extract(raw, "BIGTECH_OVERVIEW"),
        "bigtech_stories":  _extract_blocks(raw, "BIGTECH_STORY"),
    }


# ---------------------------------------------------------------------------
# HTML rendering
# ---------------------------------------------------------------------------
def _e(s: str) -> str:
    return html.escape(s or "")


def _paras(text: str, style: str = 'margin:0 0 16px;font-size:16px;color:#222;line-height:1.75;font-family:Georgia,serif;') -> str:
    """Render multi-line text as individual <p> tags, one per paragraph."""
    paras = [p.strip() for p in re.split(r'\n{2,}', (text or "").strip()) if p.strip()]
    return "".join(f'<p style="{style}">{_e(p)}</p>' for p in paras)


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
    bigtech_html = ""
    if d.get("bigtech_stories"):
        bigtech_cards = "".join(_story_card(i+1, s) for i, s in enumerate(d["bigtech_stories"][:3]))
        bigtech_html = f"""
  <tr><td style="padding:0 48px;"><hr style="border:none;border-top:1px solid #ddd;margin:0 0 32px;"></td></tr>

  <!-- Big Tech Weekly -->
  <tr><td style="padding:0 48px 32px;">
    <p style="margin:0 0 4px;font-size:11px;color:#888;letter-spacing:.12em;text-transform:uppercase;font-family:Arial,sans-serif;">Big Tech · Weekly Wrap</p>
    <h2 style="margin:0 0 10px;font-size:14px;font-weight:700;color:#111;text-transform:uppercase;letter-spacing:.08em;font-family:Arial,sans-serif;border-left:3px solid #111;padding-left:10px;">This Week in Big Tech</h2>
    {_paras(d['bigtech_overview'], 'margin:0 0 14px;font-size:16px;color:#222;line-height:1.75;font-family:Georgia,serif;')}
    {bigtech_cards}
  </td></tr>"""

    # Convert **Heading** to styled section headers, then paragraphs
    briefing_raw = d["briefing"]
    briefing_raw = re.sub(
        r'\*\*(.+?)\*\*',
        r'</p><h3 style="margin:24px 0 8px;font-size:14px;font-weight:700;color:#111;text-transform:uppercase;letter-spacing:.08em;font-family:Arial,sans-serif;border-left:3px solid #111;padding-left:10px;">\1</h3><p style="margin:0 0 16px;font-size:16px;color:#222;line-height:1.75;font-family:Georgia,serif;">',
        briefing_raw
    )
    p_style = 'margin:0 0 16px;font-size:16px;color:#222;line-height:1.75;font-family:Georgia,serif;'
    paras = [p.strip() for p in re.split(r'\n{2,}', briefing_raw.strip()) if p.strip()]
    briefing_html = "".join(f'<p style="{p_style}">{p}</p>' for p in paras)

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

  <!-- What This Means For You -->
  <tr><td style="padding:0 48px 32px;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f4f0;border-left:3px solid #111;">
      <tr><td style="padding:20px 24px;">
        <p style="margin:0 0 6px;font-size:11px;color:#888;letter-spacing:.12em;text-transform:uppercase;font-family:Arial,sans-serif;">What This Means For You</p>
        <p style="margin:0;font-size:16px;color:#222;line-height:1.75;font-family:Georgia,serif;">{_e(d['wtmfy'])}</p>
      </td></tr>
    </table>
  </td></tr>

  <tr><td style="padding:0 48px;"><hr style="border:none;border-top:1px solid #ddd;margin:8px 0 32px;"></td></tr>

  <!-- AI -->
  <tr><td style="padding:0 48px 32px;">
    <p style="margin:0 0 20px;font-size:11px;color:#888;letter-spacing:.12em;text-transform:uppercase;font-family:Arial,sans-serif;">AI Stories</p>
    <h2 style="margin:0 0 10px;font-size:14px;font-weight:700;color:#111;text-transform:uppercase;letter-spacing:.08em;font-family:Arial,sans-serif;border-left:3px solid #111;padding-left:10px;">Overview</h2>
    {_paras(d['ai_overview'], 'margin:0 0 14px;font-size:16px;color:#222;line-height:1.75;font-family:Georgia,serif;')}
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
    {_paras(d['world_overview'], 'margin:0 0 14px;font-size:16px;color:#222;line-height:1.75;font-family:Georgia,serif;')}
    {world_stories_html}
  </td></tr>

  <tr><td style="padding:0 48px;"><hr style="border:none;border-top:1px solid #ddd;margin:0 0 32px;"></td></tr>

  <!-- Australia -->
  <tr><td style="padding:0 48px 32px;">
    <p style="margin:0 0 20px;font-size:11px;color:#888;letter-spacing:.12em;text-transform:uppercase;font-family:Arial,sans-serif;">Australian News</p>
    <h2 style="margin:0 0 10px;font-size:14px;font-weight:700;color:#111;text-transform:uppercase;letter-spacing:.08em;font-family:Arial,sans-serif;border-left:3px solid #111;padding-left:10px;">Australia Snapshot</h2>
    {_paras(d['aus_overview'], 'margin:0 0 14px;font-size:16px;color:#222;line-height:1.75;font-family:Georgia,serif;')}
    {aus_stories_html}
  </td></tr>
  {bigtech_html}

  <!-- The Number -->
  <tr><td style="padding:0 48px 32px;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background:#111;">
      <tr><td style="padding:28px 32px;" align="left">
        <p style="margin:0 0 4px;font-size:11px;color:#888;letter-spacing:.15em;text-transform:uppercase;font-family:Arial,sans-serif;">The Number</p>
        <p style="margin:0 0 8px;font-size:42px;font-weight:700;color:#fff;font-family:Georgia,serif;line-height:1.1;">{_e(d['the_number_stat'])}</p>
        <p style="margin:0;font-size:14px;color:#ccc;line-height:1.6;font-family:Arial,sans-serif;">{_e(d['the_number_context'])}</p>
      </td></tr>
    </table>
  </td></tr>

  <!-- Also from us -->
  <tr><td style="padding:0 48px 32px;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f4f0;border-left:3px solid #111;">
      <tr><td style="padding:20px 24px;">
        <p style="margin:0 0 12px;font-size:11px;color:#888;letter-spacing:.12em;text-transform:uppercase;font-family:Arial,sans-serif;">Also from The Operating Brief</p>
        <table width="100%" cellpadding="0" cellspacing="0">
          <tr>
            <td width="48%" style="vertical-align:top;padding-right:12px;">
              <p style="margin:0 0 2px;font-size:13px;font-weight:700;color:#111;font-family:Arial,sans-serif;"><a href="https://theoperatingbrief.com/markets" style="color:#111;text-decoration:none;">The Markets Brief</a></p>
              <p style="margin:0;font-size:12px;color:#666;font-family:Arial,sans-serif;line-height:1.5;">Daily ASX pre-market briefing — live market data, overnight moves, and the macro stories that matter. In your inbox by 7:30am.</p>
            </td>
            <td width="4%"></td>
            <td width="48%" style="vertical-align:top;">
              <p style="margin:0 0 2px;font-size:13px;font-weight:700;color:#111;font-family:Arial,sans-serif;"><a href="https://theoperatingbrief.com/sporting" style="color:#111;text-decoration:none;">The Sporting Brief</a></p>
              <p style="margin:0;font-size:12px;color:#666;font-family:Arial,sans-serif;line-height:1.5;">Twice weekly — NRL, AFL, football, F1, NBA, golf and more. Weekend preview Thursdays, results wrap Mondays.</p>
            </td>
          </tr>
        </table>
      </td></tr>
    </table>
  </td></tr>

  <!-- Footer -->
  <tr><td style="padding:24px 48px;border-top:2px solid #111;">
    <p style="margin:0 0 16px;font-size:14px;color:#222;font-family:Georgia,serif;line-height:1.7;">
      Enjoying the brief? Forward it to one person who'd find it useful.<br>
      And if someone sent this your way — <a href="https://theoperatingbrief.com" style="color:#111;text-decoration:none;border-bottom:1px solid #111;padding-bottom:1px;">subscribe here and we'll see you tomorrow.</a>
    </p>
    <p style="margin:0 0 16px;font-size:13px;color:#222;font-family:Georgia,serif;line-height:1.6;">
      Thoughts on today's edition? Hit reply — we read every response.
    </p>
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


def fetch_previously_sent_urls(days: int = 1) -> set[str]:
    """Return all article URLs that appeared in the last `days` editions."""
    try:
        sb = get_supabase()
        aest = ZoneInfo("Australia/Sydney")
        slugs = [
            (datetime.now(aest) - timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range(1, days + 1)
        ]
        result = sb.table("editions").select("html").in_("slug", slugs).execute()
        urls: set[str] = set()
        for row in result.data or []:
            urls.update(re.findall(r'href="(https?://[^"]+)"', row.get("html") or ""))
        print(f"  Loaded {len(urls)} URLs from previous {days} edition(s) for dedup")
        return urls
    except Exception as ex:
        print(f"  WARN: could not fetch previous editions for dedup: {ex}")
        return set()


def fetch_recently_covered_topics(days: int = 3) -> list[str]:
    """Return story titles from the last N editions to prevent topic repetition."""
    try:
        sb = get_supabase()
        aest = ZoneInfo("Australia/Sydney")
        slugs = [
            (datetime.now(aest) - timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range(1, days + 1)
        ]
        result = sb.table("editions").select("html").in_("slug", slugs).execute()
        titles = []
        for row in result.data or []:
            html = row.get("html") or ""
            found = re.findall(r'<h3[^>]*>([^<]{10,})</h3>|data-title="([^"]{10,})"', html)
            for t1, t2 in found:
                t = (t1 or t2).strip()
                if t:
                    titles.append(t)
            # Also extract from anchor text in story links
            found2 = re.findall(r'<a [^>]*class="[^"]*story[^"]*"[^>]*>([^<]{15,})</a>', html)
            titles.extend(t.strip() for t in found2 if t.strip())
        print(f"  Loaded {len(titles)} recent story titles for topic dedup")
        return titles
    except Exception as ex:
        print(f"  WARN: could not fetch recent topics: {ex}")
        return []


def filter_seen_entries(entries: dict, seen_urls: set[str]) -> dict:
    """Remove entries whose URL was in a previously sent edition."""
    if not seen_urls:
        return entries
    filtered = {}
    removed = 0
    for cat, items in entries.items():
        kept = [e for e in items if e["url"] not in seen_urls]
        removed += len(items) - len(kept)
        filtered[cat] = kept
    print(f"  Removed {removed} duplicate story/stories already sent in a previous edition")
    return filtered


def load_recipients() -> list[dict]:
    sb = get_supabase()
    result = sb.table("subscribers").select("email,token").eq("active", True).execute()
    print(f"  {len(result.data)} active subscriber(s) from Supabase")
    return result.data  # list of {email, token}


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


def save_edition(slug: str, subject: str, preview_text: str, html_body: str) -> None:
    try:
        sb = get_supabase()
        sb.table("editions").upsert({
            "slug": slug,
            "subject": subject,
            "preview_text": preview_text,
            "html": html_body,
        }, on_conflict="slug").execute()
        print(f"  Edition saved to archive: {slug}")
    except Exception as ex:
        print(f"  WARN: could not save edition: {ex}")


# ---------------------------------------------------------------------------
# Social image — The Number card
# ---------------------------------------------------------------------------
def generate_number_image(stat: str, context: str) -> str | None:
    if not stat:
        return None
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("  WARN: Pillow not installed — skipping image. Run: pip install Pillow")
        return None

    W, H = 1080, 1080
    img = Image.new("RGB", (W, H), color="#111111")
    draw = ImageDraw.Draw(img)

    font_dir = "/System/Library/Fonts/Supplemental"
    def font(name, size):
        path = os.path.join(font_dir, name)
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            return ImageFont.load_default()

    label_font   = font("Arial.ttf", 22)
    context_font = font("Georgia.ttf", 34)
    brand_font   = font("Arial.ttf", 20)

    def wrap_text(text, f, max_width):
        words = text.split()
        lines, current = [], []
        for word in words:
            test = " ".join(current + [word])
            if draw.textbbox((0, 0), test, font=f)[2] > max_width:
                if current:
                    lines.append(" ".join(current))
                current = [word]
            else:
                current.append(word)
        if current:
            lines.append(" ".join(current))
        return lines

    # Find the largest font size where the stat wraps to 3 lines or fewer
    stat_size = 160
    stat_font = font("Georgia Bold.ttf", stat_size)
    stat_lines = []
    while stat_size >= 48:
        stat_lines = wrap_text(stat, stat_font, W - 140)
        if len(stat_lines) <= 3:
            break
        stat_size -= 8
        stat_font = font("Georgia Bold.ttf", stat_size)

    # Label
    draw.text((W // 2, 180), "THE NUMBER", font=label_font, fill="#888888", anchor="mm")
    draw.line([(W // 2 - 60, 216), (W // 2 + 60, 216)], fill="#333333", width=1)

    # Stat — vertically centred as a block
    stat_line_h = stat_size + 12
    stat_block_h = len(stat_lines) * stat_line_h
    stat_y = H // 2 - stat_block_h // 2
    for line in stat_lines:
        draw.text((W // 2, stat_y), line, font=stat_font, fill="#ffffff", anchor="mm")
        stat_y += stat_line_h

    # Context — word-wrap below stat block
    context_lines = wrap_text(context, context_font, W - 140)
    y = H // 2 + stat_block_h // 2 + 32
    for line in context_lines:
        draw.text((W // 2, y), line, font=context_font, fill="#cccccc", anchor="mm")
        y += 52

    # Branding
    draw.text((W // 2, H - 100), "theoperatingbrief.com", font=brand_font, fill="#555555", anchor="mm")

    images_dir = os.path.join(os.path.dirname(__file__), "social_images")
    os.makedirs(images_dir, exist_ok=True)
    slug = datetime.now(ZoneInfo("Australia/Sydney")).strftime("%Y-%m-%d")
    image_path = os.path.join(images_dir, f"{slug}_the_number.png")
    img.save(image_path, "PNG")
    print(f"  Number image saved → {image_path}")
    return image_path


# ---------------------------------------------------------------------------
# PDF export
# ---------------------------------------------------------------------------
def generate_pdf(html_body: str) -> str | None:
    try:
        from weasyprint import HTML
    except (ImportError, OSError) as e:
        print(f"  WARN: PDF skipped — WeasyPrint unavailable ({e}). Run: brew install pango && pip install weasyprint")
        return None
    pdfs_dir = os.path.join(os.path.dirname(__file__), "pdfs")
    os.makedirs(pdfs_dir, exist_ok=True)
    slug = datetime.now(ZoneInfo("Australia/Sydney")).strftime("%Y-%m-%d")
    pdf_path = os.path.join(pdfs_dir, f"{slug}.pdf")
    HTML(string=html_body).write_pdf(pdf_path)
    print(f"  PDF saved → {pdf_path}")
    return pdf_path


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
    print(f"    Sent → {resend_id}")
    return resend_id


def send_to_all(subscribers: list[dict], subject: str, base_html: str) -> list[str]:
    """Send individual emails with personalised unsubscribe links."""
    resend_ids = []
    for sub in subscribers:
        token = sub.get("token", "")
        email = sub["email"]
        unsub_url = f"https://theoperatingbrief.com/unsubscribe?token={token}"
        sub_url = "https://theoperatingbrief.com"
        personalised = base_html.replace(
            'href="mailto:hello@theoperatingbrief.com?subject=Subscribe%20to%20The%20Operating%20Brief"',
            f'href="{sub_url}"'
        ).replace(
            'href="mailto:hello@theoperatingbrief.com?subject=Unsubscribe%20from%20The%20Operating%20Brief"',
            f'href="{unsub_url}"'
        )
        resend_id = send_email([email], subject, personalised)
        resend_ids.append(resend_id)
        time.sleep(0.6)  # stay under Resend's 2 req/s limit
    return resend_ids


# ---------------------------------------------------------------------------
# Quality checks
# ---------------------------------------------------------------------------
def quality_check(digest: dict, entries: dict) -> list[str]:
    warnings = []
    if not digest.get("podcasts"):
        warnings.append("⚠️  No podcast episodes found")
    if not digest.get("ai_stories"):
        warnings.append("⚠️  No AI stories parsed")
    if not digest.get("world_stories"):
        warnings.append("⚠️  No world stories parsed")
    if not digest.get("aus_stories"):
        warnings.append("⚠️  No Australian stories parsed")
    if not digest.get("briefing"):
        warnings.append("⚠️  Main briefing is missing")
    if len(digest.get("briefing", "")) < 200:
        warnings.append("⚠️  Main briefing looks too short")
    if not digest.get("wtmfy"):
        warnings.append("⚠️  'What This Means For You' section is missing")
    if not digest.get("the_number_stat"):
        warnings.append("⚠️  'The Number' stat is missing")
    if not digest.get("ai_overview"):
        warnings.append("⚠️  AI overview is missing")
    return warnings


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    import argparse, webbrowser
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", action="store_true", help="Generate email, run quality checks, open in browser. Does not send.")
    parser.add_argument("--send", action="store_true", help="Send the last generated preview to all subscribers without regenerating.")
    args = parser.parse_args()

    aest = ZoneInfo("Australia/Sydney")
    date_str = datetime.now(aest).strftime("%B %d, %Y")
    subject = f"The Operating Brief – {date_str}"
    preview_path = os.path.join(os.path.dirname(__file__), "preview_latest.html")
    subject_path = os.path.join(os.path.dirname(__file__), "preview_subject.txt")

    if args.send:
        if not os.path.exists(preview_path):
            print("No preview found. Run --preview first.")
            return
        with open(preview_path) as f:
            html_body = f.read()
        # Strip the social assets panel (preview-only, not for subscribers)
        html_body = re.sub(r'<div style="background:#222.*?</div>', '', html_body, flags=re.DOTALL)
        if os.path.exists(subject_path):
            with open(subject_path) as f:
                subject = f.read().strip() or subject
        print(f"  Subject: {subject}")
        print("Saving edition to archive…")
        slug = datetime.now(aest).strftime("%Y-%m-%d")
        save_edition(slug, subject, "", html_body)
        print("Generating PDF…")
        generate_pdf(html_body)
        print("Loading recipients…")
        recipients = load_recipients()
        if not recipients:
            print("No active subscribers. Exiting.")
            return
        print(f"  Sending to {len(recipients)} recipient(s)")
        resend_ids = send_to_all(recipients, subject, html_body)
        log_send(subject, len(recipients), resend_ids[0] if resend_ids else "")
        print("Done! ✅")
        return

    print("Fetching RSS feeds…")
    entries = fetch_entries(FEEDS)

    print("Filtering stories already sent in previous editions…")
    seen_urls = fetch_previously_sent_urls(days=1)
    entries = filter_seen_entries(entries, seen_urls)
    recent_topics = fetch_recently_covered_topics(days=3)

    total = sum(len(v) for v in entries.values())
    print(f"  {total} stories total after deduplication")

    if total == 0:
        print("No stories found. Exiting.")
        return

    print("Summarising with Claude…")
    prompt = build_prompt(entries, recent_topics=recent_topics)
    raw = call_claude(prompt)

    print("Parsing response…")
    digest = parse_response(raw)

    subject = digest.get("subject_line") or subject

    with open(subject_path, "w") as f:
        f.write(subject)
    print(f"  Subject: {subject}")

    print("Rendering HTML…")
    html_body = render_html(digest, date_str)

    with open(preview_path, "w") as f:
        f.write(html_body)

    social_path = os.path.join(os.path.dirname(__file__), "social_caption.txt")
    with open(social_path, "w") as f:
        f.write(f"THE NUMBER: {digest.get('the_number_stat', '')}\n\n")
        f.write(f"{digest.get('social_line1', '')}\n\n")
        f.write(f"{digest.get('social_line2', '')}\n\n")
        f.write(f"{digest.get('social_line3', '')}\n\n")
        f.write(f"{digest.get('social_cta', '')}\n\n")
        f.write(f"{digest.get('social_hashtags', '')}\n")
    print(f"  Social caption saved → {social_path}")

    print("Generating Number image…")
    image_path = generate_number_image(digest.get("the_number_stat", ""), digest.get("the_number_context", ""))

    if image_path and os.path.exists(image_path):
        import base64
        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()
        caption_lines = "\n".join(filter(None, [
            digest.get("social_line1", ""),
            digest.get("social_line2", ""),
            digest.get("social_line3", ""),
            digest.get("social_cta", ""),
            digest.get("social_hashtags", ""),
        ]))
        social_panel = f"""
<div style="background:#222;padding:40px 0;margin-top:0;">
  <div style="max-width:620px;margin:0 auto;padding:0 16px;">
    <p style="font-size:11px;letter-spacing:.15em;text-transform:uppercase;color:#666;font-family:Arial,sans-serif;margin:0 0 20px;">Preview only — Social Assets</p>
    <img src="data:image/png;base64,{img_b64}" style="width:100%;max-width:400px;display:block;margin:0 auto 24px;" alt="The Number card">
    <pre style="font-family:Arial,sans-serif;font-size:13px;color:#ccc;line-height:1.8;white-space:pre-wrap;margin:0;background:#333;padding:20px;">{html.escape(caption_lines)}</pre>
  </div>
</div>"""
        preview_html = html_body.replace("</body>", social_panel + "</body>")
        with open(preview_path, "w") as f:
            f.write(preview_html)

    print("\n── Quality Check ───────────────────────────────")
    warnings = quality_check(digest, entries)
    if warnings:
        for w in warnings:
            print(w)
    else:
        print("✅  All checks passed")
    print("────────────────────────────────────────────────\n")

    if args.preview:
        print("Saving draft to Supabase…")
        save_edition("draft", subject, digest.get("ai_overview", "")[:120], html_body)
        print(f"Preview saved → {preview_path}")
        print(f"  Web preview: https://theoperatingbrief.com/preview/{os.environ.get('PREVIEW_TOKEN', '<PREVIEW_TOKEN>')}")
        if not sys.stdin.isatty():
            print("Running unattended — draft saved. Approve and send from the web preview.")
            return
        webbrowser.open(f"file://{preview_path}")
        print("\nReview the email, then approve from the web preview or type y here.\n")
        answer = input("Send to subscribers now? (y/n): ").strip().lower()
        if answer != "y":
            print("Not sent. Approve from the web preview whenever you're ready.")
            return
        args.send = True

    print("Saving edition to archive…")
    slug = datetime.now(aest).strftime("%Y-%m-%d")
    preview_text = digest.get("ai_overview", "")[:120]
    save_edition(slug, subject, preview_text, html_body)

    print("Generating PDF…")
    generate_pdf(html_body)

    print("Loading recipients…")
    recipients = load_recipients()
    if not recipients:
        print("No active subscribers. Exiting.")
        return

    print(f"  Sending to {len(recipients)} recipient(s)")
    resend_ids = send_to_all(recipients, subject, html_body)
    log_send(subject, len(recipients), resend_ids[0] if resend_ids else "")
    print("Done! ✅")


if __name__ == "__main__":
    main()
