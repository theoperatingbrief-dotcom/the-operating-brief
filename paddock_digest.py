#!/usr/bin/env python3
"""
Daily Agriculture Digest — The Paddock Brief
Covers Australian agriculture, global conditions, AgTech/AI, and policy.
Audience: Australian producers, agronomists, rural advisors (Humans of Agriculture listeners).
Same architecture as daily_digest.py. Run with --preview to check output locally.
"""
import os
import re
import html
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
    "grain": [
        "https://www.graincentral.com/feed/",
        "https://www.farmweekly.com.au/rss.xml",
        "https://www.weeklytimesnow.com.au/rss.xml",
        "https://www.farmonline.com.au/rss.xml",
        "https://news.google.com/rss/search?q=Australian+wheat+barley+canola+price+grain&hl=en-AU&gl=AU&ceid=AU:en",
        "https://news.google.com/rss/search?q=ABARES+Australian+crop+harvest+forecast&hl=en-AU&gl=AU&ceid=AU:en",
        "https://www.world-grain.com/rss/news",
    ],
    "livestock": [
        "https://www.beefcentral.com/feed/",
        "https://www.sheepcentral.com/feed/",
        "https://www.mla.com.au/rss/",
        "https://news.google.com/rss/search?q=Australian+cattle+sheep+lamb+price+livestock&hl=en-AU&gl=AU&ceid=AU:en",
        "https://news.google.com/rss/search?q=AuctionsPlus+cattle+sheep+yarding&hl=en-AU&gl=AU&ceid=AU:en",
        "https://news.google.com/rss/search?q=Australian+beef+export+market&hl=en-AU&gl=AU&ceid=AU:en",
    ],
    "horticulture": [
        "https://www.freshplaza.com/rss/",
        "https://news.google.com/rss/search?q=Australian+horticulture+fruit+vegetables+wool+cotton&hl=en-AU&gl=AU&ceid=AU:en",
        "https://news.google.com/rss/search?q=Hort+Innovation+Australia+growers&hl=en-AU&gl=AU&ceid=AU:en",
        "https://news.google.com/rss/search?q=Australian+wool+price+AWEX&hl=en-AU&gl=AU&ceid=AU:en",
    ],
    "global": [
        "https://feeds.reuters.com/reuters/businessNews",
        "https://news.google.com/rss/search?q=USDA+crop+report+global+grain+supply&hl=en-AU&gl=AU&ceid=AU:en",
        "https://news.google.com/rss/search?q=La+Nina+El+Nino+Australia+agriculture+drought+rain&hl=en-AU&gl=AU&ceid=AU:en",
        "https://news.google.com/rss/search?q=China+Australia+agriculture+trade+export+tariff&hl=en-AU&gl=AU&ceid=AU:en",
        "https://news.google.com/rss/search?q=Ukraine+Russia+wheat+grain+global+supply&hl=en-AU&gl=AU&ceid=AU:en",
        "https://news.google.com/rss/search?q=global+food+commodity+price+agriculture&hl=en-AU&gl=AU&ceid=AU:en",
        "https://news.google.com/rss/search?q=Indonesia+Southeast+Asia+Australia+beef+trade&hl=en-AU&gl=AU&ceid=AU:en",
    ],
    "weather": [
        "https://news.google.com/rss/search?q=BOM+seasonal+outlook+Australia+rainfall+drought&hl=en-AU&gl=AU&ceid=AU:en",
        "https://news.google.com/rss/search?q=Australia+farm+flooding+drought+frost+weather&hl=en-AU&gl=AU&ceid=AU:en",
        "https://news.google.com/rss/search?q=Australia+soil+moisture+crop+conditions&hl=en-AU&gl=AU&ceid=AU:en",
    ],
    "agtech": [
        "https://agfundernews.com/feed",
        "https://www.precisionag.com/feed/",
        "https://news.google.com/rss/search?q=AgTech+Australia+precision+agriculture+robotics+drone&hl=en-AU&gl=AU&ceid=AU:en",
        "https://news.google.com/rss/search?q=AI+agriculture+farm+technology+satellite+sensing&hl=en-AU&gl=AU&ceid=AU:en",
        "https://news.google.com/rss/search?q=autonomous+farm+equipment+harvester+tractor+technology&hl=en-AU&gl=AU&ceid=AU:en",
    ],
    "policy": [
        "https://www.abc.net.au/rural/rss.xml",
        "https://news.google.com/rss/search?q=Australian+agriculture+policy+biosecurity+DAFF&hl=en-AU&gl=AU&ceid=AU:en",
        "https://news.google.com/rss/search?q=National+Farmers+Federation+NFF+Australia+farm+policy&hl=en-AU&gl=AU&ceid=AU:en",
        "https://news.google.com/rss/search?q=Murray+Darling+Basin+water+rights+irrigation+Australia&hl=en-AU&gl=AU&ceid=AU:en",
        "https://news.google.com/rss/search?q=Australian+agriculture+minister+land+clearing+regulation&hl=en-AU&gl=AU&ceid=AU:en",
    ],
}

