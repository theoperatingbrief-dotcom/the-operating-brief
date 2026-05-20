#!/usr/bin/env python3
"""
Federal Budget Special — one-time edition.
Fetches budget news, analyses with Claude, sends to all active subscribers
across The Operating Brief and The Markets Brief.

Usage:
  python3 budget_brief.py --preview   # generate + open browser + y/n prompt
  python3 budget_brief.py --send      # send the saved preview_budget.html
"""
import os
import re
import html
import difflib
import subprocess
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from email.utils import parsedate_to_datetime

import time
import requests
from bs4 import BeautifulSoup
import feedparser
import resend
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SIMILARITY_THRESHOLD = 0.75

# Direct articles to fetch and inject as named sources (not RSS)
DIRECT_ARTICLES = [
    {
        "url": "https://business.nab.com.au/tag/federal-budget/2026-federal-budget--what-it-means-for-regional---agribusiness",
        "source": "NAB Business",
    },
]

FEEDS = [
    # Broad Australian news
    "https://www.abc.net.au/news/feed/51120/rss.xml",
    "https://www.smh.com.au/rss/feed.xml",
    "https://www.theguardian.com/australia-news/rss",
    "https://www.afr.com/rss/feed.xml",
    "https://www.news.com.au/content-feeds/latest-news-national/",
    # Broad budget
    "https://news.google.com/rss/search?q=Australian+federal+budget+2026&hl=en-AU&gl=AU&ceid=AU:en",
    "https://news.google.com/rss/search?q=Chalmers+budget+surplus+deficit+2026&hl=en-AU&gl=AU&ceid=AU:en",
    "https://news.google.com/rss/search?q=budget+2026+ASX+market+reaction&hl=en-AU&gl=AU&ceid=AU:en",
    # Individuals & cost of living
    "https://news.google.com/rss/search?q=budget+2026+tax+cuts+individuals+Australia&hl=en-AU&gl=AU&ceid=AU:en",
    "https://news.google.com/rss/search?q=budget+2026+cost+of+living+relief+welfare+payments&hl=en-AU&gl=AU&ceid=AU:en",
    "https://news.google.com/rss/search?q=budget+2026+housing+first+home+buyer+rent+assistance&hl=en-AU&gl=AU&ceid=AU:en",
    "https://news.google.com/rss/search?q=budget+2026+HECS+student+debt+education&hl=en-AU&gl=AU&ceid=AU:en",
    # Business
    "https://news.google.com/rss/search?q=budget+2026+small+business+instant+asset+write+off&hl=en-AU&gl=AU&ceid=AU:en",
    "https://news.google.com/rss/search?q=budget+2026+business+investment+incentives+corporate&hl=en-AU&gl=AU&ceid=AU:en",
    "https://news.google.com/rss/search?q=budget+2026+energy+renewables+manufacturing&hl=en-AU&gl=AU&ceid=AU:en",
    # Agribusiness
    "https://news.google.com/rss/search?q=budget+2026+agriculture+farmers+agribusiness&hl=en-AU&gl=AU&ceid=AU:en",
    "https://news.google.com/rss/search?q=budget+2026+drought+water+rural+regional&hl=en-AU&gl=AU&ceid=AU:en",
    "https://news.google.com/rss/search?q=budget+2026+food+security+biosecurity+farming&hl=en-AU&gl=AU&ceid=AU:en",
    # Health
    "https://news.google.com/rss/search?q=budget+2026+health+Medicare+hospitals+PBS&hl=en-AU&gl=AU&ceid=AU:en",
    "https://news.google.com/rss/search?q=budget+2026+aged+care+mental+health+NDIS&hl=en-AU&gl=AU&ceid=AU:en",
]


