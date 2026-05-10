#!/usr/bin/env python3
"""
Daily Sports Digest — The Sporting Brief
Covers NRL, AFL, Football/Soccer, NBA, and AI in Sport.
Same architecture as daily_digest.py. Run with --preview to check output locally.
"""
import os
import re
import html
import socket
import difflib
import subprocess
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from email.utils import parsedate_to_datetime

import json
import urllib.request
import feedparser
import resend
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# ---------------------------------------------------------------------------
# Feed configuration
# ---------------------------------------------------------------------------
FEEDS = {
    "nrl": [
        "https://www.nrl.com/rss/latest-news/",
        "https://www.foxsports.com.au/rss",
        "https://www.abc.net.au/news/feed/52278/rss.xml",
        "https://wwos.nine.com.au/rss",
        "https://www.news.com.au/content-feeds/latest-news-sport/",
        "https://news.google.com/rss/search?q=NRL+results+scores&hl=en-AU&gl=AU&ceid=AU:en",
        "https://www.espn.com/espn/rss/nrl/news",
    ],
    "afl": [
        "https://www.afl.com.au/rss/news",
        "https://www.theage.com.au/rss/sport/afl.xml",
        "https://www.abc.net.au/news/feed/52278/rss.xml",
        "https://wwos.nine.com.au/rss",
        "https://www.news.com.au/content-feeds/latest-news-sport/",
        "https://news.google.com/rss/search?q=AFL+results+scores&hl=en-AU&gl=AU&ceid=AU:en",
        "https://www.espn.com/espn/rss/afl/news",
    ],
    "football": [
        "https://www.theguardian.com/football/rss",
        "https://feeds.bbci.co.uk/sport/football/rss.xml",
        "https://www.espn.com/espn/rss/soccer/news",
        "https://theathletic.com/rss/",
        "https://www.skysports.com/rss/12040",
        "https://news.google.com/rss/search?q=football+soccer+results+scores&hl=en-AU&gl=AU&ceid=AU:en",
        "https://news.google.com/rss/search?q=World+Cup+2026+football&hl=en-AU&gl=AU&ceid=AU:en",
    ],
    "nba": [
        "https://feeds.bbci.co.uk/sport/basketball/rss.xml",
        "https://www.espn.com/espn/rss/nba/news",
        "https://theathletic.com/rss/",
        "https://news.google.com/rss/search?q=NBA+results+scores&hl=en-AU&gl=AU&ceid=AU:en",
    ],
    "golf": [
        "https://www.espn.com/espn/rss/golf/news",
        "https://feeds.bbci.co.uk/sport/golf/rss.xml",
        "https://www.pgatour.com/rss/news.xml",
        "https://theathletic.com/rss/",
        "https://news.google.com/rss/search?q=golf+PGA+leaderboard+results&hl=en-AU&gl=AU&ceid=AU:en",
    ],
    "cricket": [
        "https://www.espn.com/espn/rss/cricket/news",
        "https://www.abc.net.au/news/feed/52278/rss.xml",
        "https://news.google.com/rss/search?q=Australia+cricket+Test+ODI+T20&hl=en-AU&gl=AU&ceid=AU:en",
        "https://news.google.com/rss/search?q=IPL+cricket+Australian+players&hl=en-AU&gl=AU&ceid=AU:en",
        "https://news.google.com/rss/search?q=Australia+women+cricket&hl=en-AU&gl=AU&ceid=AU:en",
    ],
    "f1": [
        "https://www.espn.com/espn/rss/f1/news",
        "https://feeds.bbci.co.uk/sport/formula1/rss.xml",
        "https://www.autosport.com/rss/f1/news/",
        "https://www.motorsport.com/rss/f1/news/",
        "https://www.skysports.com/rss/12433",
        "https://news.google.com/rss/search?q=Formula+1+F1+race+results&hl=en-AU&gl=AU&ceid=AU:en",
    ],
    "us_sport": [
        "https://www.espn.com/espn/rss/mlb/news",
        "https://www.espn.com/espn/rss/nhl/news",
        "https://www.espn.com/espn/rss/nfl/news",
        "https://theathletic.com/rss/",
        "https://www.si.com/rss/si_topstories.rss",
        "https://news.google.com/rss/search?q=MLB+baseball+results+scores&hl=en-AU&gl=AU&ceid=AU:en",
        "https://news.google.com/rss/search?q=NHL+hockey+playoff+results&hl=en-AU&gl=AU&ceid=AU:en",
    ],
    "rugby_union": [
        "https://feeds.bbci.co.uk/sport/rugby-union/rss.xml",
        "https://www.theguardian.com/sport/rugby-union/rss",
        "https://www.skysports.com/rss/12977",
        "https://news.google.com/rss/search?q=rugby+union+Super+Rugby+results&hl=en-AU&gl=AU&ceid=AU:en",
    ],
    "cycling": [
        # Activated during major races: Giro (May), Tour de France (July), Vuelta (Sep)
        "https://www.cyclingnews.com/rss.xml",
        "https://feeds.bbci.co.uk/sport/cycling/rss.xml",
        "https://news.google.com/rss/search?q=cycling+Giro+Tour+de+France+results&hl=en-AU&gl=AU&ceid=AU:en",
    ],
    "ai_sport": [
        "https://www.sporttechie.com/feed",
        "https://www.frontofficesports.com/feed/",
        "https://www.sportspromedia.com/feed/",
        "https://news.google.com/rss/search?q=AI+sport+technology+analytics&hl=en-AU&gl=AU&ceid=AU:en",
        "https://news.google.com/rss/search?q=sport+technology+data+analytics&hl=en-AU&gl=AU&ceid=AU:en",
        "https://news.google.com/rss/search?q=VAR+technology+football+sport&hl=en-AU&gl=AU&ceid=AU:en",
        "https://news.google.com/rss/search?q=wearable+technology+sport+performance&hl=en-AU&gl=AU&ceid=AU:en",
    ],
}