SIMILARITY_THRESHOLD = 0.75


# ---------------------------------------------------------------------------
# Fetch & deduplicate
# ---------------------------------------------------------------------------
def fetch_entries(feeds: dict) -> dict:
    is_monday = datetime.now(timezone.utc).weekday() == 0
    base_hours = 96 if is_monday else 48
    cutoff = datetime.now(timezone.utc) - timedelta(hours=base_hours)
    results = {k: [] for k in feeds}

    for cat, urls in feeds.items():
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
        "You are producing a weekly agriculture digest for Australian producers, agronomists, and rural advisors.",
        "Your audience listens to Humans of Agriculture — practical, grounded people who run properties or work closely with those who do.",
        "Based on the stories below, produce output in EXACTLY this format — no extra text:\n",

        "GLOBAL RULES — follow exactly:",
        "1. Always be specific — name the commodity, region, country, company, or policy. Never write 'a farmer', 'a commodity', 'some markets'.",
        "2. Framing is always farm-gate first: 'what does this mean for Australian producers?' not 'what does this mean for the market?'",
        "3. No hype, no buzzwords, no breathless AgTech boosterism. If a technology isn't proven or deployed at scale, say so.",
        "4. Tone: practical reporter, not columnist. Facts, then implication. No dramatic framing.",
        "5. If a price or figure is in the source data, include it. Don't round or omit specific numbers.",
        "6. Cut every unnecessary word.\n",

        "BRIEFING_START",
        "Write a 400-word opening briefing in 3-4 short paragraphs — no bullet points, no bold headings.",
        "Cover the 3-4 most significant stories across all categories this week.",
        "Lead with what matters most to a producer right now: prices, weather, trade, biosecurity.",
        "End with one sentence pointing to the detail sections below.",
        "Separate each paragraph with a blank line.",
        "BRIEFING_END\n",

        "COMMODITY_OVERVIEW_START",
        "1-sentence summary of the most significant commodity price signal or market move this week. Name the specific commodity and direction.",
        "COMMODITY_OVERVIEW_END\n",

        "3 most important commodity stories (grain, livestock, horticulture, wool — mix where possible):",
        "COMMODITY_STORY_START\nTITLE: <title>\nSOURCE: <source>\nCOMMODITY: <e.g. Wheat | Cattle | Wool | Canola | Lamb | Cotton>\nURL: <url>\nSUMMARY: <2 sentences — price or market signal first, implication for producers second>\nCOMMODITY_STORY_END\n",

        "GLOBAL_OVERVIEW_START",
        "1-sentence summary of the most important global condition affecting Australian agriculture this week. Be specific — name the country, policy, or weather event.",
        "GLOBAL_OVERVIEW_END\n",

        "2 most important global conditions stories (trade, supply chains, geopolitics, weather systems, USDA reports):",
        "GLOBAL_STORY_START\nTITLE: <title>\nSOURCE: <source>\nURL: <url>\nSUMMARY: <2 sentences — global event first, Australian flow-on second>\nGLOBAL_STORY_END\n",

        "WEATHER_OVERVIEW_START",
        "1-sentence summary of the most significant weather or climate signal for Australian farming this week. Include the region and the key implication (planting window, drought risk, flooding). Write exactly NO_CONTENT if there is nothing significant.",
        "WEATHER_OVERVIEW_END\n",

        "AGTECH_OVERVIEW_START",
        "1-sentence summary of the most practically relevant AgTech or AI-in-agriculture story this week. Name the specific technology, company, or trial. Write exactly NO_CONTENT if there is nothing genuinely significant.",
        "AGTECH_OVERVIEW_END\n",

        "Up to 2 AgTech stories (only include if genuinely relevant to Australian producers — no puff pieces, no overseas-only announcements with no AU relevance):",
        "AGTECH_STORY_START\nTITLE: <title>\nSOURCE: <source>\nURL: <url>\nSUMMARY: <2 sentences — what the technology does, what it means for producers>\nAGTECH_STORY_END\n",

        "POLICY_OVERVIEW_START",
        "1-sentence summary of the most important policy, biosecurity, or regulatory development for Australian agriculture this week. Write exactly NO_CONTENT if there is nothing significant.",
        "POLICY_OVERVIEW_END\n",

        "Up to 2 policy stories (biosecurity, water, government ag policy, trade agreements):",
        "POLICY_STORY_START\nTITLE: <title>\nSOURCE: <source>\nURL: <url>\nSUMMARY: <2 sentences — what the policy is, what it means for producers>\nPOLICY_STORY_END\n",

        "=== STORIES ===\n",
    ]

    limits = {"grain": 8, "livestock": 8, "horticulture": 6, "global": 8, "weather": 5, "agtech": 6, "policy": 6}
    for cat, items in entries.items():
        lines.append(f"--- {cat.upper()} ---")
        for item in items[:limits.get(cat, 8)]:
            lines.append(f"[{item['source']}] {item['title']}")
            lines.append(f"  {item['url']}")
        lines.append("")

    return "\n".join(lines)


