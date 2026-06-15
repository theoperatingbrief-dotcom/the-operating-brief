#!/usr/bin/env python3
"""
Daily Sports Digest — The Sporting Brief
Covers NRL, AFL, Football/Soccer, NBA, and AI in Sport.
Same architecture as daily_digest.py. Run with --preview to check output locally.
"""
import os
import re
import sys
import html
import time
import socket
import difflib
import subprocess  # still used for macOS `open` command
import anthropic
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

# Additional feeds used for AFL/NRL on Thursdays — preview/fixture focused rather than results
FEEDS_THURSDAY_PREVIEW = {
    "afl": [
        "https://www.afl.com.au/rss/news",
        "https://www.theage.com.au/rss/sport/afl.xml",
        "https://www.abc.net.au/news/feed/52278/rss.xml",
        "https://wwos.nine.com.au/rss",
        "https://news.google.com/rss/search?q=AFL+Round+preview+fixtures+weekend&hl=en-AU&gl=AU&ceid=AU:en",
        "https://news.google.com/rss/search?q=AFL+Round+tips+team+selections+2025&hl=en-AU&gl=AU&ceid=AU:en",
        "https://news.google.com/rss/search?q=AFL+injury+news+team+list+this+week&hl=en-AU&gl=AU&ceid=AU:en",
    ],
    "nrl": [
        "https://www.nrl.com/rss/latest-news/",
        "https://www.foxsports.com.au/rss",
        "https://www.abc.net.au/news/feed/52278/rss.xml",
        "https://wwos.nine.com.au/rss",
        "https://news.google.com/rss/search?q=NRL+Round+preview+fixtures+weekend&hl=en-AU&gl=AU&ceid=AU:en",
        "https://news.google.com/rss/search?q=NRL+Round+tips+team+selections+2025&hl=en-AU&gl=AU&ceid=AU:en",
        "https://news.google.com/rss/search?q=NRL+injury+news+team+list+this+week&hl=en-AU&gl=AU&ceid=AU:en",
    ],
}

SIMILARITY_THRESHOLD = 0.75


# ---------------------------------------------------------------------------
# Fetch & deduplicate
# ---------------------------------------------------------------------------
def fetch_entries(feeds: dict, hours_override: int = 0, preview_feed_keys: set[str] | None = None) -> dict:
    aest_now = datetime.now(ZoneInfo("Australia/Sydney"))
    is_monday = aest_now.weekday() == 0
    is_preview_day = aest_now.weekday() in (3, 4)
    preview_feed_keys = preview_feed_keys or set()
    if hours_override:
        base_hours = hours_override
    else:
        base_hours = 120 if is_monday else (48 if is_preview_day else 24)
    cutoff_default = datetime.now(timezone.utc) - timedelta(hours=base_hours)
    cutoff_ai = datetime.now(timezone.utc) - timedelta(hours=max(base_hours, 72))
    results = {k: [] for k in feeds}

    for cat, urls in feeds.items():
        # On Thursday/Friday previews, AFL/NRL need fixture-focused feeds.
        # Friday can be a hybrid: one round game may already be complete, with the rest still ahead.
        if (is_preview_day or cat in preview_feed_keys) and cat in FEEDS_THURSDAY_PREVIEW:
            urls = FEEDS_THURSDAY_PREVIEW[cat]
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
                            "summary": _clean_summary(e.get("summary") or e.get("description") or ""),
                        })
            except Exception as ex:
                print(f"  WARN {url}: {ex}")
        results[cat] = _dedupe(results[cat])
        print(f"  {cat}: {len(results[cat])} stories")

    return results


def _clean_summary(raw: str) -> str:
    text = re.sub(r"<[^>]+>", " ", raw or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:500]


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


def _fetch_nrl_scores(mode: str = "auto") -> tuple[str, list[dict], int]:
    """Fetch NRL scores. Returns (prompt_text, structured_results, round_number)."""
    aest = ZoneInfo("Australia/Sydney")
    season = datetime.now(aest).year
    rounds = []
    for rnd in range(1, 30):
        try:
            url = f"https://www.nrl.com/draw/data?competition=111&round={rnd}&season={season}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as r:
                data = json.loads(r.read())
            all_fixtures = data.get("fixtures", [])
            if all_fixtures:
                rounds.append((rnd, all_fixtures))
        except Exception:
            break

    active_round, current_round_all = 0, []
    if mode == "wrap":
        for rnd, fixtures in reversed(rounds):
            if any(f.get("matchState") == "FullTime" for f in fixtures):
                active_round, current_round_all = rnd, fixtures
                break
    else:
        for rnd, fixtures in rounds:
            if any(f.get("matchState") != "FullTime" for f in fixtures):
                active_round, current_round_all = rnd, fixtures
                break
    if not current_round_all:
        for rnd, fixtures in reversed(rounds):
            if any(f.get("matchState") == "FullTime" for f in fixtures):
                active_round, current_round_all = rnd, fixtures
                break

    current_fixtures = [f for f in current_round_all if f.get("matchState") == "FullTime"]
    upcoming = [] if mode == "wrap" else [f for f in current_round_all if f.get("matchState") != "FullTime"]
    results = []
    lines = []
    if current_fixtures:
        lines.append(f"--- NRL Round {active_round} Completed ---")
        for f in current_fixtures:
            home = f.get("homeTeam", {})
            away = f.get("awayTeam", {})
            h_name = home.get("nickName", "?")
            a_name = away.get("nickName", "?")
            h_score = home.get("score", "?")
            a_score = away.get("score", "?")
            draw = h_score == a_score
            results.append({"home": h_name, "away": a_name, "home_score": h_score, "away_score": a_score, "draw": draw})
            if draw:
                lines.append(f"  {h_name} {h_score} — {a_name} {a_score} (Draw)")
            elif int(h_score) > int(a_score):
                lines.append(f"  {h_name} def. {a_name} {h_score}-{a_score}")
            else:
                lines.append(f"  {a_name} def. {h_name} {a_score}-{h_score}")
    if upcoming:
        lines.append(f"--- NRL Round {active_round} Upcoming ---")
        for f in upcoming:
            home = f.get("homeTeam", {})
            away = f.get("awayTeam", {})
            h_name = home.get("nickName", "?")
            a_name = away.get("nickName", "?")
            clock = f.get("clock") or {}
            kickoff = clock.get("kickOffTimeLong") if isinstance(clock, dict) else ""
            kickoff = kickoff or f.get("matchStart") or f.get("startTime") or f.get("date") or ""
            venue = f.get("venue") or ""
            detail = " — ".join(part for part in (kickoff, venue) if part)
            lines.append(f"  {h_name} v {a_name}" + (f" — {detail}" if detail else ""))
    if current_fixtures or upcoming:
        lines.append("")
    return "\n".join(lines), results, active_round, upcoming