SIMILARITY_THRESHOLD = 0.75


# ---------------------------------------------------------------------------
# Fetch & deduplicate
# ---------------------------------------------------------------------------
def fetch_entries(feeds: dict, hours_override: int = 0) -> dict:
    aest_now = datetime.now(ZoneInfo("Australia/Sydney"))
    is_monday = aest_now.weekday() == 0
    is_thursday = aest_now.weekday() == 3
    if hours_override:
        base_hours = hours_override
    else:
        base_hours = 120 if is_monday else (48 if is_thursday else 24)
    cutoff_default = datetime.now(timezone.utc) - timedelta(hours=base_hours)
    cutoff_ai = datetime.now(timezone.utc) - timedelta(hours=max(base_hours, 72))
    results = {k: [] for k in feeds}

    for cat, urls in feeds.items():
        cutoff = cutoff_ai if cat == "ai_sport" else cutoff_default
        for url in urls:
            try:
                old_timeout = socket.getdefaulttimeout()
                socket.setdefaulttimeout(10)
                try:
                    feed = feedparser.parse(url)
                finally:
                    socket.setdefaulttimeout(old_timeout)
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
# ESPN scoreboard
# ---------------------------------------------------------------------------
ESPN_SCOREBOARDS = {
    "Football": "https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard",
    "NBA":      "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard",
    "Golf":     "https://site.api.espn.com/apis/site/v2/sports/golf/pga/scoreboard",
    "Cricket":  "https://site.api.espn.com/apis/site/v2/sports/cricket/scoreboard",
    "F1":       "https://site.api.espn.com/apis/site/v2/sports/racing/f1/scoreboard",
    "MLB":      "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard",
    "NHL":      "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard",
}


def _fetch_nrl_scores() -> tuple[str, list[dict], int]:
    """Fetch NRL scores. Returns (prompt_text, structured_results, round_number)."""
    aest = ZoneInfo("Australia/Sydney")
    season = datetime.now(aest).year
    current_round, current_fixtures = 0, []
    for rnd in range(1, 30):
        try:
            url = f"https://www.nrl.com/draw/data?competition=111&round={rnd}&season={season}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as r:
                data = json.loads(r.read())
            fulltime = [f for f in data.get("fixtures", []) if f.get("matchState") == "FullTime"]
            if not fulltime:
                break
            current_round, current_fixtures = rnd, fulltime
        except Exception:
            break

    results = []
    lines = []
    if current_fixtures:
        lines.append(f"--- NRL Round {current_round} ---")
        for f in current_fixtures:
            home = f.get("homeTeam", {})
            away = f.get("awayTeam", {})
            h_name = home.get("nickName", "?")
            a_name = away.get("nickName", "?")
            h_score = home.get("score", "?")
            a_score = away.get("score", "?")
            draw = h_score == a_score
            results.append({"home": h_name, "away": a_name, "home_score": h_score, "away_score": a_score, "draw": draw})
            lines.append(f"  {h_name} {h_score} def. {a_name} {a_score}" if not draw
                         else f"  {h_name} {h_score} — {a_name} {a_score} (Draw)")
        lines.append("")
    return "\n".join(lines), results, current_round