# ---------------------------------------------------------------------------
# Fetch & deduplicate feeds
# ---------------------------------------------------------------------------
def fetch_entries(lookback_hours: int = 48) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    all_entries = []

    for url in FEEDS:
        try:
            feed = feedparser.parse(url)
            count = 0
            source = feed.feed.get("title", url[:60])
            for e in feed.entries:
                dt = _parse_date(e)
                title = e.get("title", "").strip()
                if title and (dt is None or dt >= cutoff):
                    all_entries.append({
                        "title": title,
                        "url": e.get("link", ""),
                        "source": source,
                    })
                    count += 1
            print(f"    {count:3d} stories — {source[:60]}")
        except Exception as ex:
            print(f"    WARN {url[:60]}: {ex}")

    deduped = _dedupe(all_entries)
    budget_kw = ("budget", "chalmers", "treasurer", "surplus", "deficit", "tax",
                 "cost of living", "housing", "spending", "fiscal", "albanese")
    budget = [e for e in deduped if any(k in e["title"].lower() for k in budget_kw)]
    other  = [e for e in deduped if e not in budget]
    result = budget + other
    print(f"  {len(result)} total stories ({len(budget)} budget-specific)")
    return result


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
# Direct article fetcher
# ---------------------------------------------------------------------------
def fetch_direct_articles() -> list[dict]:
    """Fetches named article URLs and extracts readable text for the prompt."""
    results = []
    for art in DIRECT_ARTICLES:
        try:
            resp = requests.get(
                art["url"],
                timeout=15,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            # Strip nav, header, footer, scripts, styles
            for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)
            # Keep first ~3000 chars — enough for Claude to work with
            text = "\n".join(line for line in text.splitlines() if len(line.strip()) > 40)[:3000]
            results.append({"source": art["source"], "url": art["url"], "text": text})
            print(f"    Fetched direct article: {art['source']} ({len(text)} chars)")
        except Exception as ex:
            print(f"    WARN direct article {art['url'][:60]}: {ex}")
    return results