def _fetch_afl_scores(mode: str = "auto") -> tuple[str, list[dict], int]:
    """Fetch AFL scores. Returns (prompt_text, structured_results, round_number)."""
    aest = ZoneInfo("Australia/Sydney")
    year = datetime.now(aest).year
    rounds = []
    for rnd in range(1, 30):
        try:
            url = f"https://api.squiggle.com.au/?q=games;year={year};round={rnd}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 SportingBrief/1.0"})
            with urllib.request.urlopen(req, timeout=8) as r:
                data = json.loads(r.read())
            all_games = data.get("games", [])
            if all_games:
                rounds.append((rnd, all_games))
        except Exception:
            break

    active_round, current_round_all = 0, []
    if mode == "wrap":
        for rnd, games in reversed(rounds):
            if any(g.get("timestr") == "Full Time" for g in games):
                active_round, current_round_all = rnd, games
                break
    else:
        for rnd, games in rounds:
            if any(g.get("timestr") != "Full Time" for g in games):
                active_round, current_round_all = rnd, games
                break
    if not current_round_all:
        for rnd, games in reversed(rounds):
            if any(g.get("timestr") == "Full Time" for g in games):
                active_round, current_round_all = rnd, games
                break

    current_games = [g for g in current_round_all if g.get("timestr") == "Full Time"]
    upcoming = [] if mode == "wrap" else [g for g in current_round_all if g.get("timestr") != "Full Time"]
    results = []
    lines = []
    if current_games:
        lines.append(f"--- AFL Round {active_round} Completed ---")
        for g in current_games:
            h_name = g.get("hteam", "?")
            a_name = g.get("ateam", "?")
            h_score = g.get("hscore", "?")
            a_score = g.get("ascore", "?")
            draw = h_score == a_score
            results.append({"home": h_name, "away": a_name, "home_score": h_score, "away_score": a_score, "draw": draw})
            if draw:
                lines.append(f"  {h_name} {h_score} — {a_name} {a_score} (Draw)")
            elif int(h_score) > int(a_score):
                lines.append(f"  {h_name} def. {a_name} {h_score}-{a_score}")
            else:
                lines.append(f"  {a_name} def. {h_name} {a_score}-{h_score}")
    if upcoming:
        lines.append(f"--- AFL Round {active_round} Upcoming ---")
        for g in upcoming:
            h_name = g.get("hteam", "?")
            a_name = g.get("ateam", "?")
            when = g.get("timestr") or g.get("localtime") or g.get("date") or ""
            venue = g.get("venue") or ""
            detail = " — ".join(part for part in (when, venue) if part)
            lines.append(f"  {h_name} v {a_name}" + (f" — {detail}" if detail else ""))
    if current_games or upcoming:
        lines.append("")
    return "\n".join(lines), results, active_round, upcoming


def fetch_scores(mode: str = "auto") -> tuple[str, dict]:
    """Returns (prompt_text, structured) where structured has nrl/afl results."""
    lines = ["=== LIVE SCORES & RESULTS ===\n"]
    structured = {"nrl": [], "nrl_round": 0, "nrl_upcoming": [], "afl": [], "afl_round": 0, "afl_upcoming": []}

    # NRL — nrl.com
    try:
        nrl_text, nrl_results, nrl_round, nrl_upcoming = _fetch_nrl_scores(mode)
        if nrl_text:
            lines.append(nrl_text)
            structured["nrl"] = nrl_results
            structured["nrl_round"] = nrl_round
            structured["nrl_upcoming"] = nrl_upcoming
            print("  NRL scores: OK")
    except Exception as ex:
        print(f"  WARN NRL scores: {ex}")

    # AFL — Squiggle
    try:
        afl_text, afl_results, afl_round, afl_upcoming = _fetch_afl_scores(mode)
        if afl_text:
            lines.append(afl_text)
            structured["afl"] = afl_results
            structured["afl_round"] = afl_round
            structured["afl_upcoming"] = afl_upcoming
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


def _dynamic_round_mode(feed_key: str, requested_mode: str, scores_structured: dict) -> str:
    if feed_key not in ("afl", "nrl") or requested_mode != "preview":
        return requested_mode

    completed = scores_structured.get(feed_key) or []
    upcoming = scores_structured.get(f"{feed_key}_upcoming") or []
    if completed and upcoming:
        return "round_preview"
    if upcoming:
        return "thursday_preview"
    return "wrap"


# ---------------------------------------------------------------------------
# Claude CLI summarisation — per-sport pipeline
# ---------------------------------------------------------------------------

# (feed_key, display_label, tag, max_stories, special_notes)
SPORT_SECTIONS = [
    ("afl",      "AFL",                        "AFL",       6, ""),
    ("nrl",      "NRL",                       "NRL",       6, ""),
    ("football", "Football/Soccer",            "FOOTBALL",  8, ""),
    ("cricket",  "Cricket",                    "CRICKET",   5,
     "Australian Men's and Women's national teams only, plus Australians in the IPL. Ignore County Championship and non-Australian domestic cricket."),
    ("f1",       "Formula 1",                  "F1",        5, "RESULT format: 'Winner: Name, P2: Name' or omit. Only report if a race or sprint took place in the last 3 days. If no race or sprint took place in the last 3 days, write exactly: NO_CONTENT"),
    ("nba",      "NBA",                        "NBA",       5, ""),
    ("us_sport", "MLB/NHL",                    "US_SPORT",  5, ""),
    ("golf",     "Golf",                       "GOLF",      5, "RESULT format: 'Leader: Name -12' or omit."),
    ("ai_sport", "AI, Business & Technology",  "AI_SPORT",  5,
     "Cover: AI/data analytics, broadcast tech, sports business deals, stadium tech, player tracking, club ownership/finance. Name the specific technology, company, or deal. If no genuine story exists, write exactly: NO_CONTENT"),
]