def _fetch_afl_scores() -> tuple[str, list[dict], int]:
    """Fetch AFL scores. Returns (prompt_text, structured_results, round_number)."""
    aest = ZoneInfo("Australia/Sydney")
    year = datetime.now(aest).year
    current_round, current_games = 0, []
    for rnd in range(1, 30):
        try:
            url = f"https://api.squiggle.com.au/?q=games;year={year};round={rnd}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 SportingBrief/1.0"})
            with urllib.request.urlopen(req, timeout=8) as r:
                data = json.loads(r.read())
            games = [g for g in data.get("games", []) if g.get("timestr") == "Full Time"]
            if not games:
                break
            current_round, current_games = rnd, games
        except Exception:
            break

    results = []
    lines = []
    if current_games:
        lines.append(f"--- AFL Round {current_round} ---")
        for g in current_games:
            h_name = g.get("hteam", "?")
            a_name = g.get("ateam", "?")
            h_score = g.get("hscore", "?")
            a_score = g.get("ascore", "?")
            draw = h_score == a_score
            results.append({"home": h_name, "away": a_name, "home_score": h_score, "away_score": a_score, "draw": draw})
            lines.append(f"  {h_name} {h_score} def. {a_name} {a_score}" if not draw
                         else f"  {h_name} {h_score} — {a_name} {a_score} (Draw)")
        lines.append("")
    return "\n".join(lines), results, current_round


def fetch_scores() -> tuple[str, dict]:
    """Returns (prompt_text, structured) where structured has nrl/afl results."""
    lines = ["=== LIVE SCORES & RESULTS ===\n"]
    structured = {"nrl": [], "nrl_round": 0, "afl": [], "afl_round": 0}

    # NRL — nrl.com
    try:
        nrl_text, nrl_results, nrl_round = _fetch_nrl_scores()
        if nrl_text:
            lines.append(nrl_text)
            structured["nrl"] = nrl_results
            structured["nrl_round"] = nrl_round
            print("  NRL scores: OK")
    except Exception as ex:
        print(f"  WARN NRL scores: {ex}")

    # AFL — Squiggle
    try:
        afl_text, afl_results, afl_round = _fetch_afl_scores()
        if afl_text:
            lines.append(afl_text)
            structured["afl"] = afl_results
            structured["afl_round"] = afl_round
            print("  AFL scores: OK")
    except Exception as ex:
        print(f"  WARN AFL scores: {ex}")

    # ESPN — Football, NBA, Golf
    for sport, url in ESPN_SCOREBOARDS.items():
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
            events = data.get("events", [])
            if not events:
                print(f"  ESPN {sport}: no events")
                continue
            print(f"  ESPN {sport}: {len(events)} event(s)")
            lines.append(f"--- {sport} ---")
            for event in events[:10]:
                status = event.get("status", {}).get("type", {}).get("description", "")
                comps = event.get("competitions", [{}])[0]
                competitors = comps.get("competitors", [])
                if len(competitors) == 2:
                    home = competitors[0]
                    away = competitors[1]
                    lines.append(
                        f"  {home.get('team',{}).get('displayName','?')} {home.get('score','?')} — "
                        f"{away.get('score','?')} {away.get('team',{}).get('displayName','?')} [{status}]"
                    )
            lines.append("")
        except Exception as ex:
            print(f"  WARN ESPN {sport}: {ex}")

    return "\n".join(lines), structured


# ---------------------------------------------------------------------------
# Claude CLI summarisation — per-sport pipeline
# ---------------------------------------------------------------------------

# (feed_key, display_label, tag, max_stories, special_notes)
SPORT_SECTIONS = [
    ("nrl",      "NRL",                       "NRL",       6, ""),
    ("afl",      "AFL",                        "AFL",       6, ""),
    ("football", "Football/Soccer",            "FOOTBALL",  8, ""),
    ("cricket",  "Cricket",                    "CRICKET",   5,
     "Australian Men's and Women's national teams only, plus Australians in the IPL. Ignore County Championship and non-Australian domestic cricket."),
    ("f1",       "Formula 1",                  "F1",        5, "RESULT format: 'Winner: Name, P2: Name' or omit."),
    ("nba",      "NBA",                        "NBA",       5, ""),
    ("us_sport", "MLB/NHL",                    "US_SPORT",  5, ""),
    ("golf",     "Golf",                       "GOLF",      5, "RESULT format: 'Leader: Name -12' or omit."),
    ("ai_sport", "AI, Business & Technology",  "AI_SPORT",  5,
     "Cover: AI/data analytics, broadcast tech, sports business deals, stadium tech, player tracking, club ownership/finance. Name the specific technology, company, or deal. If no genuine story exists, write exactly: NO_CONTENT"),
]