# ---------------------------------------------------------------------------
# Claude prompt
# ---------------------------------------------------------------------------
def build_prompt(entries: list[dict], date_str: str, direct_articles: list[dict] | None = None) -> str:
    story_block = "\n".join(
        f"[{e['source']}] {e['title']}\n  {e['url']}"
        for e in entries[:40]
    )

    direct_block = ""
    if direct_articles:
        parts = []
        for a in direct_articles:
            parts.append(f"=== FULL ARTICLE: {a['source']} ===\nURL: {a['url']}\n\n{a['text']}\n")
        direct_block = "\n=== IN-DEPTH SOURCES (use these for detailed analysis) ===\n\n" + "\n".join(parts)

    return f"""You are producing a Federal Budget special edition of The Operating Brief for {date_str}.
Audience: Australian professionals, investors, business owners, farmers, and individuals.
IMPORTANT: Do NOT use WebFetch or any tool. Do NOT visit any URLs. Write from the headlines only.
Produce output in EXACTLY this format — no extra text outside the tags:

GLOBAL RULES:
1. Ground every claim in the stories below — no invented figures.
2. Use specific dollar amounts, percentages, and timeframes wherever the headlines provide them.
3. Write with authority and analytical depth — explain implications, not just facts. What changes on the ground?
4. Short sentences. Active voice. No hedging phrases ("it remains to be seen", "could potentially").
5. SUMMARY fields: exactly 2 sentences. Sentence 1: the specific measure with a number. Sentence 2: the real-world implication for the reader — what actually changes for them.
6. Section OVERVIEW fields: 1-2 sentences of synthesis, not description. Capture the "so what" for that audience.
7. If a section has no relevant stories, write a 1-sentence overview saying so and omit story blocks.

BUDGET_HEADLINE_START
2-sentence plain-English headline summary. Lead with the single most important number (surplus/deficit, headline tax measure, or total spend).
BUDGET_HEADLINE_END

BUDGET_OVERVIEW_START
300-word analytical opening note. Go beyond listing measures — explain what they mean and why they matter.
Paragraph 1 (2-3 sentences): Fiscal position and character of the budget. Is this a spending budget or a reform budget? Surplus or deficit, dollar figure, the structural forces shaping it (NDIS blowout, cigarette excise, global risks).
Paragraph 2 (2-3 sentences): The defining political and economic bet Chalmers is making. What is the government trying to do — stimulate, redistribute, reform? Name the tension or trade-off at the centre of this budget.
Paragraph 3 (2-3 sentences): The two or three measures with the most direct impact on Australians — not just what they are, but what changes on the ground. Use specific figures.
Paragraph 4 (2-3 sentences): The risk picture — what could go wrong, what external forces the budget itself flags (Middle East conflict, Trump tariffs, global slowdown), and what that means for Australian households and businesses.
Write with authority. Active voice. Short sentences. No hedging. No "it remains to be seen". No editorial opinion — just clear-eyed analysis.
Separate paragraphs with a blank line. No headings. No bullet points.
BUDGET_OVERVIEW_END

THE_NUMBER_START
STAT: <standout figure — max 6 words, e.g. '$2,816 average worker tax relief'>
CONTEXT: <one sentence — what it is and why it matters to an Australian>
THE_NUMBER_END

INDIVIDUALS_OVERVIEW_START
1-sentence factual summary of the most important personal finance and cost-of-living impacts.
INDIVIDUALS_OVERVIEW_END

2-3 most important stories for individuals (tax cuts, cost of living, housing, welfare, education):
INDIVIDUALS_STORY_START
TITLE: <headline from the stories>
SOURCE: <publication name>
URL: <url>
SUMMARY: <2 sentences — specific figure in sentence 1, implication in sentence 2>
INDIVIDUALS_STORY_END

BUSINESS_OVERVIEW_START
1-sentence factual summary of the key business and investment measures.
BUSINESS_OVERVIEW_END

2-3 most important stories for business (SMEs, corporates, investment, energy, workforce):
BUSINESS_STORY_START
TITLE: <headline>
SOURCE: <publication>
URL: <url>
SUMMARY: <2 sentences>
BUSINESS_STORY_END

AGRI_OVERVIEW_START
1-sentence factual summary of agribusiness and rural measures. If nothing material: say so in one sentence.
AGRI_OVERVIEW_END

Up to 2 agribusiness stories (farmers, drought, biosecurity, rural communities) — omit entirely if nothing material:
AGRI_STORY_START
TITLE: <headline>
SOURCE: <publication>
URL: <url>
SUMMARY: <2 sentences>
AGRI_STORY_END

HEALTH_OVERVIEW_START
1-sentence factual summary of health, aged care, Medicare, NDIS, and PBS measures.
HEALTH_OVERVIEW_END

2-3 most important health stories:
HEALTH_STORY_START
TITLE: <headline>
SOURCE: <publication>
URL: <url>
SUMMARY: <2 sentences>
HEALTH_STORY_END

MARKET_TAKE_START
1-sentence factual summary of the immediate ASX and macro implications.
MARKET_TAKE_END

2-3 most important market and investor stories:
MARKET_STORY_START
TITLE: <headline>
SOURCE: <publication>
URL: <url>
SUMMARY: <2 sentences>
MARKET_STORY_END

SUBJECT_LINE_START
One email subject line, max 60 characters. Lead with the most important number or measure. No clickbait.
Format: <key stat or hook> | Federal Budget Special
SUBJECT_LINE_END

=== BUDGET STORIES ===

{story_block}
{direct_block}
"""


def call_claude(prompt: str) -> str:
    print("  Calling claude CLI…")
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    result = subprocess.run(
        ["claude", "-p", "-"],
        input=prompt,
        capture_output=True, text=True, timeout=900,
        env=env,
    )
    if result.returncode != 0:
        raise RuntimeError(f"claude CLI error (rc={result.returncode}): {result.stderr!r}")
    return result.stdout


# ---------------------------------------------------------------------------
# Parse response
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
            for key in ("TITLE", "SOURCE", "URL", "SUMMARY"):
                if line.startswith(f"{key}:"):
                    item[key.lower()] = line[len(key)+1:].strip()
        if item.get("title"):
            items.append(item)
    return items