def build_sport_prompt(label: str, tag: str, entries: list, scores_text: str, mode: str, special_notes: str = "") -> str:
    is_thursday_preview = mode == "thursday_preview"
    is_round_preview = mode == "round_preview"
    is_preview = mode in ("preview", "thursday_preview", "round_preview")
    if tag == "AI_SPORT":
        overview_instr = f"2-3 sentences on a secondary AI, business, or technology story in sport — not the lead story already covered in the opening briefing. Sharp, punchy, active voice. Each sentence on its own line. {special_notes}"
    elif tag == "F1":
        overview_instr = (
            "2-3 sentences on the most recent Formula 1 race. If a race occurred, the first sentence must name the Grand Prix winner and winning team. "
            "Then add the decisive race detail, retirement, podium, or championship implication from the source data. "
            "Do not lead with paddock comments, regulation threats, or car-performance quotes when a race result is available. "
            f"Each sentence on its own line. {special_notes}"
        )
    elif tag == "FOOTBALL":
        overview_instr = (
            "2-3 sentences on the biggest football story. If a major league season has just ended, lead with the champion, relegated teams, and European qualifiers before individual match colour. "
            "For preview editions, do not list Premier League final-day results that were already wrap material; focus on current trophies, finals, appointments, transfer/ownership stories, or upcoming fixtures. "
            "Name the competition and clubs. Do not confuse teams from different competitions or finals. The tournament starting on 11 June 2026 is the FIFA World Cup 26, not the Club World Cup. "
            "Use Sunderland/Chelsea-style surprise stories only after the title/relegation/Europe picture is clear. Each sentence on its own line."
        )
    elif is_round_preview:
        overview_instr = (
            f"2-3 sentences previewing the upcoming {label} weekend while acknowledging any completed round game already played. "
            "First, briefly state the completed result if the source data or live scores include one from the current round. "
            "Then preview the key remaining fixture or team-selection storyline. "
            "Do not treat the whole round as complete. Do not ignore State of Origin if it is part of this week's context. "
            "Specific teams and players only. Each sentence on its own line."
        )
    elif is_thursday_preview:
        overview_instr = (
            f"2-3 sentences previewing the upcoming {label} weekend — the key fixture, what's at stake, and recent form. "
            "Specific teams and players only. Do not report upcoming events as completed results. Each sentence on its own line."
        )
    elif is_preview:
        overview_instr = (
            f"2-3 sentences on a secondary {label} story this week — not the headline fixture already covered in the opening briefing. "
            "Sharp, punchy, active voice. Specific teams, names, scores. Each sentence on its own line."
        )
    else:
        overview_instr = (
            f"2-3 sentences on a secondary {label} story from the weekend — not the headline result already covered in the opening briefing. "
            "Sharp, punchy, active voice. Scores and names required. Each sentence on its own line."
        )

    if is_round_preview:
        result_hint = "completed score e.g. 'Bulldogs def. Storm 30-20' OR upcoming fixture e.g. 'Broncos v Storm, Sat 7:30pm AEST'"
    elif is_thursday_preview:
        result_hint = "upcoming fixture e.g. 'Broncos v Storm, Sat 7:30pm AEST', or omit"
    elif tag in ("F1", "GOLF"):
        result_hint = special_notes
    else:
        result_hint = "score e.g. 'Sharks def. Tigers 52-10', or omit if unknown"

    if is_round_preview:
        digest_label = "round-so-far weekend preview"
    elif is_thursday_preview:
        digest_label = "Thursday weekend preview"
    else:
        digest_label = "weekend sports digest"
    lines = [
        f"You are writing the {label} section of a {digest_label} for Australian fans.",
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
        "1. Specific names only — players, coaches, teams. Never 'a player', 'the star', 'a key figure'.",
        "2. Include scores for completed games and scheduled date/time for upcoming fixtures when known. Clearly label which is which." if is_round_preview else
        "2. Always include the score when reporting a result." if not is_thursday_preview else
            "2. Include scheduled date/time when known. Do not invent scores for upcoming matches.",
        "3. This is a hybrid round preview: report completed current-round games as results, then preview remaining fixtures. Do not imply the round is complete."
            if is_round_preview else
        "3. Report upcoming weekend fixtures only — do not report past results or imply milestones have been reached."
            if is_thursday_preview else
            "3. Only report events that have already occurred. Do not report upcoming fixtures as results.\n"
            "   Do not complete or anticipate milestones — if a record or milestone is upcoming, omit it entirely.",
        "4. Only use facts, quotes, scores, venues, and statistics that appear verbatim in the source data.",
        "   If it is not in the source data, omit it. Do not infer, estimate, or fill gaps from general knowledge.",
        "   Never invent or guess a venue. If the venue is not present, omit the venue.",
        "5. If reporting an injury, name the player. Never write generic descriptors like 'a promising young Blue',",
        "   'a key player', or 'the star'. If the player is not named in the source data, omit the injury.",
        "6. For Formula 1, a race result outranks paddock/commentary stories. If a Grand Prix or sprint occurred,",
        "   lead the section with the winner and race name.",
        "7. For football, season outcomes outrank single-match colour. If a league season ended, lead with champion,",
        "   relegated clubs, and European qualification before a surprise result.",
        "8. Sharp, punchy prose. Active voice. Short sentences. Every sentence earns its place.",
        "9. BANNED PHRASES — never use: 'notable', 'significant', 'dominant', 'standout', 'decisive',",
        "   'reshaping', 'heading into', 'ladder implications', 'top-four contenders', 'on the verge',",
        "   'further solidifying', 'remains to be seen', 'question marks', 'building momentum',",
        "   'captured attention', 'drew scrutiny', 'attracted interest', 'collectively', 'amid'.",
    ]
    if special_notes and tag not in ("F1", "GOLF", "AI_SPORT"):
        lines.append(f"6. {special_notes}")

    lines.append(f"\n=== {label.upper()} STORIES ===")
    for item in entries:
        lines.append(f"[{item['source']}] {item['title']}")
        if item.get("summary"):
            lines.append(f"  Summary: {item['summary']}")
        if item.get("url"):
            lines.append(f"  {item['url']}")

    if scores_text:
        lines.append(f"\n=== LIVE SCORES (reference only) ===\n{scores_text}")

    return "\n".join(lines)