def build_sport_prompt(label: str, tag: str, entries: list, scores_text: str, mode: str, special_notes: str = "") -> str:
    is_preview = mode == "preview"
    if tag == "AI_SPORT":
        overview_instr = f"2-3 sentences covering the most interesting AI, business, or technology stories in sport. Put each sentence on its own line. {special_notes}"
    elif is_preview:
        overview_instr = (
            f"2-3 sentences previewing the most important {label} fixtures this week. "
            "Lead with the biggest game. Put each sentence on its own line. Facts only — specific teams, days, and context."
        )
    else:
        overview_instr = (
            f"2-3 sentences covering the biggest {label} results from the weekend. "
            "Lead with the headline result. Put each sentence on its own line. Facts only — scores, names, key details."
        )

    result_hint = special_notes if tag in ("F1", "GOLF") else "score e.g. 'Sharks def. Tigers 52-10', or omit if unknown"

    lines = [
        f"You are writing the {label} section of a weekend sports digest for Australian fans.",
        "Produce output in EXACTLY this format — no extra text, no preamble:\n",
        f"{tag}_OVERVIEW_START",
        overview_instr,
        f"{tag}_OVERVIEW_END\n",
        f"2 most important {label} stories (use EXACTLY this block format):",
        f"{tag}_STORY_START",
        "TITLE: <headline>",
        "SOURCE: <outlet name>",
        "URL: <url>",
        f"RESULT: <{result_hint}>",
        "SUMMARY: <1 sentence — score first, key detail second>",
        f"{tag}_STORY_END\n",
        "RULES:",
        "1. Specific names only — players, coaches, teams. Never 'a player' or 'the star'.",
        "2. Always include the score when reporting a result.",
        "3. If a fact is not in the source data, omit it — do not write 'unavailable'.",
        "4. No colour writing, no drama. Pure information.",
    ]
    if special_notes and tag not in ("F1", "GOLF", "AI_SPORT"):
        lines.append(f"5. {special_notes}")

    lines.append(f"\n=== {label.upper()} STORIES ===")
    for item in entries:
        lines.append(f"[{item['source']}] {item['title']}")
        if item.get("url"):
            lines.append(f"  {item['url']}")

    if scores_text:
        lines.append(f"\n=== LIVE SCORES (reference only) ===\n{scores_text}")

    return "\n".join(lines)


def build_briefing_prompt(sport_summaries: dict, mode: str) -> str:
    is_preview = mode == "preview"
    if is_preview:
        instr = (
            "Write a WEEK PREVIEW in 3-4 paragraphs. Podcast presenter voice — conversational but authoritative.\n"
            "Cover the 4-6 most significant upcoming fixtures. Group related fixtures into the same paragraph.\n"
            "Separate each paragraph with a blank line. Do not put every sentence on its own line.\n"
            "End with a sentence on what to watch for this weekend."
        )
    else:
        instr = (
            "Write a WEEKEND WRAP in 3-4 paragraphs. Podcast presenter voice — conversational but authoritative.\n"
            "Cover the 4-6 most significant stories. Specific names and scores required — e.g. 'Antonelli won Miami' not 'a driver extended their lead'.\n"
            "Group related stories into the same paragraph. Separate each paragraph with a blank line. Do not put every sentence on its own line.\n"
            "End with a sentence on what's coming up next weekend."
        )

    lines = [
        "You are writing the opening briefing for a weekend sports digest.",
        instr,
        "No bullet points, no bold headings, no sport labels. Flowing prose only.\n",
        "BRIEFING_START",
        "[3-4 paragraphs separated by blank lines]",
        "BRIEFING_END\n",
        "=== SPORT SUMMARIES ===",
    ]
    for sport_label, overview in sport_summaries.items():
        if overview and overview.strip().upper() not in ("NO_CONTENT", ""):
            lines.append(f"{sport_label}: {overview}")
    return "\n".join(lines)


def call_claude(prompt: str, retries: int = 2, timeout: int = 120) -> str:
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
            for key in ("TITLE", "SOURCE", "URL", "RESULT", "SUMMARY"):
                if line.startswith(f"{key}:"):
                    item[key.lower()] = line[len(key)+1:].strip()
        if item:
            items.append(item)
    return items