def parse_response(raw: str) -> dict:
    the_number_block = re.findall(r"THE_NUMBER_START\n(.*?)\nTHE_NUMBER_END", raw, re.DOTALL)
    stat, context = "", ""
    if the_number_block:
        for line in the_number_block[0].splitlines():
            if line.startswith("STAT:"):
                stat = line[5:].strip()
            elif line.startswith("CONTEXT:"):
                context = line[8:].strip()
    return {
        "headline":             _extract(raw, "BUDGET_HEADLINE"),
        "overview":             _extract(raw, "BUDGET_OVERVIEW"),
        "stat":                 stat,
        "context":              context,
        "individuals_overview": _extract(raw, "INDIVIDUALS_OVERVIEW"),
        "individuals_stories":  _extract_blocks(raw, "INDIVIDUALS_STORY"),
        "business_overview":    _extract(raw, "BUSINESS_OVERVIEW"),
        "business_stories":     _extract_blocks(raw, "BUSINESS_STORY"),
        "agri_overview":        _extract(raw, "AGRI_OVERVIEW"),
        "agri_stories":         _extract_blocks(raw, "AGRI_STORY"),
        "health_overview":      _extract(raw, "HEALTH_OVERVIEW"),
        "health_stories":       _extract_blocks(raw, "HEALTH_STORY"),
        "market_take":          _extract(raw, "MARKET_TAKE"),
        "market_stories":       _extract_blocks(raw, "MARKET_STORY"),
        "subject_line":         _extract(raw, "SUBJECT_LINE"),
    }


# ---------------------------------------------------------------------------
# HTML rendering — same story-card pattern as the other digests
# ---------------------------------------------------------------------------
def _e(s: str) -> str:
    return html.escape(s or "")


def _story_card(item: dict) -> str:
    return f"""
<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:20px;">
  <tr><td style="padding-bottom:16px;border-bottom:1px solid #eee;">
    <p style="margin:0 0 4px;font-size:11px;color:#888;font-family:Arial,sans-serif;text-transform:uppercase;letter-spacing:.05em;">{_e(item.get('source',''))}</p>
    <p style="margin:0 0 6px;font-size:17px;font-weight:700;color:#111;line-height:1.35;font-family:Georgia,serif;"><a href="{_e(item.get('url',''))}" style="color:#111;text-decoration:none;">{_e(item.get('title',''))}</a></p>
    <p style="margin:0;font-size:14px;color:#444;line-height:1.6;font-family:Arial,sans-serif;">{_e(item.get('summary',''))}</p>
  </td></tr>
</table>"""


def _section(label: str, overview: str, stories: list) -> str:
    stories_html = "".join(_story_card(s) for s in stories)
    return f"""
  <tr><td style="padding:0 48px 32px;">
    <p style="margin:0 0 20px;font-size:11px;color:#888;letter-spacing:.12em;text-transform:uppercase;font-family:Arial,sans-serif;">{_e(label)}</p>
    <p style="margin:0 0 24px;font-size:16px;color:#222;line-height:1.75;font-family:Georgia,serif;">{_e(overview)}</p>
    {stories_html}
  </td></tr>
  <tr><td style="padding:0 48px;"><hr style="border:none;border-top:1px solid #ddd;margin:0 0 32px;"></td></tr>"""