def call_claude(prompt: str) -> str:
    print("  Calling claude CLI...")
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    result = subprocess.run(
        ["claude", "-p", "-"],
        input=prompt,
        capture_output=True, text=True, timeout=900,
        env=env,
    )
    if result.returncode != 0:
        raise RuntimeError(f"claude CLI error (rc={result.returncode}): stderr={result.stderr!r} stdout={result.stdout[:500]!r}")
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
            for key in ("TITLE", "SOURCE", "COMMODITY", "URL", "SUMMARY"):
                if line.startswith(f"{key}:"):
                    item[key.lower()] = line[len(key)+1:].strip()
        if item:
            items.append(item)
    return items


def parse_response(raw: str) -> dict:
    return {
        "briefing":          _extract(raw, "BRIEFING"),
        "commodity_overview": _extract(raw, "COMMODITY_OVERVIEW"),
        "commodity_stories": _extract_blocks(raw, "COMMODITY_STORY"),
        "global_overview":   _extract(raw, "GLOBAL_OVERVIEW"),
        "global_stories":    _extract_blocks(raw, "GLOBAL_STORY"),
        "weather_overview":  _extract(raw, "WEATHER_OVERVIEW"),
        "agtech_overview":   _extract(raw, "AGTECH_OVERVIEW"),
        "agtech_stories":    _extract_blocks(raw, "AGTECH_STORY"),
        "policy_overview":   _extract(raw, "POLICY_OVERVIEW"),
        "policy_stories":    _extract_blocks(raw, "POLICY_STORY"),
    }


# ---------------------------------------------------------------------------
# HTML rendering
# ---------------------------------------------------------------------------
ACCENT = "#4a7c59"  # earthy green


def _e(s: str) -> str:
    return html.escape(s or "")