def parse_response(raw: str) -> dict:
    return {
        "briefing":            _extract(raw, "BRIEFING"),
        "nrl_overview":        _extract(raw, "NRL_OVERVIEW"),
        "nrl_stories":         _extract_blocks(raw, "NRL_STORY"),
        "afl_overview":        _extract(raw, "AFL_OVERVIEW"),
        "afl_stories":         _extract_blocks(raw, "AFL_STORY"),
        "football_overview":   _extract(raw, "FOOTBALL_OVERVIEW"),
        "football_stories":    _extract_blocks(raw, "FOOTBALL_STORY"),
        "cricket_overview":    _extract(raw, "CRICKET_OVERVIEW"),
        "cricket_stories":     _extract_blocks(raw, "CRICKET_STORY"),
        "f1_overview":         _extract(raw, "F1_OVERVIEW"),
        "f1_stories":          _extract_blocks(raw, "F1_STORY"),
        "us_sport_overview":   _extract(raw, "US_SPORT_OVERVIEW"),
        "us_sport_stories":    _extract_blocks(raw, "US_SPORT_STORY"),
        "nba_overview":        _extract(raw, "NBA_OVERVIEW"),
        "nba_stories":         _extract_blocks(raw, "NBA_STORY"),
        "golf_overview":       _extract(raw, "GOLF_OVERVIEW"),
        "golf_stories":        _extract_blocks(raw, "GOLF_STORY"),
        "ai_sport_overview":   _extract(raw, "AI_SPORT_OVERVIEW"),
        "ai_sport_stories":    _extract_blocks(raw, "AI_SPORT_STORY"),
    }


# ---------------------------------------------------------------------------
# HTML rendering
# ---------------------------------------------------------------------------
def _e(s: str) -> str:
    return html.escape(s or "")


def _story_card(item: dict) -> str:
    result = item.get("result", "").strip()
    result_html = (
        f'<p style="margin:0 0 8px;display:inline-block;font-size:12px;font-weight:700;color:#fff;background:#111;font-family:Arial,sans-serif;padding:3px 10px;letter-spacing:.03em;">{_e(result)}</p>'
        if result and result.upper() != "N/A" else ""
    )
    return f"""
<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:20px;">
  <tr><td style="padding-bottom:16px;border-bottom:1px solid #eee;">
    <p style="margin:0 0 4px;font-size:11px;color:#888;font-family:Arial,sans-serif;text-transform:uppercase;letter-spacing:.05em;">{_e(item.get('source',''))}</p>
    {result_html}
    <p style="margin:0 0 6px;font-size:17px;font-weight:700;color:#111;line-height:1.35;font-family:Georgia,serif;"><a href="{_e(item.get('url',''))}" style="color:#111;text-decoration:none;">{_e(item.get('title',''))}</a></p>
    <p style="margin:0;font-size:14px;color:#444;line-height:1.6;font-family:Arial,sans-serif;">{_e(item.get('summary',''))}</p>
  </td></tr>
</table>"""


def _results_table(results: list[dict], round_num: int, label: str) -> str:
    if not results:
        return ""
    rows = ""
    for r in results:
        home_bold = r["home_score"] > r["away_score"] if not r["draw"] else False
        away_bold = r["away_score"] > r["home_score"] if not r["draw"] else False
        h_style = "font-weight:700;color:#111;" if home_bold else "color:#444;"
        a_style = "font-weight:700;color:#111;" if away_bold else "color:#444;"
        rows += f"""
    <tr>
      <td style="padding:7px 8px;font-size:13px;font-family:Arial,sans-serif;{h_style}text-align:right;">{_e(r['home'])}</td>
      <td style="padding:7px 4px;font-size:14px;font-weight:700;color:#111;font-family:Arial,sans-serif;text-align:center;width:28px;">{r['home_score']}</td>
      <td style="padding:7px 2px;font-size:11px;color:#aaa;font-family:Arial,sans-serif;text-align:center;width:16px;">–</td>
      <td style="padding:7px 4px;font-size:14px;font-weight:700;color:#111;font-family:Arial,sans-serif;text-align:center;width:28px;">{r['away_score']}</td>
      <td style="padding:7px 8px;font-size:13px;font-family:Arial,sans-serif;{a_style}">{_e(r['away'])}</td>
    </tr>"""
    return f"""
<p style="margin:0 0 8px;font-size:11px;color:#888;text-transform:uppercase;letter-spacing:.08em;font-family:Arial,sans-serif;">{_e(label)} — Round {round_num} Results</p>
<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:24px;border-collapse:collapse;">
  <tbody>{rows}
  </tbody>
</table>"""