def render_html(d: dict, date_str: str) -> str:
    para_style = 'margin:0 0 16px;font-size:16px;color:#222;line-height:1.75;font-family:Georgia,serif;'
    overview_html = "".join(
        f'<p style="{para_style}">{_e(p.strip())}</p>'
        for p in re.split(r'\n{2,}', d["overview"].strip()) if p.strip()
    )

    the_number_html = ""
    if d.get("stat"):
        the_number_html = f"""
  <tr><td style="padding:0 48px 32px;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background:#111;">
      <tr><td style="padding:28px 32px;" align="left">
        <p style="margin:0 0 4px;font-size:11px;color:#888;letter-spacing:.15em;text-transform:uppercase;font-family:Arial,sans-serif;">The Number</p>
        <p style="margin:0 0 8px;font-size:42px;font-weight:700;color:#fff;font-family:Georgia,serif;line-height:1.1;">{_e(d['stat'])}</p>
        <p style="margin:0;font-size:14px;color:#ccc;line-height:1.6;font-family:Arial,sans-serif;">{_e(d['context'])}</p>
      </td></tr>
    </table>
  </td></tr>
  <tr><td style="padding:0 48px;"><hr style="border:none;border-top:1px solid #ddd;margin:8px 0 32px;"></td></tr>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Federal Budget Special – {date_str}</title></head>
<body style="margin:0;padding:0;background:#f5f4f0;font-family:Georgia,serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f4f0;padding:40px 16px;">
<tr><td align="center">
<table width="620" cellpadding="0" cellspacing="0" style="max-width:620px;width:100%;background:#fff;">

  <!-- Header -->
  <tr><td style="padding:40px 48px 24px;border-bottom:3px solid #111;">
    <p style="margin:0 0 4px;font-size:11px;color:#888;letter-spacing:.15em;text-transform:uppercase;font-family:Arial,sans-serif;">Special Edition · {date_str}</p>
    <h1 style="margin:0 0 6px;font-size:38px;font-weight:700;color:#111;font-family:Georgia,serif;letter-spacing:-1px;line-height:1.05;">Federal Budget<br>2026 Special</h1>
    <p style="margin:4px 0 0;font-size:11px;color:#888;letter-spacing:.12em;text-transform:uppercase;font-family:Arial,sans-serif;">The Operating Brief · The Markets Brief</p>
  </td></tr>

  <!-- Headline -->
  <tr><td style="padding:28px 48px 0;">
    <p style="margin:0;font-size:19px;font-weight:700;color:#111;line-height:1.5;font-family:Georgia,serif;font-style:italic;">{_e(d['headline'])}</p>
  </td></tr>

  <tr><td style="padding:20px 48px;"><hr style="border:none;border-top:1px solid #ddd;margin:0;"></td></tr>

  <!-- Opening overview -->
  <tr><td style="padding:0 48px 24px;">
    <p style="margin:0 0 16px;font-size:11px;color:#888;letter-spacing:.12em;text-transform:uppercase;font-family:Arial,sans-serif;">Budget Overview</p>
    {overview_html}
  </td></tr>

  <tr><td style="padding:0 48px;"><hr style="border:none;border-top:1px solid #ddd;margin:0 0 32px;"></td></tr>

  {the_number_html}

  {_section("Individuals & Households", d.get("individuals_overview",""), d.get("individuals_stories",[]))}
  {_section("Business", d.get("business_overview",""), d.get("business_stories",[]))}
  {_section("Agribusiness & Rural", d.get("agri_overview",""), d.get("agri_stories",[]))}
  {_section("Health & Aged Care", d.get("health_overview",""), d.get("health_stories",[]))}
  {_section("Markets & Investors", d.get("market_take",""), d.get("market_stories",[]))}

  <!-- Footer -->
  <tr><td style="padding:24px 48px;border-top:2px solid #111;">
    <p style="margin:0 0 4px;font-size:12px;color:#888;font-family:Arial,sans-serif;">A special edition from The Operating Brief &amp; The Markets Brief.</p>
    <p style="margin:0;font-size:12px;color:#aaa;font-family:Arial,sans-serif;">This is a one-time special. Your regular briefings continue tomorrow.</p>
  </td></tr>

</table></td></tr></table>
</body></html>"""


# ---------------------------------------------------------------------------
# Supabase — combined subscriber list (both newsletters)
# ---------------------------------------------------------------------------
def get_supabase():
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])


def load_all_recipients() -> list[dict]:
    sb = get_supabase()
    ob = sb.table("subscribers").select("email,token").eq("active", True).execute()
    mb = sb.table("markets_subscribers").select("email,token").eq("active", True).execute()
    seen, combined = set(), []
    for row in (ob.data or []) + (mb.data or []):
        if row["email"] not in seen:
            seen.add(row["email"])
            combined.append(row)
    print(f"  {len(ob.data or [])} Operating Brief + {len(mb.data or [])} Markets Brief = {len(combined)} unique recipients")
    return combined