def _story_card(item: dict) -> str:
    commodity = item.get("commodity", "").strip()
    tag_html = (
        f'<span style="display:inline-block;font-size:11px;font-weight:700;color:#fff;background:{ACCENT};font-family:Arial,sans-serif;padding:2px 8px;letter-spacing:.04em;margin-bottom:6px;">{_e(commodity)}</span><br>'
        if commodity else ""
    )
    return f"""
<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:20px;">
  <tr><td style="padding-bottom:16px;border-bottom:1px solid #eee;">
    <p style="margin:0 0 6px;font-size:11px;color:#888;font-family:Arial,sans-serif;text-transform:uppercase;letter-spacing:.05em;">{_e(item.get('source', ''))}</p>
    {tag_html}
    <p style="margin:0 0 6px;font-size:17px;font-weight:700;color:#111;line-height:1.35;font-family:Georgia,serif;"><a href="{_e(item.get('url', ''))}" style="color:#111;text-decoration:none;">{_e(item.get('title', ''))}</a></p>
    <p style="margin:0;font-size:14px;color:#444;line-height:1.6;font-family:Arial,sans-serif;">{_e(item.get('summary', ''))}</p>
  </td></tr>
</table>"""


def _section(label: str, overview: str, stories: list) -> str:
    stories_html = "".join(_story_card(s) for s in stories)
    overview_html = f'<p style="margin:0 0 24px;font-size:16px;color:#222;line-height:1.75;font-family:Georgia,serif;">{_e(overview)}</p>' if overview else ""
    return f"""
  <tr><td style="padding:0 48px 32px;">
    <p style="margin:0 0 20px;font-size:11px;color:#888;letter-spacing:.12em;text-transform:uppercase;font-family:Arial,sans-serif;">{_e(label)}</p>
    <h2 style="margin:0 0 10px;font-size:14px;font-weight:700;color:#111;text-transform:uppercase;letter-spacing:.08em;font-family:Arial,sans-serif;border-left:3px solid {ACCENT};padding-left:10px;">Overview</h2>
    {overview_html}
    {stories_html}
  </td></tr>
  <tr><td style="padding:0 48px;"><hr style="border:none;border-top:1px solid #ddd;margin:0 0 32px;"></td></tr>"""