def _section(label: str, overview: str, stories: list, accent: str = "#111", results_html: str = "") -> str:
    stories_html = "".join(_story_card(s) for s in stories)
    para_style = 'margin:0 0 14px;font-size:16px;color:#222;line-height:1.75;font-family:Georgia,serif;'
    paras = [p.strip() for p in re.split(r'\n{2,}', overview.strip()) if p.strip()]
    overview_html = "".join(f'<p style="{para_style}">{_e(p)}</p>' for p in paras) if paras else ""
    return f"""
  <tr><td style="padding:0 48px 32px;">
    <p style="margin:0 0 20px;font-size:11px;color:#888;letter-spacing:.12em;text-transform:uppercase;font-family:Arial,sans-serif;">{_e(label)}</p>
    <h2 style="margin:0 0 10px;font-size:14px;font-weight:700;color:#111;text-transform:uppercase;letter-spacing:.08em;font-family:Arial,sans-serif;border-left:3px solid {accent};padding-left:10px;">Overview</h2>
    {overview_html}
    {results_html}
    {stories_html}
  </td></tr>
  <tr><td style="padding:0 48px;"><hr style="border:none;border-top:1px solid #ddd;margin:0 0 32px;"></td></tr>"""


def render_html(d: dict, date_str: str, edition_label: str = "Weekend Wrap", scores: dict = None) -> str:
    def _render_briefing(raw: str) -> str:
        html_parts = []
        para_style = 'margin:0 0 16px;font-size:16px;color:#333;line-height:1.75;font-family:Georgia,serif;'
        # Split into paragraphs on blank lines or newlines, render each as its own <p>
        paragraphs = [p.strip() for p in re.split(r'\n{2,}|\n', raw.strip()) if p.strip()]
        for para in paragraphs:
            html_parts.append(f'<p style="{para_style}">{_e(para)}</p>')
        return ''.join(html_parts)

    briefing_html = _render_briefing(d["briefing"])
    scores = scores or {}

    nrl_table = _results_table(scores.get("nrl", []), scores.get("nrl_round", 0), "NRL") if scores.get("nrl") else ""
    afl_table = _results_table(scores.get("afl", []), scores.get("afl_round", 0), "AFL") if scores.get("afl") else ""

    sections = (
        _section("NRL", d["nrl_overview"], d["nrl_stories"][:3], results_html=nrl_table) +
        _section("AFL", d["afl_overview"], d["afl_stories"][:3], results_html=afl_table) +
        _section("Football", d["football_overview"], d["football_stories"][:3]) +
        _section("Cricket", d["cricket_overview"], d["cricket_stories"][:2]) +
        _section("Formula 1", d["f1_overview"], d["f1_stories"][:2]) +
        _section("NBA", d["nba_overview"], d["nba_stories"][:2]) +
        _section("MLB / NHL", d["us_sport_overview"], d["us_sport_stories"][:2]) +
        _section("Golf", d["golf_overview"], d["golf_stories"][:2]) +
        (_section("AI, Business & Technology", d["ai_sport_overview"], d["ai_sport_stories"][:2])
         if d.get("ai_sport_overview", "").strip().upper() != "NO_CONTENT" else "")
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>The Sporting Brief – {date_str}</title></head>
<body style="margin:0;padding:0;background:#f5f4f0;font-family:Georgia,serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f4f0;padding:40px 16px;">
<tr><td align="center">
<table width="620" cellpadding="0" cellspacing="0" style="max-width:620px;width:100%;background:#fff;">

  <!-- Header -->
  <tr><td style="padding:40px 48px 24px;border-bottom:3px solid #111;">
    <p style="margin:0 0 6px;font-size:11px;color:#888;letter-spacing:.15em;text-transform:uppercase;font-family:Arial,sans-serif;">{date_str}</p>
    <h1 style="margin:0;font-size:40px;font-weight:700;color:#111;font-family:Georgia,serif;letter-spacing:-1px;line-height:1;">The Sporting Brief</h1>
    <p style="margin:4px 0 0;font-size:11px;color:#888;letter-spacing:.12em;text-transform:uppercase;font-family:Arial,sans-serif;">{_e(edition_label)}</p>
  </td></tr>

  <!-- Briefing -->
  <tr><td style="padding:32px 48px 0;">
    <p style="margin:0 0 20px;font-size:11px;color:#888;letter-spacing:.12em;text-transform:uppercase;font-family:Arial,sans-serif;">Today's Briefing</p>
    {briefing_html}
  </td></tr>

  <tr><td style="padding:0 48px;"><hr style="border:none;border-top:1px solid #ddd;margin:8px 0 32px;"></td></tr>

  {sections}

  <!-- Footer -->
  <tr><td style="padding:24px 48px;border-top:2px solid #111;">
    <table width="100%" cellpadding="0" cellspacing="0">
      <tr>
        <td><p style="margin:0;font-size:12px;color:#888;font-family:Arial,sans-serif;">Your daily sports briefing</p></td>
        <td align="right">
          <a href="mailto:hello@theoperatingbrief.com?subject=Subscribe%20to%20The%20Sporting%20Brief" style="font-size:11px;color:#111;font-family:Arial,sans-serif;text-decoration:none;border-bottom:1px solid #111;padding-bottom:1px;margin-right:16px;">Subscribe</a>
          <a href="mailto:hello@theoperatingbrief.com?subject=Unsubscribe%20from%20The%20Sporting%20Brief" style="font-size:11px;color:#888;font-family:Arial,sans-serif;text-decoration:none;border-bottom:1px solid #ccc;padding-bottom:1px;">Unsubscribe</a>
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
    result = sb.table("sports_subscribers").select("email,token").eq("active", True).execute()
    print(f"  {len(result.data)} active subscriber(s)")
    return result.data


def log_send(subject: str, recipient_count: int, resend_id: str) -> None:
    try:
        sb = get_supabase()
        sb.table("sports_send_log").insert({
            "subject": subject,
            "recipient_count": recipient_count,
            "resend_id": resend_id,
        }).execute()
    except Exception as ex:
        print(f"  WARN: could not log send: {ex}")


def save_edition(slug: str, subject: str, preview_text: str, html_body: str) -> None:
    try:
        sb = get_supabase()
        sb.table("sports_editions").upsert({
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
        "from": os.environ.get("SPORTS_FROM_EMAIL", "brief@theoperatingbrief.com"),
        "to": to,
        "reply_to": os.environ.get("SPORTS_REPLY_TO_EMAIL", "hello@theoperatingbrief.com"),
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
        unsub_url = f"https://thesportingbrief.com/unsubscribe?token={token}"
        sub_url = "https://thesportingbrief.com"
        personalised = base_html.replace(
            'href="mailto:hello@theoperatingbrief.com?subject=Subscribe%20to%20The%20Sporting%20Brief"',
            f'href="{sub_url}"'
        ).replace(
            'href="mailto:hello@theoperatingbrief.com?subject=Unsubscribe%20from%20The%20Sporting%20Brief"',
            f'href="{unsub_url}"'
        )
        resend_id = send_email([email], subject, personalised)
        resend_ids.append(resend_id)
    return resend_ids


# ---------------------------------------------------------------------------
# Ingest — fetch + summarise per sport + store in DB
# ---------------------------------------------------------------------------
def run_ingest(mode: str, backfill: bool = False) -> None:
    aest = ZoneInfo("Australia/Sydney")
    today = datetime.now(aest).date()
    sb = get_supabase()

    hours = 336 if backfill else 0  # 14 days if backfill, else auto by weekday
    if backfill:
        print("Fetching RSS feeds (14-day backfill)…")
    else:
        print("Fetching RSS feeds…")
    entries = fetch_entries(FEEDS, hours_override=hours)
    total = sum(len(v) for v in entries.values())
    print(f"  {total} stories total after deduplication")
    if total == 0:
        print("No stories found. Exiting.")
        return

    scores_text, _ = fetch_scores()

    print("Summarising with Claude (per-sport)…")
    for feed_key, label, tag, max_stories, special_notes in SPORT_SECTIONS:
        sport_entries = entries.get(feed_key, [])[:max_stories]
        if not sport_entries and feed_key != "ai_sport":
            print(f"  [{label}] skipped — no stories")
            continue
        prompt = build_sport_prompt(label, tag, sport_entries, scores_text, mode, special_notes)
        print(f"  [{label}] {len(prompt):,} chars — calling Claude…")
        raw = call_claude(prompt)
        overview = _extract(raw, f"{tag}_OVERVIEW")
        stories = _extract_blocks(raw, f"{tag}_STORY")
        try:
            sb.table("sports_daily_summaries").upsert({
                "summary_date": str(today),
                "sport": feed_key,
                "overview": overview,
                "stories": stories[:2],
            }, on_conflict="summary_date,sport").execute()
            print(f"  [{label}] stored — {len(stories)} stories")
        except Exception as ex:
            print(f"  WARN [{label}] DB write failed: {ex}")

    print("Ingest complete ✅")


# ---------------------------------------------------------------------------
# Compile — load from DB + write briefing + render
# ---------------------------------------------------------------------------
def compile_digest(mode: str, days_back: int = 14) -> tuple[dict, dict]:
    """Load stored sport summaries, generate briefing. Returns (digest, scores_structured)."""
    aest = ZoneInfo("Australia/Sydney")
    cutoff = (datetime.now(aest).date() - timedelta(days=days_back)).isoformat()
    sb = get_supabase()

    print("Loading sport summaries from DB…")
    result = sb.table("sports_daily_summaries") \
        .select("summary_date, sport, overview, stories") \
        .gte("summary_date", cutoff) \
        .order("summary_date", desc=True) \
        .execute()

    # Most recent row per sport
    sport_rows: dict[str, dict] = {}
    for row in result.data:
        if row["sport"] not in sport_rows:
            sport_rows[row["sport"]] = row
    print(f"  {len(sport_rows)} sport(s) loaded from DB")

    digest: dict = {
        "briefing": "",
        "nrl_overview": "", "nrl_stories": [],
        "afl_overview": "", "afl_stories": [],
        "football_overview": "", "football_stories": [],
        "cricket_overview": "", "cricket_stories": [],
        "f1_overview": "", "f1_stories": [],
        "nba_overview": "", "nba_stories": [],
        "us_sport_overview": "", "us_sport_stories": [],
        "golf_overview": "", "golf_stories": [],
        "ai_sport_overview": "", "ai_sport_stories": [],
    }
    sport_summaries: dict[str, str] = {}
    for feed_key, label, tag, _, _ in SPORT_SECTIONS:
        if feed_key in sport_rows:
            row = sport_rows[feed_key]
            digest[f"{feed_key}_overview"] = row.get("overview") or ""
            digest[f"{feed_key}_stories"] = row.get("stories") or []
            sport_summaries[label] = row.get("overview") or ""

    print("  [Briefing] calling Claude…")
    briefing_prompt = build_briefing_prompt(sport_summaries, mode)
    raw = call_claude(briefing_prompt)
    digest["briefing"] = _extract(raw, "BRIEFING")
    print(f"  [Briefing] done — {len(digest['briefing'])} chars")

    _, scores_structured = fetch_scores()
    return digest, scores_structured


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    import argparse, webbrowser
    parser = argparse.ArgumentParser()
    parser.add_argument("--ingest", action="store_true",
                        help="Fetch stories, summarise per sport, store in DB. Run daily.")
    parser.add_argument("--backfill", action="store_true",
                        help="Use with --ingest: fetch 14 days of RSS articles instead of the normal window.")
    parser.add_argument("--preview", action="store_true",
                        help="Compile from DB and open in browser — no email sent.")
    parser.add_argument("--mode", choices=["wrap", "preview"], default=None,
                        help="Edition mode: 'wrap' (results) or 'preview' (week ahead). Auto-detected if not set.")
    args = parser.parse_args()

    aest = ZoneInfo("Australia/Sydney")
    now_aest = datetime.now(aest)
    date_str = now_aest.strftime("%B %d, %Y")

    if args.mode:
        mode = args.mode
    else:
        mode = "preview" if now_aest.weekday() in (3, 4) else "wrap"

    edition_label = "Week Preview" if mode == "preview" else "Weekend Wrap"
    print(f"Mode: {edition_label}")

    # --- INGEST MODE ---
    if args.ingest:
        run_ingest(mode, backfill=getattr(args, "backfill", False))
        return

    # --- COMPILE / SEND MODE ---
    subject = f"The Sporting Brief – {edition_label} – {date_str}"
    digest, scores_structured = compile_digest(mode)

    print("Rendering HTML…")
    html_body = render_html(digest, date_str, edition_label, scores=scores_structured)

    if args.preview:
        path = os.path.join(os.path.dirname(__file__), "preview_sports.html")
        with open(path, "w") as f:
            f.write(html_body)
        print(f"Preview saved → {path}")
        webbrowser.open(f"file://{path}")
        print("Opened in browser. Nothing was sent.")
        return

    print("Saving edition to archive…")
    slug = now_aest.strftime("%Y-%m-%d") + f"-{mode}"
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