def _score_briefing_lines(scores: dict) -> list[str]:
    lines = []
    for key, label in (("afl", "AFL"), ("nrl", "NRL")):
        results = scores.get(key, [])
        round_num = scores.get(f"{key}_round", 0)
        if not results:
            continue
        lines.append(f"{label} Round {round_num} results:")
        for r in results:
            home_score = int(r["home_score"])
            away_score = int(r["away_score"])
            if r.get("draw"):
                lines.append(f"- {r['home']} {home_score} drew {r['away']} {away_score}")
            elif home_score > away_score:
                margin = home_score - away_score
                lines.append(f"- {r['home']} def. {r['away']} {home_score}-{away_score} by {margin}")
            else:
                margin = away_score - home_score
                lines.append(f"- {r['away']} def. {r['home']} {away_score}-{home_score} by {margin}")
    return lines


def _result_sentence(r: dict) -> tuple[int, str]:
    home_score = int(r["home_score"])
    away_score = int(r["away_score"])
    if r.get("draw"):
        return 0, f"{r['home']} drew {r['away']} {home_score}-{away_score}"
    if home_score > away_score:
        margin = home_score - away_score
        return margin, f"{r['home']} beat {r['away']} {home_score}-{away_score} by {margin}"
    margin = away_score - home_score
    return margin, f"{r['away']} beat {r['home']} {away_score}-{home_score} by {margin}"


def _round_overview_from_scores(scores: dict, key: str, label: str) -> str:
    results = scores.get(key, [])
    round_num = scores.get(f"{key}_round", 0)
    if not results:
        return ""

    sentences = [_result_sentence(r) for r in results]
    by_margin = sorted(sentences, key=lambda x: x[0], reverse=True)
    close_games = [text for margin, text in sentences if 0 < margin <= 6]
    other_results = [text for _, text in sentences if text not in close_games and text != by_margin[0][1]]

    lines = [
        f"{label} Round {round_num} is complete.",
        f"Biggest margin: {by_margin[0][1]}."
    ]
    if close_games:
        lines.append("Close games: " + "; ".join(close_games) + ".")
    if other_results:
        lines.append("Also: " + "; ".join(other_results[:4]) + ".")
    return "\n".join(lines)