def send_email(to: list[str], subject: str, html_body: str) -> str:
    resend.api_key = os.environ["RESEND_API_KEY"]
    params: resend.Emails.SendParams = {
        "from":     os.environ.get("FROM_EMAIL", "brief@theoperatingbrief.com"),
        "to":       to,
        "reply_to": os.environ.get("REPLY_TO_EMAIL", "hello@theoperatingbrief.com"),
        "subject":  subject,
        "html":     html_body,
    }
    resp = resend.Emails.send(params)
    return resp.get("id", str(resp))


def send_to_all(recipients: list[dict], subject: str, base_html: str) -> list[str]:
    resend_ids = []
    failed = []
    for i, sub in enumerate(recipients):
        if i > 0:
            time.sleep(0.6)  # stay under Resend's 2 req/sec limit
        try:
            resend_id = send_email([sub["email"]], subject, base_html)
            print(f"    → {sub['email']} ({resend_id})")
            resend_ids.append(resend_id)
        except Exception as ex:
            print(f"    FAILED {sub['email']}: {ex}")
            failed.append(sub["email"])
    if failed:
        print(f"\n  ⚠️  {len(failed)} failed: {', '.join(failed)}")
    return resend_ids


# ---------------------------------------------------------------------------
# Send helper
# ---------------------------------------------------------------------------
def _do_send(html_body: str, subject: str) -> None:
    print("Loading recipients…")
    recipients = load_all_recipients()
    if not recipients:
        print("No active subscribers found. Exiting.")
        return
    print(f"  Sending to {len(recipients)} recipient(s)…")
    send_to_all(recipients, subject, html_body)
    print("Done! ✅")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    import argparse, webbrowser
    parser = argparse.ArgumentParser(description="Federal Budget Special Edition")
    parser.add_argument("--preview", action="store_true", help="Generate HTML, open in browser, then prompt y/n to send")
    parser.add_argument("--send",    action="store_true", help="Send the saved preview_budget.html without regenerating")
    args = parser.parse_args()

    aest = ZoneInfo("Australia/Sydney")
    now_aest = datetime.now(aest)
    date_str = now_aest.strftime("%B %d, %Y")

    preview_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "preview_budget.html")
    subject_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "preview_budget_subject.txt")

    if args.send:
        if not os.path.exists(preview_path):
            print(f"No preview found at {preview_path}. Run --preview first.")
            return
        with open(preview_path) as f:
            html_body = f.read()
        subject = "Federal Budget 2026 | Special Edition"
        if os.path.exists(subject_path):
            with open(subject_path) as f:
                subject = f.read().strip() or subject
        print(f"  Sending: {subject}")
        _do_send(html_body, subject)
        return

    print("Fetching budget news…")
    entries = fetch_entries(lookback_hours=48)
    if not entries:
        print("No stories found — try again after 7:30pm AEST.")
        return

    print("Fetching direct articles…")
    direct_articles = fetch_direct_articles()

    print("Summarising with Claude…")
    prompt = build_prompt(entries, date_str, direct_articles)
    print(f"  Prompt length: {len(prompt):,} chars (~{len(prompt)//4:,} tokens)")
    raw = call_claude(prompt)

    with open("debug_budget_response.txt", "w") as f:
        f.write(raw)

    print("Parsing response…")
    digest = parse_response(raw)
    subject = digest.get("subject_line") or "Federal Budget 2026 | Special Edition"
    print(f"  Subject: {subject}")

    print("Rendering HTML…")
    html_body = render_html(digest, date_str)

    with open(preview_path, "w") as f:
        f.write(html_body)
    with open(subject_path, "w") as f:
        f.write(subject)

    if args.preview:
        print(f"Preview saved → {preview_path}")
        webbrowser.open(f"file://{preview_path}")
        answer = input("\nSend to all subscribers now? (y/n): ").strip().lower()
        if answer != "y":
            print("Not sent. Run with --send to send the saved preview.")
            return

    _do_send(html_body, subject)


if __name__ == "__main__":
    main()