def render_html(d: dict, date_str: str) -> str:
    def _render_briefing(raw: str) -> str:
        para_style = 'margin:0 0 16px;font-size:16px;color:#333;line-height:1.75;font-family:Georgia,serif;'
        paragraphs = [p.strip() for p in re.split(r'\n{2,}|\n', raw.strip()) if p.strip()]
        return ''.join(f'<p style="{para_style}">{_e(p)}</p>' for p in paragraphs)

    briefing_html = _render_briefing(d["briefing"])

    sections = _section("Commodities", d["commodity_overview"], d["commodity_stories"][:3])
    sections += _section("Global Conditions", d["global_overview"], d["global_stories"][:2])

    if d.get("weather_overview", "").strip().upper() != "NO_CONTENT" and d.get("weather_overview"):
        sections += f"""
  <tr><td style="padding:0 48px 32px;">
    <p style="margin:0 0 20px;font-size:11px;color:#888;letter-spacing:.12em;text-transform:uppercase;font-family:Arial,sans-serif;">Weather & Climate</p>
    <h2 style="margin:0 0 10px;font-size:14px;font-weight:700;color:#111;text-transform:uppercase;letter-spacing:.08em;font-family:Arial,sans-serif;border-left:3px solid {ACCENT};padding-left:10px;">Outlook</h2>
    <p style="margin:0;font-size:16px;color:#222;line-height:1.75;font-family:Georgia,serif;">{_e(d['weather_overview'])}</p>
  </td></tr>
  <tr><td style="padding:0 48px;"><hr style="border:none;border-top:1px solid #ddd;margin:0 0 32px;"></td></tr>"""

    if d.get("agtech_overview", "").strip().upper() != "NO_CONTENT" and d.get("agtech_overview"):
        sections += _section("AgTech & AI", d["agtech_overview"], d["agtech_stories"][:2])

    if d.get("policy_overview", "").strip().upper() != "NO_CONTENT" and d.get("policy_overview"):
        sections += _section("Policy & Biosecurity", d["policy_overview"], d["policy_stories"][:2])

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>The Paddock Brief – {date_str}</title></head>
<body style="margin:0;padding:0;background:#f5f4f0;font-family:Georgia,serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f4f0;padding:40px 16px;">
<tr><td align="center">
<table width="620" cellpadding="0" cellspacing="0" style="max-width:620px;width:100%;background:#fff;">

  <!-- Header -->
  <tr><td style="padding:40px 48px 24px;border-bottom:3px solid #111;">
    <p style="margin:0 0 6px;font-size:11px;color:#888;letter-spacing:.15em;text-transform:uppercase;font-family:Arial,sans-serif;">{date_str}</p>
    <h1 style="margin:0;font-size:40px;font-weight:700;color:#111;font-family:Georgia,serif;letter-spacing:-1px;line-height:1;">The Paddock Brief</h1>
    <p style="margin:4px 0 0;font-size:13px;color:#555;font-family:Arial,sans-serif;">Australian agriculture, global conditions, AgTech</p>
  </td></tr>

  <!-- Briefing -->
  <tr><td style="padding:32px 48px 0;">
    <p style="margin:0 0 20px;font-size:11px;color:#888;letter-spacing:.12em;text-transform:uppercase;font-family:Arial,sans-serif;">This Week's Briefing</p>
    {briefing_html}
  </td></tr>

  <tr><td style="padding:0 48px;"><hr style="border:none;border-top:1px solid #ddd;margin:8px 0 32px;"></td></tr>

  {sections}

  <!-- Footer -->
  <tr><td style="padding:24px 48px;border-top:2px solid #111;">
    <p style="margin:0 0 16px;font-size:13px;color:#222;font-family:Georgia,serif;line-height:1.6;">
      Thoughts on this week's edition? Hit reply — we read everything.
    </p>
    <table width="100%" cellpadding="0" cellspacing="0">
      <tr>
        <td><p style="margin:0;font-size:12px;color:#888;font-family:Arial,sans-serif;">Australian agriculture, delivered weekly</p></td>
        <td align="right">
          <a href="mailto:hello@thepaddockbrief.com.au?subject=Subscribe%20to%20The%20Paddock%20Brief" style="font-size:11px;color:#111;font-family:Arial,sans-serif;text-decoration:none;border-bottom:1px solid #111;padding-bottom:1px;margin-right:16px;">Subscribe</a>
          <a href="mailto:hello@thepaddockbrief.com.au?subject=Unsubscribe%20from%20The%20Paddock%20Brief" style="font-size:11px;color:#888;font-family:Arial,sans-serif;text-decoration:none;border-bottom:1px solid #ccc;padding-bottom:1px;">Unsubscribe</a>
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


def load_recipients() -> list[dict]:
    sb = get_supabase()
    result = sb.table("paddock_subscribers").select("email,token").eq("active", True).execute()
    print(f"  {len(result.data)} active subscriber(s)")
    return result.data


def log_send(subject: str, recipient_count: int, resend_id: str) -> None:
    try:
        sb = get_supabase()
        sb.table("paddock_send_log").insert({
            "subject": subject,
            "recipient_count": recipient_count,
            "resend_id": resend_id,
        }).execute()
    except Exception as ex:
        print(f"  WARN: could not log send: {ex}")


def save_edition(slug: str, subject: str, preview_text: str, html_body: str) -> None:
    try:
        sb = get_supabase()
        sb.table("paddock_editions").upsert({
            "slug": slug,
            "subject": subject,
            "preview_text": preview_text,
            "html": html_body,
        }).execute()
        print(f"  Edition saved: {slug}")
    except Exception as ex:
        print(f"  WARN: could not save edition: {ex}")


# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------
def send_email(to: list[str], subject: str, html_body: str) -> str:
    resend.api_key = os.environ["RESEND_API_KEY"]
    params: resend.Emails.SendParams = {
        "from": os.environ.get("PADDOCK_FROM_EMAIL", "brief@thepaddockbrief.com.au"),
        "to": to,
        "reply_to": os.environ.get("PADDOCK_REPLY_TO_EMAIL", "hello@thepaddockbrief.com.au"),
        "subject": subject,
        "html": html_body,
    }
    resp = resend.Emails.send(params)
    resend_id = resp.get("id", str(resp))
    print(f"    Sent → {resend_id}")
    return resend_id