def build_briefing_prompt(sport_summaries: dict, mode: str, is_thursday: bool = False, scores: dict | None = None) -> str:
    is_preview = mode == "preview"
    banned = (
        "BANNED PHRASES — do not use any of these: 'notable', 'significant', 'dominant', 'standout', "
        "'decisive', 'reshaping', 'heading into', 'ladder implications', 'top-four contenders', 'on the verge', "
        "'further solidifying', 'remains to be seen', 'question marks', 'building momentum', "
        "'captured attention', 'drew scrutiny', 'attracted interest', 'collectively', 'amid', "
        "'off the field', 'on the field', 'in the mix', 'keeps their run alive', 'carry significant', "
        "'put on a show', 'dismantling', 'brutal result', 'came down to millimetres', 'told another story', "
        "'the number that defined it', 'tightest result of the round', 'round full of narrow margins', "
        "'genuinely close', 'genuinely brutal', 'the outlier', 'real pressure landed elsewhere', "
        "'left empty-handed again', 'without a single round off'."
    )
    if is_preview:
        instr = (
            "Write a WEEKEND PREVIEW in 5-7 short paragraphs. Sharp, punchy, active voice. Short sentences. Every sentence earns its place — no padding.\n"
            "Open with AFL (first) and NRL. Use the schedule state in the summaries: some sports may be pure upcoming fixtures, some may be round-so-far plus weekend ahead, and NRL may include State of Origin context.\n"
            "For AFL and NRL, acknowledge completed current-round games or Origin only when present, then preview the key remaining weekend fixtures. State who is playing, recent form, and what is at stake.\n"
            "For football, do not list old Premier League results that were likely covered in the Monday wrap. In a preview edition, only include football if there is a current trophy, final, appointment, or upcoming fixture that matters now.\n"
            "For FIFA stories, be precise: 11 June 2026 is the FIFA World Cup 26 kickoff, not the Club World Cup kickoff.\n"
            "After football, split other sports by sport rather than merging them into one 'Elsewhere' paragraph. Use separate short paragraphs for Golf, NBA, and MLB/NHL when each has a worthwhile item.\n"
            "Do not add filler transition phrases such as 'with the rest of the round unfolding', 'with a full slate of fixtures', 'headlining a full slate', 'the weekend continues', or 'the stage is set'. Name the fixture and why it matters, then stop.\n"
            "Do not call anything the 'game of the weekend', 'pick of the round', 'pick of the weekend', 'marquee fixture', or similar. Mention fixtures once in context only.\n"
            "Do not add performative stakes sentences such as 'both clubs know what is at stake', 'this one has genuine edge', 'as good as the NRL gets', or 'it should be a cracker'.\n"
            "Do not add a closing 'game of the weekend' paragraph. If a fixture is worth flagging, mention it once in the relevant AFL or NRL paragraph and move on.\n"
            f"{banned}"
        )
    else:
        instr = (
            "Write a WEEKEND WRAP in 4-6 short paragraphs. Sharp, punchy, active voice. Short sentences. Every sentence earns its place — no padding.\n"
            "Write like a sports desk editor filing a premium briefing: specific, economical, unsentimental. No classroom compare-and-contrast framing.\n"
            "The opening briefing is a rundown of key stories, not a scoreboard. Results are not stories by default; they become stories only when tied to title race, ladder position, selection, injuries, coaching, scandal, contracts, money, records, or a named player/coach performance.\n"
            "Lead with AFL, not NRL. The first paragraph should select the 1-2 most important AFL stories from the AFL story blocks and explain why they matter. Do not re-list round results. Use no more than one score or margin, and only if it is essential to the story.\n"
            "The second paragraph should select the 1-2 most important NRL stories from the NRL story blocks and explain why they matter. Do not summarise the round by margin counts or list close games. Use no more than one score or margin, and only if it is essential to the story.\n"
            "Then cover the next 2-4 most important results and stories across other sports. Prefer story consequence over score recitation.\n"
            "The AFL and NRL result tables below carry the full scoreboard. Do not repeat the table in prose.\n"
            "Write like a brief, not a match report: no theatrical framing, no school-essay transitions, no 'making it a round where...' sentences, no vague ladder claims, no sweeping claims unless sourced.\n"
            "State only what changed or what matters. Make every fact count.\n"
            "Do not add a closing forward-looking sentence — end on the last result.\n"
            f"{banned}"
        )

    lines = [
        "You are writing the opening briefing for a weekend sports digest.",
        instr,
        "Australian audience — lead with AFL and NRL, then other sports. Do not open with F1 or international sports.\n",
        "No bullet points, no bold headings, no sport labels. Flowing prose only. Use blank lines between sport/topic paragraphs.\n",
        "Avoid repeating the section summaries or score tables verbatim. Use the opening as a tight synthesis; the sport sections below will carry the detail.\n",
        "STRICT ACCURACY RULES — these override everything else:",
        "1. Only use facts, scores, names, venues, and quotes that appear in LIVE ROUND RESULTS or the sport summaries below.",
        "   Do not draw on general knowledge, training data, or fill gaps by inference.",
        "   Never invent or guess a venue. If the summaries do not include a venue, omit it.",
        "2. In preview mode, clearly separate completed games from upcoming fixtures. Do not report upcoming fixtures, milestones, or records as completed."
            if is_preview else
            "2. Only report events that have already happened. Do not report upcoming fixtures, milestones, or records as completed.",
        "3. Do not mix sports. NRL teams (Warriors, Broncos, Storm, etc.) must never appear in AFL paragraphs, and vice versa.",
        "4. Do not invent or paraphrase quotes. Only include a quote if it appears verbatim in the source summaries.\n",
        "BRIEFING_START",
        "[4-6 paragraphs separated by blank lines]",
        "BRIEFING_END\n",
        "THE_NUMBER_START",
        "STAT: <one standout sports stat from this edition — score, streak, record, margin. Max 6 words. E.g. '44-16', '8 straight wins', '54-point margin'>",
        "CONTEXT: <one sentence explaining what this stat is and why it matters>",
        "THE_NUMBER_END\n",
    ]
    score_lines = _score_briefing_lines(scores or {})
    if score_lines:
        lines.extend(["=== LIVE ROUND RESULTS ===", *score_lines])
    lines.append("=== SPORT SUMMARIES ===")
    for sport_label, overview in sport_summaries.items():
        if overview and overview.strip().upper() not in ("NO_CONTENT", ""):
            lines.append(f"{sport_label}: {overview}")
    return "\n".join(lines)


