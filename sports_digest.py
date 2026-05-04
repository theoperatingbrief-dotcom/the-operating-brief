#!/usr/bin/env python3
"""
Daily Sports Digest — The Sporting Brief
Covers NRL, AFL, Football/Soccer, NBA, and AI in Sport.
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
def fetch_entries(feeds: dict) -> dict:
    aest_now = datetime.now(ZoneInfo("Australia/Sydney"))
    is_monday = aest_now.weekday() == 0
    is_thursday = aest_now.weekday() == 3
    base_hours = 120 if is_monday else (48 if is_thursday else 24)
    cutoff_default = datetime.now(timezone.utc) - timedelta(hours=base_hours)
    cutoff_ai = datetime.now(timezone.utc) - timedelta(hours=72)
    results = {k: [] for k in feeds}

    for cat, urls in feeds.items():
        cutoff = cutoff_ai if cat == "ai_sport" else cutoff_default
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
# Claude CLI summarisation
# ---------------------------------------------------------------------------
def build_prompt(entries: dict, scores: str = "", mode: str = "wrap") -> str:
    is_preview = mode == "preview"

    if is_preview:
        briefing_instruction = (
            "Write a 400-word WEEK PREVIEW with bold headings: **NRL**, **AFL**, **Football**, **Cricket**, **F1**, **NBA**, **MLB/NHL**, **Golf**.\n"
            "Each section: 2-4 bullet points of key fixtures and storylines. Format: '• Team A v Team B (Day) — key context.'\n"
            "Cricket: Australian Men's and Women's national teams only, plus Australians in the IPL. Skip County Championship and non-Australian domestic cricket.\n"
            "Facts only. Specific names, teams, and dates. No editorial framing."
        )
        overview_instruction = "1-sentence preview of the most important {sport} fixture this week. Format: '[Team] host/face [Team] on [day], with [key context].' No editorial framing — just the fact."
        summary_instruction = "2 sentences — preview focus: who's playing, what's at stake, key players to watch."
    else:
        briefing_instruction = (
            "Write a WEEKEND WRAP briefing in 3-4 short paragraphs — no bullet points, no bold headings, no sport-by-sport structure.\n"
            "This is the opening of a weekend sports podcast. Write like a presenter walking the listener through what happened — conversational but authoritative.\n"
            "Each paragraph covers a cluster of related stories. Cover the 4-6 most significant stories across all sports. Specific names and scores must be included — e.g. 'Kimi Antonelli won the Miami Grand Prix for the third consecutive race' not 'a driver extended their championship lead'.\n"
            "Separate each paragraph with a blank line.\n"
            "Cricket: Australian Men's and Women's national teams only, plus Australians in the IPL.\n"
            "No dramatic framing, no colour writing. Just the facts, told in a natural spoken voice.\n"
            "End the final paragraph with a single sentence pointing to what's coming up next weekend."
        )
        overview_instruction = "1-sentence factual summary of the biggest {sport} result from the weekend. Format: '[Team] defeated [Team] [score], with [key detail].' No editorial framing — just the fact."
        summary_instruction = "2 sentences — result focus: include the score in the first sentence, key moment or player in the second."

    lines = [
        f"You are producing a {'week preview' if is_preview else 'weekend wrap'} sports digest for Australian sports fans with a global outlook.",
        "Based on the stories and scoreboard data below, produce output in EXACTLY this format — no extra text:\n",

        "GLOBAL RULES — follow these exactly for every section:",
        "1. Always use specific names — players, coaches, teams. Never say 'a player', 'the superstar', 'a coach'.",
        "2. Always include the scoreline when reporting a result. Never say 'won' or 'defeated' without the score.",
        "3. If a score or fact is not in the source data, leave it out entirely. Do NOT write 'no score was confirmed' or 'score unavailable' — just omit it.",
        "4. In the BRIEFING section: flowing prose only — no bullet points, no bold headings. In the STORY sections: include the score in RESULT field.",
        "5. No colour writing, no dramatic framing, no vague descriptors. Pure information.",
        "6. Cut every unnecessary word. 'Holding off a second-half comeback' not 'holding off a second-half comeback attempt'. 'Cook kicked the winner' not 'Cook kicked what proved to be the winner'.\n",

        "BRIEFING_START",
        briefing_instruction,
        "No stage directions, no script labels. Clean readable prose only.",
        "BRIEFING_END\n",

        f"NRL_OVERVIEW_START",
        overview_instruction.format(sport="NRL"),
        "NRL_OVERVIEW_END\n",

        "STORY BLOCK RULES: RESULT = score e.g. 'Roosters def. Broncos 38-24', omit if unknown. SUMMARY = 1 sentence, score first, key detail second.\n",

        "2 most important NRL stories:",
        "NRL_STORY_START\nTITLE: <title>\nSOURCE: <source>\nURL: <url>\nRESULT: <score or omit>\nSUMMARY: <1 sentence>\nNRL_STORY_END\n",

        "AFL_OVERVIEW_START",
        overview_instruction.format(sport="AFL"),
        "AFL_OVERVIEW_END\n",

        "2 most important AFL stories:",
        "AFL_STORY_START\nTITLE: <title>\nSOURCE: <source>\nURL: <url>\nRESULT: <score or omit>\nSUMMARY: <1 sentence>\nAFL_STORY_END\n",

        "FOOTBALL_OVERVIEW_START",
        overview_instruction.format(sport="Football/Soccer"),
        "FOOTBALL_OVERVIEW_END\n",

        "2 most important football stories:",
        "FOOTBALL_STORY_START\nTITLE: <title>\nSOURCE: <source>\nURL: <url>\nRESULT: <score or omit>\nSUMMARY: <1 sentence>\nFOOTBALL_STORY_END\n",

        "CRICKET_OVERVIEW_START",
        overview_instruction.format(sport="Cricket"),
        "CRICKET focus: Australian Men's and Women's national teams only, plus Australian players in the IPL. Ignore County Championship and non-Australian domestic cricket entirely.",
        "CRICKET_OVERVIEW_END\n",

        "2 most important cricket stories (Australian teams/players only):",
        "CRICKET_STORY_START\nTITLE: <title>\nSOURCE: <source>\nURL: <url>\nRESULT: <score or omit>\nSUMMARY: <1 sentence>\nCRICKET_STORY_END\n",

        "F1_OVERVIEW_START",
        overview_instruction.format(sport="Formula 1"),
        "F1_OVERVIEW_END\n",

        "2 most important F1 stories:",
        "F1_STORY_START\nTITLE: <title>\nSOURCE: <source>\nURL: <url>\nRESULT: <e.g. 'Winner: Antonelli, P2: Norris' or omit>\nSUMMARY: <1 sentence>\nF1_STORY_END\n",

        "NBA_OVERVIEW_START",
        overview_instruction.format(sport="NBA"),
        "NBA_OVERVIEW_END\n",

        "2 most important NBA stories:",
        "NBA_STORY_START\nTITLE: <title>\nSOURCE: <source>\nURL: <url>\nRESULT: <score or omit>\nSUMMARY: <1 sentence>\nNBA_STORY_END\n",

        "US_SPORT_OVERVIEW_START",
        overview_instruction.format(sport="US Sport (MLB/NHL)"),
        "US_SPORT_OVERVIEW_END\n",

        "2 most important MLB/NHL stories:",
        "US_SPORT_STORY_START\nTITLE: <title>\nSOURCE: <source>\nURL: <url>\nRESULT: <score or omit>\nSUMMARY: <1 sentence>\nUS_SPORT_STORY_END\n",

        "GOLF_OVERVIEW_START",
        overview_instruction.format(sport="Golf"),
        "GOLF_OVERVIEW_END\n",

        "2 most important golf stories:",
        "GOLF_STORY_START\nTITLE: <title>\nSOURCE: <source>\nURL: <url>\nRESULT: <e.g. 'Leader: Scheffler -12' or omit>\nSUMMARY: <1 sentence>\nGOLF_STORY_END\n",

        "AI_SPORT_OVERVIEW_START",
        "1-sentence snapshot of the most interesting AI, business, or technology story in sport. Cover: AI/data analytics, broadcast tech, sports business deals, stadium tech, player tracking, club ownership/finance. Name the specific technology, company, or deal. If none exists in the sources write exactly: NO_CONTENT",
        "AI_SPORT_OVERVIEW_END\n",

        "Up to 2 AI, business & technology in sport stories (only if genuine — no puff pieces):",
        "AI_SPORT_STORY_START\nTITLE: <title>\nSOURCE: <source>\nURL: <url>\nSUMMARY: <1 sentence — name specific technology, company, or deal>\nAI_SPORT_STORY_END\n",

        "=== STORIES ===\n",
    ]
    if scores:
        lines.insert(-1, scores)
        lines.insert(-1, "")

    limits = {"nrl": 6, "afl": 6, "football": 8, "cricket": 5, "f1": 5,
              "nba": 5, "us_sport": 5, "golf": 5, "rugby_union": 4, "cycling": 4, "ai_sport": 5}
    for cat, items in entries.items():
        lines.append(f"--- {cat.upper()} ---")
        for item in items[:limits.get(cat, 10)]:
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
    return f"""
  <tr><td style="padding:0 48px 32px;">
    <p style="margin:0 0 20px;font-size:11px;color:#888;letter-spacing:.12em;text-transform:uppercase;font-family:Arial,sans-serif;">{_e(label)}</p>
    <h2 style="margin:0 0 10px;font-size:14px;font-weight:700;color:#111;text-transform:uppercase;letter-spacing:.08em;font-family:Arial,sans-serif;border-left:3px solid {accent};padding-left:10px;">Overview</h2>
    <p style="margin:0 0 24px;font-size:16px;color:#222;line-height:1.75;font-family:Georgia,serif;">{_e(overview)}</p>
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
          <a href="mailto:hello@thesportingbrief.com?subject=Subscribe%20to%20The%20Sporting%20Brief" style="font-size:11px;color:#111;font-family:Arial,sans-serif;text-decoration:none;border-bottom:1px solid #111;padding-bottom:1px;margin-right:16px;">Subscribe</a>
          <a href="mailto:hello@thesportingbrief.com?subject=Unsubscribe%20from%20The%20Sporting%20Brief" style="font-size:11px;color:#888;font-family:Arial,sans-serif;text-decoration:none;border-bottom:1px solid #ccc;padding-bottom:1px;">Unsubscribe</a>
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
        "from": os.environ.get("SPORTS_FROM_EMAIL", "brief@thesportingbrief.com"),
        "to": to,
        "reply_to": os.environ.get("SPORTS_REPLY_TO_EMAIL", "hello@thesportingbrief.com"),
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
            'href="mailto:hello@thesportingbrief.com?subject=Subscribe%20to%20The%20Sporting%20Brief"',
            f'href="{sub_url}"'
        ).replace(
            'href="mailto:hello@thesportingbrief.com?subject=Unsubscribe%20from%20The%20Sporting%20Brief"',
            f'href="{unsub_url}"'
        )
        resend_id = send_email([email], subject, personalised)
        resend_ids.append(resend_id)
    return resend_ids


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    import argparse, webbrowser
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", action="store_true", help="Generate HTML and open in browser without sending")
    parser.add_argument("--mode", choices=["wrap", "preview"], default=None,
                        help="Edition mode: 'wrap' (Thursday, weekend results) or 'preview' (Monday, week ahead). Auto-detected from day of week if not set.")
    args = parser.parse_args()

    aest = ZoneInfo("Australia/Sydney")
    now_aest = datetime.now(aest)
    date_str = now_aest.strftime("%B %d, %Y")

    # Auto-detect mode: Thursday = week preview (upcoming weekend), Monday = weekend wrap (results)
    if args.mode:
        mode = args.mode
    else:
        mode = "preview" if now_aest.weekday() == 3 else "wrap"

    edition_label = "Week Preview" if mode == "preview" else "Weekend Wrap"
    subject = f"The Sporting Brief – {edition_label} – {date_str}"
    print(f"Mode: {edition_label}")

    print("Fetching RSS feeds…")
    entries = fetch_entries(FEEDS)
    total = sum(len(v) for v in entries.values())
    print(f"  {total} stories total after deduplication")

    if total == 0:
        print("No stories found. Exiting.")
        return

    print("Fetching live scores from ESPN…")
    scores_text, scores_structured = fetch_scores()

    print("Summarising with Claude…")
    prompt = build_prompt(entries, scores_text, mode)
    print(f"  Prompt length: {len(prompt):,} chars (~{len(prompt)//4:,} tokens)")
    raw = call_claude(prompt)

    with open("debug_claude_response.txt", "w") as f:
        f.write(raw)

    print("Parsing response…")
    digest = parse_response(raw)
    print(f"  briefing: {len(digest['briefing'])} chars")
    print(f"  nrl_overview: {len(digest['nrl_overview'])} chars")
    print(f"  afl_overview: {len(digest['afl_overview'])} chars")

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
    slug = datetime.now(aest).strftime("%Y-%m-%d") + f"-{mode}"
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