def send_to_all(subscribers: list[dict], subject: str, base_html: str) -> list[str]:
    resend_ids = []
    for sub in subscribers:
        token = sub.get("token", "")
        email = sub["email"]
        unsub_url = f"https://thepaddockbrief.com.au/unsubscribe?token={token}"
        sub_url = "https://thepaddockbrief.com.au"
        personalised = base_html.replace(
            'href="mailto:hello@thepaddockbrief.com.au?subject=Subscribe%20to%20The%20Paddock%20Brief"',
            f'href="{sub_url}"'
        ).replace(
            'href="mailto:hello@thepaddockbrief.com.au?subject=Unsubscribe%20from%20The%20Paddock%20Brief"',
            f'href="{unsub_url}"'
        )
        resend_id = send_email([email], subject, personalised)
        resend_ids.append(resend_id)
    return resend_ids


# ---------------------------------------------------------------------------
# Quality check
# ---------------------------------------------------------------------------
def quality_check(digest: dict) -> list[str]:
    warnings = []
    if not digest.get("briefing"):
        warnings.append("⚠️  Briefing is missing")
    if len(digest.get("briefing", "")) < 200:
        warnings.append("⚠️  Briefing looks too short")
    if not digest.get("commodity_stories"):
        warnings.append("⚠️  No commodity stories parsed")
    if not digest.get("global_stories"):
        warnings.append("⚠️  No global stories parsed")
    if not digest.get("commodity_overview"):
        warnings.append("⚠️  Commodity overview missing")
    return warnings


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    import argparse, webbrowser, sys
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", action="store_true", help="Generate HTML and open in browser without sending")
    parser.add_argument("--send", action="store_true", help="Send the last generated preview to all subscribers without regenerating")
    args = parser.parse_args()

    aest = ZoneInfo("Australia/Sydney")
    now_aest = datetime.now(aest)
    date_str = now_aest.strftime("%B %d, %Y")
    subject = f"The Paddock Brief – {date_str}"
    preview_path = os.path.join(os.path.dirname(__file__), "preview_paddock.html")

    if args.send:
        if not os.path.exists(preview_path):
            print("No preview found. Run --preview first.")
            return
        with open(preview_path) as f:
            html_body = f.read()
        print("Saving edition to archive…")
        slug = now_aest.strftime("%Y-%m-%d")
        save_edition(slug, subject, "", html_body)
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
    total = sum(len(v) for v in entries.values())
    print(f"  {total} stories total after deduplication")

    if total == 0:
        print("No stories found. Exiting.")
        return

    print("Summarising with Claude…")
    prompt = build_prompt(entries)
    print(f"  Prompt length: {len(prompt):,} chars (~{len(prompt)//4:,} tokens)")
    raw = call_claude(prompt)

    with open("debug_paddock_response.txt", "w") as f:
        f.write(raw)

    print("Parsing response…")
    digest = parse_response(raw)

    print("Rendering HTML…")
    html_body = render_html(digest, date_str)

    with open(preview_path, "w") as f:
        f.write(html_body)

    print("\n── Quality Check ───────────────────────────────")
    warnings = quality_check(digest)
    if warnings:
        for w in warnings:
            print(w)
    else:
        print("✅  All checks passed")
    print("────────────────────────────────────────────────\n")

    if args.preview:
        print(f"Preview saved → {preview_path}")
        webbrowser.open(f"file://{preview_path}")
        if not sys.stdin.isatty():
            print("Running unattended — preview saved. Run 'python3 paddock_digest.py --send' to send.")
            return
        print("\nReview the email in your browser, then come back here.\n")
        answer = input("Send to subscribers? (y/n): ").strip().lower()
        if answer != "y":
            print("Not sent. Run 'python3 paddock_digest.py --send' whenever you're ready.")
            return

    print("Saving edition to archive…")
    slug = now_aest.strftime("%Y-%m-%d")
    preview_text = digest.get("briefing", "")[:120]
    save_edition(slug, subject, preview_text, html_body)

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