def call_claude(prompt: str, retries: int = 2, timeout: int = 240) -> str:
    """Call the Anthropic API."""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    model = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6")

    for attempt in range(1, retries + 1):
        print(f"  Calling Anthropic API (attempt {attempt}/{retries}, model={model})...")
        try:
            message = client.messages.create(
                model=model,
                max_tokens=8192,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text
        except Exception as e:
            print(f"  WARN: API call failed on attempt {attempt}: {e}")
            if attempt == retries:
                raise RuntimeError(f"Anthropic API failed after {retries} attempts: {e}")

    raise RuntimeError("Anthropic API failed")


# ---------------------------------------------------------------------------
# Parse Claude response
# ---------------------------------------------------------------------------
def _extract(text: str, tag: str) -> str:
    m = re.search(rf"{tag}_START\s*(.*?)\s*{tag}_END", text, re.DOTALL)
    return m.group(1).strip() if m else ""


def _extract_blocks(text: str, tag: str) -> list[dict]:
    blocks = re.findall(rf"{tag}_START\s*(.*?)\s*{tag}_END", text, re.DOTALL)
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


def _extract_briefing(text: str) -> str:
    tagged = _extract(text, "BRIEFING")
    if tagged:
        return tagged
    fallback = re.split(r"\n\s*-{3,}\s*\n|THE_NUMBER_START|^STAT:", text.strip(), maxsplit=1, flags=re.MULTILINE)[0]
    fallback = re.sub(r"^\s*BRIEFING_START\s*", "", fallback)
    fallback = re.sub(r"\s*BRIEFING_END\s*$", "", fallback)
    return fallback.strip()


def _extract_the_number(text: str) -> tuple[str, str]:
    stat = ""
    context = ""
    the_number_block = re.findall(r"THE_NUMBER_START\s*(.*?)\s*THE_NUMBER_END", text, re.DOTALL)
    source = the_number_block[0] if the_number_block else text
    for line in source.splitlines():
        line = line.strip()
        if line.startswith("STAT:"):
            stat = line[5:].strip()
        elif line.startswith("CONTEXT:"):
            context = line[8:].strip()
    return stat, context


def _clean_preview_filler(text: str) -> str:
    replacements = [
        r",?\s+with the rest of the round unfolding across Saturday and Sunday",
        r",?\s+with a full slate of fixtures to follow across the weekend",
        r",?\s+headlining a full slate of remaining Round \d+ fixtures across the weekend",
        r",?\s+with the round continuing across the weekend",
        r"\s+with the remaining round still to play",
        r",?\s+with both clubs knowing[^.]*",
        r",?\s+with both clubs needing the points",
        r"\s+Both clubs know exactly what is at stake\.",
        r"\s+Both clubs know what is at stake\.",
        r"\s+The Storm don't offer many easy nights at home\.",
        r",?\s+Tedesco fronting up against a Storm side that will want to send a message on their own patch",
        r"\s+The Cats have been[^.]*\. The Blues need[^.]*\.",
        r",?\s+as the weekend continues",
        r"\s+This one has genuine edge\.",
        r"\s+as good as the NRL gets\.",
        r"\s+It should be a cracker\.",
        r"\s+in the pick of Round \d+",
        r"\s+in the pick of the round",
        r"\s+as the pick of Round \d+",
        r"\s+as the pick of the round",
        r"\s*Saturday night's main event is Melbourne Storm hosting the Sydney Roosters at AAMI Park, with Tedesco running straight back into the team that gave him his platform\.",
        r"\.?\s*[A-Z][^.]{0,80}\b(?:v|versus|against)\b[^.]{0,100}game of the round\.",
        r"\.?\s*[A-Z][^.]{0,80}\b(?:v|versus|against)\b[^.]{0,120}game of the weekend\.",
        r"\.?\s*(?:The\s+)?pick of (?:the\s+)?(?:Round \d+|round|weekend|NRL weekend)[^.]*\.",
        r"\.?\s*[A-Z][^.]{0,80}\b(?:v|versus|against)\b[^.]{0,120}marquee fixture[^.]*\.",
    ]
    cleaned = text or ""
    for pattern in replacements:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(
        r"(?:Now\s+)?Carlton host Geelong at the MCG on Friday night[^.]*\.",
        "Carlton host Geelong at the MCG on Friday night.",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"\bMelbourne host (?:Sydney|the Roosters) at AAMI Park\b",
        "Storm host the Roosters at AAMI Park",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"James Tedesco was the difference-maker for NSW, and he lines up for Melbourne against the Roosters at AAMI Park on Saturday night\.",
        "James Tedesco was the difference-maker for NSW, and returns for the Roosters against the Storm at AAMI Park on Saturday night.",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"\s*(?:It's|It is) the fixture of the round\.",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    return cleaned


def _clean_football_competition(text: str) -> str:
    cleaned = text or ""
    cleaned = re.sub(
        r"\bClub World Cup\b(?=[^.]{0,80}\b(?:11 June|June 11|11 Jun|Jun 11)\b)",
        "FIFA World Cup 26",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"\b(?:the\s+)?Club World Cup kicks off on 11 June\b",
        "the FIFA World Cup 26 kicks off on 11 June",
        cleaned,
        flags=re.IGNORECASE,
    )
    return cleaned


def _clean_football_blocks(items: list[dict]) -> list[dict]:
    cleaned_items = []
    for item in items:
        cleaned_items.append({
            key: _clean_football_competition(value) if isinstance(value, str) else value
            for key, value in item.items()
        })
    return cleaned_items


def parse_response(raw: str) -> dict:
    stat, context = _extract_the_number(raw)
    result = {
        "briefing":            _clean_football_competition(_clean_preview_filler(_extract_briefing(raw))),
        "nrl_overview":        _clean_preview_filler(_extract(raw, "NRL_OVERVIEW")),
        "nrl_stories":         _extract_blocks(raw, "NRL_STORY"),
        "afl_overview":        _clean_preview_filler(_extract(raw, "AFL_OVERVIEW")),
        "afl_stories":         _extract_blocks(raw, "AFL_STORY"),
        "football_overview":   _clean_football_competition(_extract(raw, "FOOTBALL_OVERVIEW")),
        "football_stories":    _clean_football_blocks(_extract_blocks(raw, "FOOTBALL_STORY")),
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
        "the_number_stat":     stat,
        "the_number_context":  context,
    }
    return result


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


def _results_table(results: list[dict], round_num: int, label: str, heading: str = "Results") -> str:
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
<p style="margin:0 0 8px;font-size:11px;color:#888;text-transform:uppercase;letter-spacing:.08em;font-family:Arial,sans-serif;">{_e(label)} — Round {round_num} {_e(heading)}</p>
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

    result_heading = "So Far" if "Preview" in edition_label else "Results"
    nrl_table = _results_table(scores.get("nrl", []), scores.get("nrl_round", 0), "NRL", result_heading) if scores.get("nrl") else ""
    afl_table = _results_table(scores.get("afl", []), scores.get("afl_round", 0), "AFL", result_heading) if scores.get("afl") else ""

    sections = (
        _section("AFL", d["afl_overview"], d["afl_stories"][:3], results_html=afl_table) +
        _section("NRL", d["nrl_overview"], d["nrl_stories"][:3], results_html=nrl_table) +
        _section("Football", d["football_overview"], d["football_stories"][:3]) +
        _section("Cricket", d["cricket_overview"], d["cricket_stories"][:2]) +
        (_section("Formula 1", d["f1_overview"], d["f1_stories"][:2])
         if d.get("f1_overview", "").strip().upper() not in ("NO_CONTENT", "") else "") +
        _section("NBA", d["nba_overview"], d["nba_stories"][:2]) +
        _section("MLB / NHL", d["us_sport_overview"], d["us_sport_stories"][:2]) +
        _section("Golf", d["golf_overview"], d["golf_stories"][:2]) +
        (_section("AI, Business & Technology", d["ai_sport_overview"], d["ai_sport_stories"][:2])
         if d.get("ai_sport_overview", "").strip().upper() not in ("NO_CONTENT", "") else "")
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
# Social card — sports stat image (1080x1080, Instagram/LinkedIn ready)
# ---------------------------------------------------------------------------
def generate_sports_card(stat: str, context: str, edition_label: str = "Weekend Wrap") -> str | None:
    if not stat:
        return None
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("  WARN: Pillow not installed — skipping social card. Run: pip install Pillow")
        return None

    W, H = 1080, 1080
    img = Image.new("RGB", (W, H), color="#111111")
    draw = ImageDraw.Draw(img)

    font_dir = "/System/Library/Fonts/Supplemental"
    def font(name, size):
        try:
            return ImageFont.truetype(os.path.join(font_dir, name), size)
        except Exception:
            return ImageFont.load_default()

    label_font   = font("Arial.ttf", 22)
    context_font = font("Georgia.ttf", 34)
    brand_font   = font("Arial.ttf", 20)
    edition_font = font("Arial.ttf", 18)

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

    # Auto-size the stat
    stat_size = 160
    stat_font = font("Georgia Bold.ttf", stat_size)
    stat_lines = []
    while stat_size >= 48:
        stat_lines = wrap_text(stat, stat_font, W - 140)
        if len(stat_lines) <= 3:
            break
        stat_size -= 8
        stat_font = font("Georgia Bold.ttf", stat_size)

    # Edition label (e.g. "WEEK PREVIEW" or "WEEKEND WRAP")
    draw.text((W // 2, 140), edition_label.upper(), font=edition_font, fill="#666666", anchor="mm")

    # "THE NUMBER" label
    draw.text((W // 2, 190), "THE NUMBER", font=label_font, fill="#888888", anchor="mm")
    draw.line([(W // 2 - 60, 226), (W // 2 + 60, 226)], fill="#333333", width=1)

    # Stat — vertically centred
    stat_line_h = stat_size + 12
    stat_block_h = len(stat_lines) * stat_line_h
    stat_y = H // 2 - stat_block_h // 2
    for line in stat_lines:
        draw.text((W // 2, stat_y), line, font=stat_font, fill="#ffffff", anchor="mm")
        stat_y += stat_line_h

    # Context below stat
    context_lines = wrap_text(context, context_font, W - 140)
    y = H // 2 + stat_block_h // 2 + 36
    for line in context_lines:
        draw.text((W // 2, y), line, font=context_font, fill="#cccccc", anchor="mm")
        y += 52

    # Branding
    draw.text((W // 2, H - 100), "The Sporting Brief", font=brand_font, fill="#555555", anchor="mm")

    images_dir = os.path.join(os.path.dirname(__file__), "social_images")
    os.makedirs(images_dir, exist_ok=True)
    slug = datetime.now(ZoneInfo("Australia/Sydney")).strftime("%Y-%m-%d")
    path = os.path.join(images_dir, f"{slug}_sports_card.png")
    img.save(path, "PNG")
    print(f"  Social card saved → {path}")
    return path


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
    print(f"    → {to[0]} ({resend_id})")
    return resend_id


def _sent_log_path() -> str:
    slug = datetime.now(ZoneInfo("Australia/Sydney")).strftime("%Y-%m-%d")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), f".sent_sports_{slug}.json")


def _load_sent_log() -> dict:
    path = _sent_log_path()
    if os.path.exists(path):
        import json as _json
        with open(path) as f:
            return _json.load(f)
    return {}


def _save_sent_log(log: dict) -> None:
    import json as _json
    with open(_sent_log_path(), "w") as f:
        _json.dump(log, f, indent=2)


def send_to_all(subscribers: list[dict], subject: str, base_html: str) -> list[str]:
    resend_ids = []
    failed = []
    sent_log = _load_sent_log()
    skipped = [e for e in sent_log]
    if skipped:
        print(f"  Skipping {len(skipped)} already sent: {', '.join(skipped)}")

    pending = [s for s in subscribers if s["email"] not in sent_log]
    for i, sub in enumerate(pending):
        if i > 0:
            time.sleep(0.6)
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
        try:
            resend_id = send_email([email], subject, personalised)
            resend_ids.append(resend_id)
            sent_log[email] = resend_id
            _save_sent_log(sent_log)
        except Exception as ex:
            print(f"    FAILED {email}: {ex}")
            failed.append(email)
    if failed:
        print(f"  ⚠️  {len(failed)} failed: {', '.join(failed)}")
    return resend_ids


# ---------------------------------------------------------------------------
# Ingest — fetch + summarise per sport + store in DB
# ---------------------------------------------------------------------------
def _f1_race_in_last_3_days() -> bool:
    """Returns True if ESPN's F1 scoreboard shows a completed race in the last 3 days."""
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/racing/f1/scoreboard"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        aest = ZoneInfo("Australia/Sydney")
        cutoff = datetime.now(aest) - timedelta(days=3)
        for event in data.get("events", []):
            status = event.get("status", {}).get("type", {}).get("completed", False)
            date_str = event.get("date", "")
            if status and date_str:
                try:
                    event_dt = datetime.fromisoformat(date_str.replace("Z", "+00:00")).astimezone(aest)
                    if event_dt >= cutoff:
                        return True
                except Exception:
                    pass
    except Exception as ex:
        print(f"  WARN F1 schedule check: {ex}")
    return False


def run_ingest(mode: str, backfill: bool = False) -> None:
    aest = ZoneInfo("Australia/Sydney")
    now_aest = datetime.now(aest)
    today = now_aest.date()
    is_thursday = now_aest.weekday() == 3
    sb = get_supabase()

    hours = 336 if backfill else 0  # 14 days if backfill, else auto by weekday
    scores_text, scores_structured = fetch_scores(mode)
    preview_feed_keys = {
        feed_key for feed_key in ("afl", "nrl")
        if _dynamic_round_mode(feed_key, mode, scores_structured) in ("round_preview", "thursday_preview")
    }
    if backfill:
        print("Fetching RSS feeds (14-day backfill)…")
    else:
        print("Fetching RSS feeds…")
    entries = fetch_entries(FEEDS, hours_override=hours, preview_feed_keys=preview_feed_keys)
    total = sum(len(v) for v in entries.values())
    print(f"  {total} stories total after deduplication")
    if total == 0:
        print("No stories found. Exiting.")
        return

    # Check if F1 had a race in the last 3 days via ESPN schedule
    f1_race_recent = _f1_race_in_last_3_days()

    print("Summarising with Claude (per-sport)…")
    for feed_key, label, tag, max_stories, special_notes in SPORT_SECTIONS:
        sport_entries = entries.get(feed_key, [])[:max_stories]
        if not sport_entries and feed_key != "ai_sport":
            print(f"  [{label}] skipped — no stories")
            continue

        # Skip F1 Claude call entirely if no recent race — store NO_CONTENT directly
        if feed_key == "f1" and not f1_race_recent:
            try:
                sb.table("sports_daily_summaries").upsert({
                    "summary_date": str(today),
                    "sport": "f1",
                    "overview": "NO_CONTENT",
                    "stories": [],
                }, on_conflict="summary_date,sport").execute()
                print(f"  [Formula 1] no race in last 3 days — stored NO_CONTENT")
            except Exception as ex:
                print(f"  WARN [Formula 1] DB write failed: {ex}")
            continue

        # AFL/NRL preview mode is schedule-driven:
        # upcoming only = fixture preview; completed + upcoming = round-so-far preview; completed only = wrap.
        if feed_key in ("afl", "nrl"):
            sport_mode = _dynamic_round_mode(feed_key, mode, scores_structured)
        elif is_thursday:
            sport_mode = "wrap"
        else:
            sport_mode = mode

        prompt = build_sport_prompt(label, tag, sport_entries, scores_text, sport_mode, special_notes)
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
def compile_digest(mode: str, days_back: int = 14, is_thursday: bool = False) -> tuple[dict, dict]:
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
        "the_number_stat": "",
        "the_number_context": "",
    }
    _, scores_structured = fetch_scores(mode)
    sport_summaries: dict[str, str] = {}
    for feed_key, label, tag, _, _ in SPORT_SECTIONS:
        if feed_key in sport_rows:
            row = sport_rows[feed_key]
            overview = row.get("overview") or ""
            if feed_key in {"nrl", "afl"} and mode == "preview":
                overview = _clean_preview_filler(overview)
            if feed_key in {"nrl", "afl"} and mode == "wrap":
                overview = _round_overview_from_scores(scores_structured, feed_key, label) or overview
            digest[f"{feed_key}_overview"] = overview
            digest[f"{feed_key}_stories"] = row.get("stories") or []
            sport_summaries[label] = overview

    print("  [Briefing] calling Claude…")
    briefing_prompt = build_briefing_prompt(sport_summaries, mode, is_thursday=is_thursday, scores=scores_structured)
    raw = call_claude(briefing_prompt)
    briefing_parsed = parse_response(raw)
    digest["briefing"] = briefing_parsed.get("briefing", "")
    digest["the_number_stat"] = briefing_parsed.get("the_number_stat", "")
    digest["the_number_context"] = briefing_parsed.get("the_number_context", "")
    print(f"  [Briefing] done — {len(digest['briefing'])} chars")

    return digest, scores_structured


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def _do_send(html_body: str, subject: str, now_aest, mode: str) -> None:
    slug = now_aest.strftime("%Y-%m-%d") + f"-{mode}"
    edition_label = "Week Preview" if mode == "preview" else "Weekend Wrap"
    preview_text = ""
    print("Saving edition to archive…")
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


def main():
    import argparse, webbrowser
    parser = argparse.ArgumentParser()
    parser.add_argument("--ingest", action="store_true",
                        help="Fetch stories, summarise per sport, store in DB. Run daily.")
    parser.add_argument("--backfill", action="store_true",
                        help="Use with --ingest: fetch 14 days of RSS articles instead of the normal window.")
    parser.add_argument("--preview", action="store_true",
                        help="Ingest, compile, open in browser, then prompt to send.")
    parser.add_argument("--send", action="store_true",
                        help="Send the last saved preview without regenerating.")
    parser.add_argument("--mode", choices=["wrap", "preview"], default=None,
                        help="Edition mode: 'wrap' (results) or 'preview' (week ahead). Auto-detected if not set.")
    args = parser.parse_args()

    aest = ZoneInfo("Australia/Sydney")
    now_aest = datetime.now(aest)
    date_str = now_aest.strftime("%B %d, %Y")
    is_thursday = now_aest.weekday() == 3

    if args.mode:
        mode = args.mode
        is_thursday = False  # explicit --mode override bypasses Thursday logic
    else:
        mode = "preview" if now_aest.weekday() in (3, 4) else "wrap"

    if is_thursday:
        edition_label = "Weekend Preview"
    elif mode == "preview":
        edition_label = "Week Preview"
    else:
        edition_label = "Weekend Wrap"
    print(f"Mode: {edition_label}")

    preview_path = os.path.join(os.path.dirname(__file__), "preview_sports.html")
    subject = f"The Sporting Brief – {edition_label} – {date_str}"

    # --- INGEST ONLY ---
    if args.ingest:
        run_ingest(mode, backfill=getattr(args, "backfill", False))
        return

    # --- SEND SAVED PREVIEW ---
    if args.send:
        if not os.path.exists(preview_path):
            print("No preview found. Run --preview first.")
            return
        with open(preview_path) as f:
            html_body = f.read()
        _do_send(html_body, subject, now_aest, mode)
        return

    # --- INGEST + COMPILE + PREVIEW (then optionally send) ---
    print("Ingesting fresh data…")
    run_ingest(mode, backfill=False)

    days_back = 7 if mode == "wrap" else 5
    digest, scores_structured = compile_digest(mode, days_back=days_back, is_thursday=is_thursday)

    print("Rendering HTML…")
    html_body = render_html(digest, date_str, edition_label, scores=scores_structured)

    with open(preview_path, "w") as f:
        f.write(html_body)
    print(f"Preview saved → {preview_path}")
    webbrowser.open(f"file://{preview_path}")

    # Generate social card from THE NUMBER stat
    card_path = generate_sports_card(
        digest.get("the_number_stat", ""),
        digest.get("the_number_context", ""),
        edition_label,
    )
    if card_path:
        import subprocess as _sp
        _sp.run(["open", card_path])  # opens in Preview on macOS

    if args.preview:
        print(f"  Web preview: https://theoperatingbrief.com/preview/{os.environ.get('PREVIEW_TOKEN', '<PREVIEW_TOKEN>')}")
        if not sys.stdin.isatty():
            print("Running unattended — draft saved. Approve and send from the web preview.")
            return
        print("\nReview the email, then type y to send.\n")
        answer = input("Send to subscribers now? (y/n): ").strip().lower()
        if answer != "y":
            print("Not sent. Run --send when ready.")
            return

    _do_send(html_body, subject, now_aest, mode)


if __name__ == "__main__":
    main()
