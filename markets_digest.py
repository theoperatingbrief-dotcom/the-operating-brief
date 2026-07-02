#!/usr/bin/env python3
"""
Daily Markets Brief — The Markets Brief
ASX pre-market briefing covering overnight US/global markets + macro news from the last 24 hours.
Same architecture as daily_digest.py and sports_digest.py.
Run with --preview to check output locally without sending.
"""
import os
import re
import sys
import html
import time
import difflib
import subprocess  # still used for macOS `open` command
import anthropic
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
    "asx": [
        "https://www.afr.com/rss/feed.xml",
        "https://www.abc.net.au/news/feed/2942820/rss.xml",
        "https://www.smh.com.au/rss/business.xml",
        "https://www.livewiremarkets.com/feed",
        "https://www.fool.com.au/feed/",
        "https://news.google.com/rss/search?q=ASX+Australia+shares+stocks+earnings&hl=en-AU&gl=AU&ceid=AU:en",
        "https://news.google.com/rss/search?q=ASX+company+results+announcement+today&hl=en-AU&gl=AU&ceid=AU:en",
        "https://news.google.com/rss/search?q=ASX+200+market+open+Australian+shares&hl=en-AU&gl=AU&ceid=AU:en",
        "https://news.google.com/rss/search?q=BHP+CBA+CSL+Macquarie+Wesfarmers+ASX&hl=en-AU&gl=AU&ceid=AU:en",
        "https://news.google.com/rss/search?q=ASX+mining+banks+resources+sector&hl=en-AU&gl=AU&ceid=AU:en",
    ],
    "macro": [
        "https://www.rba.gov.au/rss/rss-cb-speeches.xml",
        "https://www.rba.gov.au/rss/rss-cb-media-releases.xml",
        "https://feeds.reuters.com/reuters/businessNews",
        "https://www.theguardian.com/business/rss",
        "https://news.google.com/rss/search?q=RBA+interest+rates+Australia+economy&hl=en-AU&gl=AU&ceid=AU:en",
        "https://news.google.com/rss/search?q=Australia+ABS+GDP+employment+inflation+data&hl=en-AU&gl=AU&ceid=AU:en",
        "https://news.google.com/rss/search?q=Federal+Reserve+Fed+interest+rates&hl=en-AU&gl=AU&ceid=AU:en",
        "https://news.google.com/rss/search?q=inflation+CPI+GDP+economy+data&hl=en-AU&gl=AU&ceid=AU:en",
        "https://news.google.com/rss/search?q=China+economy+growth+stimulus+PBOC&hl=en-AU&gl=AU&ceid=AU:en",
        "https://news.google.com/rss/search?q=Australia+budget+treasury+government+fiscal&hl=en-AU&gl=AU&ceid=AU:en",
    ],
    "global_markets": [
        "https://feeds.marketwatch.com/marketwatch/topstories/",
        "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        "https://feeds.reuters.com/reuters/businessNews",
        "https://news.google.com/rss/search?q=Wall+Street+S%26P+500+Nasdaq+stock+market&hl=en-AU&gl=AU&ceid=AU:en",
        "https://news.google.com/rss/search?q=US+earnings+quarterly+results+tech&hl=en-AU&gl=AU&ceid=AU:en",
        "https://news.google.com/rss/search?q=European+markets+ECB+FTSE+DAX&hl=en-AU&gl=AU&ceid=AU:en",
    ],
    "commodities": [
        "https://feeds.reuters.com/reuters/commoditiesNews",
        "https://news.google.com/rss/search?q=iron+ore+price+China+steel&hl=en-AU&gl=AU&ceid=AU:en",
        "https://news.google.com/rss/search?q=oil+price+OPEC+crude+energy&hl=en-AU&gl=AU&ceid=AU:en",
        "https://news.google.com/rss/search?q=gold+silver+precious+metals+price&hl=en-AU&gl=AU&ceid=AU:en",
        "https://news.google.com/rss/search?q=copper+lithium+battery+metals+mining+Australia&hl=en-AU&gl=AU&ceid=AU:en",
    ],
}

SIMILARITY_THRESHOLD = 0.75

# ---------------------------------------------------------------------------
# Market data — yfinance
# ---------------------------------------------------------------------------
MARKET_TICKERS = [
    # Indices
    {"name": "ASX 200",   "ticker": "^AXJO",    "type": "index",     "group": "Indices"},
    {"name": "S&P 500",   "ticker": "^GSPC",    "type": "index",     "group": "Indices"},
    {"name": "Dow Jones", "ticker": "^DJI",     "type": "index",     "group": "Indices"},
    {"name": "Nasdaq",    "ticker": "^IXIC",    "type": "index",     "group": "Indices"},
    # Currencies
    {"name": "AUD/USD",   "ticker": "AUDUSD=X", "type": "fx",        "group": "FX"},
    {"name": "AUD/GBP",   "ticker": "AUDGBP=X", "type": "fx",        "group": "FX"},
    {"name": "AUD/EUR",   "ticker": "AUDEUR=X", "type": "fx",        "group": "FX"},
    {"name": "AUD/JPY",   "ticker": "AUDJPY=X", "type": "fx",        "group": "FX"},
    # Rates
    {"name": "US 10Y",    "ticker": "^TNX",     "type": "rate",      "group": "Rates"},
    # Commodities
    {"name": "Gold",      "ticker": "GC=F",     "type": "commodity", "group": "Commodities"},
    {"name": "WTI Oil",   "ticker": "CL=F",     "type": "commodity", "group": "Commodities"},
    {"name": "Copper",    "ticker": "HG=F",     "type": "commodity", "group": "Commodities"},
    # Crypto
    {"name": "Bitcoin",   "ticker": "BTC-USD",  "type": "crypto",    "group": "Crypto"},
]

# Top ASX stocks for market movers (by market cap, covering major sectors)
ASX_WATCHLIST = [
    # Big 4 banks + Macquarie
    "CBA.AX", "WBC.AX", "ANZ.AX", "NAB.AX", "MQG.AX",
    # Resources & mining
    "BHP.AX", "RIO.AX", "FMG.AX", "S32.AX", "MIN.AX", "WDS.AX", "STO.AX",
    "NEM.AX", "PLS.AX", "IGO.AX", "LYC.AX", "WHC.AX", "ALD.AX",
    # Healthcare & biotech
    "CSL.AX", "RHC.AX", "SHL.AX", "COH.AX", "RMD.AX", "MPL.AX",
    # Consumer & retail
    "WES.AX", "WOW.AX", "COL.AX", "TWE.AX", "JBH.AX",
    # Tech & growth
    "XRO.AX", "SEK.AX", "CAR.AX", "REA.AX", "WTC.AX", "TNE.AX",
    # Infrastructure & utilities
    "TCL.AX", "APA.AX", "AGL.AX", "ORG.AX", "TLS.AX",
    # Insurance & financial services
    "QBE.AX", "IAG.AX", "SUN.AX", "CPU.AX", "ASX.AX",
    # Property & industrial
    "GMG.AX", "SGP.AX", "GPT.AX", "AMC.AX", "ORI.AX",
    # Other large-cap
    "ALL.AX", "QAN.AX", "RHC.AX",
]
ASX_WATCHLIST = list(dict.fromkeys(ASX_WATCHLIST))  # dedupe while preserving order

ASX_NAMES = {
    "CBA.AX": "CommBank", "WBC.AX": "Westpac", "ANZ.AX": "ANZ",
    "NAB.AX": "NAB", "MQG.AX": "Macquarie",
    "BHP.AX": "BHP", "RIO.AX": "Rio Tinto", "FMG.AX": "Fortescue",
    "S32.AX": "South32", "MIN.AX": "Mineral Resources", "WDS.AX": "Woodside",
    "STO.AX": "Santos", "NEM.AX": "Newmont", "PLS.AX": "Pilbara Minerals",
    "IGO.AX": "IGO", "LYC.AX": "Lynas Rare Earths", "WHC.AX": "Whitehaven Coal",
    "ALD.AX": "Ampol",
    "CSL.AX": "CSL", "RHC.AX": "Ramsay Health", "SHL.AX": "Sonic Healthcare",
    "COH.AX": "Cochlear", "RMD.AX": "ResMed", "MPL.AX": "Medibank",
    "WES.AX": "Wesfarmers", "WOW.AX": "Woolworths", "COL.AX": "Coles",
    "TWE.AX": "Treasury Wine", "JBH.AX": "JB Hi-Fi",
    "XRO.AX": "Xero", "SEK.AX": "Seek", "CAR.AX": "CAR Group",
    "REA.AX": "REA Group", "WTC.AX": "WiseTech", "TNE.AX": "Technology One",
    "TCL.AX": "Transurban", "APA.AX": "APA Group", "AGL.AX": "AGL Energy",
    "ORG.AX": "Origin Energy", "TLS.AX": "Telstra",
    "QBE.AX": "QBE", "IAG.AX": "IAG", "SUN.AX": "Suncorp",
    "CPU.AX": "Computershare", "ASX.AX": "ASX Ltd",
    "GMG.AX": "Goodman Group", "SGP.AX": "Stockland", "GPT.AX": "GPT Group",
    "AMC.AX": "Amcor", "ORI.AX": "Orica",
    "ALL.AX": "Aristocrat", "QAN.AX": "Qantas",
}


def _fmt_value(cfg: dict, close: float) -> str:
    t = cfg["type"]
    if t == "fx":
        return f"{close:.4f}"
    if t == "rate":
        return f"{close:.2f}%"
    if t == "commodity":
        return f"${close:,.2f}"
    if t == "crypto":
        return f"${close:,.0f}"
    return f"{close:,.1f}"


def _fmt_change(cfg: dict, change: float, pct: float) -> tuple[str, str]:
    t = cfg["type"]
    if t == "rate":
        return f"{change*100:+.0f}bp", f"{pct:+.2f}%"
    if t == "fx":
        return f"{change:+.4f}", f"{pct:+.2f}%"
    if t == "commodity":
        return f"{change:+.2f}", f"{pct:+.2f}%"
    if t == "crypto":
        return f"{change:+,.0f}", f"{pct:+.2f}%"
    return f"{change:+.1f}", f"{pct:+.2f}%"


def _last_two_closes(hist):
    """Return (prev_close, last_close, last_date) using only completed trading days."""
    from datetime import date as date_type
    import pandas as pd
    today = datetime.now(ZoneInfo("Australia/Sydney")).date()
    # Drop any row whose date is today — it may be an incomplete intraday candle
    hist = hist.copy()
    hist.index = pd.to_datetime(hist.index).tz_localize(None)
    hist = hist[hist.index.date < today]
    if len(hist) < 2:
        return None, None, None
    last_date = hist.index[-1].date()
    return float(hist["Close"].iloc[-2]), float(hist["Close"].iloc[-1]), last_date


def fetch_market_data() -> tuple[str, list[dict]]:
    """Returns (prompt_text, structured_list)."""
    try:
        import yfinance as yf
    except ImportError:
        print("  WARN: yfinance not installed — run: pip install yfinance")
        return "", []

    structured = []
    aest = ZoneInfo("Australia/Sydney")
    today = datetime.now(aest).date()
    prompt_lines = ["=== MARKET DATA ===\n"]
    last_group = None
    group_dates: dict[str, str] = {}  # group → date label for prompt

    def _date_label(last_date) -> str:
        delta = (today - last_date).days
        if delta == 0:
            return f"today ({last_date})"
        if delta == 1:
            return f"yesterday ({last_date})"
        return f"{last_date.strftime('%A')} {last_date}"

    for cfg in MARKET_TICKERS:
        try:
            ticker = yf.Ticker(cfg["ticker"])

            # Use fast_info for real-time last_price/previous_close where available
            fi = ticker.fast_info
            close = getattr(fi, "last_price", None)
            prev  = getattr(fi, "previous_close", None)

            if not close or not prev:
                # Fall back to history
                hist = ticker.history(period="7d")
                if hist.empty or len(hist) < 2:
                    print(f"  WARN: no data for {cfg['name']} ({cfg['ticker']})")
                    continue
                prev_h, close_h, _ = _last_two_closes(hist)
                if close_h is None:
                    print(f"  WARN: insufficient completed data for {cfg['name']}")
                    continue
                close, prev = close_h, prev_h

            last_date = today - timedelta(days=1)  # best approximation when using fast_info
            change = close - prev
            pct    = (change / prev) * 100
            value_str  = _fmt_value(cfg, close)
            change_str, pct_str = _fmt_change(cfg, change, pct)
            positive = change >= 0
            grp = cfg["group"]

            if grp != last_group:
                dlabel = _date_label(last_date)
                group_dates[grp] = dlabel
                prompt_lines.append(f"{grp} [data from {dlabel}]")
                last_group = grp
            prompt_lines.append(f"  {cfg['name']}: {value_str} ({pct_str})")

            structured.append({
                "name": cfg["name"],
                "value": value_str,
                "change": change_str,
                "pct": pct_str,
                "positive": positive,
                "type": cfg["type"],
                "group": cfg["group"],
            })
            print(f"  {cfg['name']}: {value_str} ({pct_str})")
        except Exception as ex:
            print(f"  WARN {cfg['name']} ({cfg['ticker']}): {ex}")

    # Prepend a session date summary so Claude knows exactly which session each group is from
    if group_dates:
        summary = "IMPORTANT — data session dates (use these to frame your writing correctly):\n"
        summary += "\n".join(f"  {grp}: {dlabel}" for grp, dlabel in group_dates.items())
        summary += "\n"
        prompt_lines.insert(1, summary)

    prompt_lines.append("")
    return "\n".join(prompt_lines), structured


def fetch_asx_movers() -> tuple[str, list[dict], list[dict]]:
    """Returns (prompt_text, gainers, losers) from the previous ASX session."""
    try:
        import yfinance as yf
    except ImportError:
        return "", [], []

    try:
        import pandas as pd
        today = datetime.now(ZoneInfo("Australia/Sydney")).date()
        data = yf.download(ASX_WATCHLIST, period="5d", auto_adjust=True, progress=False)
        closes = data["Close"]
        # Drop today's incomplete candle if present
        closes.index = pd.to_datetime(closes.index).tz_localize(None)
        closes = closes[closes.index.date < today]

        moves = []
        for ticker in ASX_WATCHLIST:
            if ticker not in closes.columns:
                continue
            col = closes[ticker].dropna()
            if len(col) < 2:
                continue
            prev = float(col.iloc[-2])
            last = float(col.iloc[-1])
            if prev == 0:
                continue
            pct = (last - prev) / prev * 100
            moves.append({
                "ticker": ticker.replace(".AX", ""),
                "name": ASX_NAMES.get(ticker, ticker.replace(".AX", "")),
                "last": last,
                "pct": pct,
                "positive": pct >= 0,
            })

        moves.sort(key=lambda x: x["pct"], reverse=True)
        gainers = moves[:8]
        losers  = list(reversed(moves[-8:]))

        session_date = closes.index[-1].date()
        delta = (today - session_date).days
        session_label = "Friday" if (delta == 3 and datetime.now(ZoneInfo("Australia/Sydney")).strftime("%A") == "Monday") else session_date.strftime("%A")
        lines = [f"=== ASX MARKET MOVERS ({session_label} session — {session_date}) ===\n", "Top Gainers:"]
        for m in gainers:
            lines.append(f"  {m['ticker']} ({m['name']}): ${m['last']:.2f} {m['pct']:+.2f}%")
        lines.append("\nTop Losers:")
        for m in losers:
            lines.append(f"  {m['ticker']} ({m['name']}): ${m['last']:.2f} {m['pct']:+.2f}%")
        lines.append("")

        print(f"  ASX movers: top gainer {gainers[0]['ticker']} {gainers[0]['pct']:+.2f}%, top loser {losers[0]['ticker']} {losers[0]['pct']:+.2f}%")
        return "\n".join(lines), gainers, losers
    except Exception as ex:
        print(f"  WARN ASX movers: {ex}")
        return "", [], []


# ---------------------------------------------------------------------------
# Fetch & deduplicate RSS feeds
# ---------------------------------------------------------------------------
def fetch_entries(feeds: dict) -> dict:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
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
def build_prompt(entries: dict, market_data: str, movers_text: str, day_of_week: str = "") -> str:
    is_monday = day_of_week.lower() == "monday"
    us_session_ref = "on Friday" if is_monday else "overnight"
    monday_note = (
        "NOTE: Today is Monday. Wall Street closed on Friday — do not use the word 'overnight'. "
        "Reference Friday's session directly (e.g. 'Wall Street closed Friday with...', 'Friday's US session delivered...'). "
        "Where relevant, acknowledge that Australian investors are returning from the weekend.\n"
    ) if is_monday else ""

    lines = [
        "You are producing a daily pre-market financial briefing for Australian investors and professionals.",
        "The ASX opens at 10:00am AEST. This brief is sent at 7:30am AEST, before market open.",
        monday_note,
        "Based on the market data and stories below, produce output in EXACTLY this format — no extra text:\n",

        "GLOBAL RULES:",
        "1. Always use specific numbers — index levels, percentages, dollar amounts. Never say 'markets fell' without the figure.",
        "2. If a number is not in the source data, omit it. Do not guess or approximate.",
        "3. Write in an AFR-style markets column voice: measured, commercially literate, concise, and specific.",
        "4. Add a touch of Bloomberg discipline: tight numbers, clear catalysts, no filler, no dramatic language.",
        f"5. Australian perspective — lead with ASX implications of {us_session_ref}'s US moves.",
        "6. For ASX movers >5% with no direct company news: first check the macro and global stories for an indirect catalyst",
        "   (e.g. US inflation data hitting rate-sensitive stocks like banks; CGT/negative gearing policy changes hitting property-linked stocks;",
        "   commodity price moves hitting miners). Attribute the move to the macro catalyst if one plausibly fits.",
        "   Only say 'no news catalyst' if you have genuinely checked macro, global, and commodity stories and found nothing relevant.",
        "7. Avoid contradictory leads. If US markets are positive but the ASX read is negative, name the offsetting drag in the same sentence",
        "   (e.g. weaker commodities, banks, futures, AUD, China, rates, or a major local stock/sector). If no offsetting drag is in the data,",
        "   do not say the ASX is set to slide; describe the read as mixed or selectively supported.\n",

        "OPENING_SIGNAL_START",
        "RISK_TONE: <Risk-on, risk-off, or mixed — max 8 words, include the reason>",
        "ASX_READ: <Likely ASX open/read-through — max 12 words>",
        "KEY_DRIVER: <single dominant driver — max 10 words>",
        "OPENING_SIGNAL_END\n",

        "BRIEFING_START",
        "Write a 120-150 word AFR-style pre-market note for Australian investors.",
        f"Paragraph 1: lead with the ASX read-through from {us_session_ref}'s US move, then the dominant market driver. Include the most important numbers.",
        "If the ASX direction differs from Wall Street's direction, explain the divergence before the sentence ends.",
        "Paragraph 2: explain the sector or stock implications in plain English. Use restrained editorial judgement, not hype.",
        "Separate paragraphs with a blank line. No headings. Avoid 'appears' and 'watch point'.",
        "BRIEFING_END\n",

        "MARKET_TAPE_START",
        "ITEM: <US index/sector move with level and % — direct ASX implication>",
        "ITEM: <ASX 200 previous session close and % — sector implication>",
        "ITEM: <FX/rates/commodity move with price and % — direct ASX implication>",
        "ITEM: <one cross-asset confirmation or divergence, if supported by data>",
        "MARKET_TAPE_END\n",

        "WHY_IT_MATTERS_START",
        "ITEM: <one AFR-style editorial sentence on the tradeable implication for Australian equities>",
        "ITEM: <one sentence on the main macro/commodity/rates transmission channel>",
        "WHY_IT_MATTERS_END\n",

        "WATCHLIST_START",
        "ITEM: <ASX ticker/company> — <specific open catalyst; include % move or price where available>",
        "ITEM: <ASX ticker/company> — <specific open catalyst; include % move or price where available>",
        "ITEM: <ASX ticker/company> — <specific open catalyst; include % move or price where available>",
        "WATCHLIST_END\n",

        "MARKET_IMPACT_START",
        "ITEM: <market-moving news event> — Why it matters: <which ASX sector/stocks are most exposed> — What to watch: <the number, release, price, or level that would change the view>",
        "ITEM: <market-moving news event> — Why it matters: <which ASX sector/stocks are most exposed> — What to watch: <the number, release, price, or level that would change the view>",
        "ITEM: <market-moving news event> — Why it matters: <which ASX sector/stocks are most exposed> — What to watch: <the number, release, price, or level that would change the view>",
        "Only include news with a plausible price impact today or this week. Prioritise catalysts over general background.",
        "MARKET_IMPACT_END\n",

        "ASX_OVERVIEW_START",
        "1-sentence snapshot of the single most important ASX story or theme today. Name specific companies or sectors.",
        "When referencing large movers, connect them to their macro or global catalyst (US inflation, RBA, commodity prices, policy changes) — do not describe them in isolation.",
        "ASX_OVERVIEW_END\n",

        "3 most important ASX stories (earnings, company announcements, sector moves, M&A, broker calls — Australian companies only):",
        "ASX_STORY_START\nTITLE: <title>\nSOURCE: <source>\nURL: <url>\nSUMMARY: <2 sentences — name the company, include specific financial figures or % moves>\nASX_STORY_END\n",

        "MACRO_OVERVIEW_START",
        "1-sentence factual summary of the most important macro/policy development in the last 24 hours. Prioritise Australian data (RBA, ABS) over offshore. Name the specific central bank, data release, or event.",
        "MACRO_OVERVIEW_END\n",

        "2-3 most important macro & policy stories (prioritise: RBA, ABS data, Australian government; then Fed/ECB, global data):",
        "MACRO_STORY_START\nTITLE: <title>\nSOURCE: <source>\nURL: <url>\nSUMMARY: <2 sentences — include the specific number or decision>\nMACRO_STORY_END\n",

        "COMMODITY_OVERVIEW_START",
        "1-sentence snapshot of the most significant commodity move. Prioritise iron ore, coal, and LNG — the commodities that drive Australian export earnings and ASX mining stocks.",
        "Only use gold if it is the clear market leader today. Otherwise keep gold brief or omit it entirely.",
        "COMMODITY_OVERVIEW_END\n",

        "2 most important commodity stories (iron ore, coal, LNG, oil, gold, copper — weight toward Australian export commodities):",
        "Do not let gold crowd out more useful Australian signals. Prefer iron ore, coal, LNG, oil, or copper when they are the real market drivers.",
        "COMMODITY_STORY_START\nTITLE: <title>\nSOURCE: <source>\nURL: <url>\nSUMMARY: <2 sentences — include specific commodity, price direction, and ASX implication>\nCOMMODITY_STORY_END\n",

        "GLOBAL_OVERVIEW_START",
        f"1-sentence summary of the most significant {us_session_ref} development in US or European markets that Australian investors need to know about.",
        "GLOBAL_OVERVIEW_END\n",

        "2 most important global markets stories (Wall Street earnings, sector moves — only include if directly relevant to ASX or Australian portfolio exposure):",
        "GLOBAL_STORY_START\nTITLE: <title>\nSOURCE: <source>\nURL: <url>\nSUMMARY: <2 sentences — include specific company, index, or figure and why it matters for Australian investors>\nGLOBAL_STORY_END\n",

        "THE_NUMBER_START",
        "STAT: <one standout market stat from today — short and punchy, max 4 words. Examples: '-2.3%', '$3,420/oz', '4.34%'. Just the figure.>",
        "CONTEXT: <one sentence explaining what this stat is and why it matters to an Australian investor or business>",
        "Prefer the broadest market signal available: ASX 200, AUD/USD, US 10Y, a major index move, or a sector catalyst. Do not default to gold unless gold is the day's clearest and most tradeable move.",
        "Avoid repeating gold from day to day. If gold is not the dominant cross-asset driver, choose a different stat.",
        "THE_NUMBER_END\n",

        "SUBJECT_LINE_START",
        "Write one email subject line (max 55 characters) for this pre-market brief.",
        "Lead with the most important market move or number. No clickbait. No exclamation marks.",
        "Format: <key stat or hook> | The Markets Brief",
        "SUBJECT_LINE_END\n",

        "=== MARKET DATA ===\n",
    ]

    if market_data:
        lines.append(market_data)
    if movers_text:
        lines.append(movers_text)

    lines.append("=== STORIES ===\n")
    limits = {"asx": 8, "macro": 8, "global_markets": 8, "commodities": 6}
    for cat, items in entries.items():
        lines.append(f"--- {cat.upper()} ---")
        for item in items[:limits.get(cat, 8)]:
            lines.append(f"[{item['source']}] {item['title']}")
            lines.append(f"  {item['url']}")
        lines.append("")

    return "\n".join(lines)


def call_claude(prompt: str) -> str:
    print("  Calling Anthropic API...")
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    model = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6")
    message = client.messages.create(
        model=model,
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


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
            for key in ("TITLE", "SOURCE", "URL", "SUMMARY", "STAT", "CONTEXT", "RISK_TONE", "ASX_READ", "KEY_DRIVER"):
                if line.startswith(f"{key}:"):
                    item[key.lower()] = line[len(key)+1:].strip()
        if item:
            items.append(item)
    return items


def _extract_items(text: str, tag: str) -> list[str]:
    block = _extract(text, tag)
    items = []
    for line in block.splitlines():
        if line.startswith("ITEM:"):
            items.append(line[len("ITEM:"):].strip())
    return items


def parse_response(raw: str) -> dict:
    the_number_blocks = _extract_blocks(raw, "THE_NUMBER")
    the_number = the_number_blocks[0] if the_number_blocks else {}
    opening_signal_blocks = _extract_blocks(raw, "OPENING_SIGNAL")
    opening_signal = opening_signal_blocks[0] if opening_signal_blocks else {}
    return {
        "briefing":           _extract(raw, "BRIEFING"),
        "opening_signal":     opening_signal,
        "market_tape":        _extract_items(raw, "MARKET_TAPE"),
        "why_it_matters":     _extract_items(raw, "WHY_IT_MATTERS"),
        "watchlist":          _extract_items(raw, "WATCHLIST"),
        "market_impact":      _extract_items(raw, "MARKET_IMPACT"),
        "macro_overview":     _extract(raw, "MACRO_OVERVIEW"),
        "macro_stories":      _extract_blocks(raw, "MACRO_STORY"),
        "asx_overview":       _extract(raw, "ASX_OVERVIEW"),
        "asx_stories":        _extract_blocks(raw, "ASX_STORY"),
        "global_overview":    _extract(raw, "GLOBAL_OVERVIEW"),
        "global_stories":     _extract_blocks(raw, "GLOBAL_STORY"),
        "commodity_overview": _extract(raw, "COMMODITY_OVERVIEW"),
        "commodity_stories":  _extract_blocks(raw, "COMMODITY_STORY"),
        "the_number_stat":    the_number.get("stat", ""),
        "the_number_context": the_number.get("context", ""),
        "subject_line":       _extract(raw, "SUBJECT_LINE"),
    }


# ---------------------------------------------------------------------------
# HTML rendering
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


def _opening_briefing_html(d: dict) -> str:
    signal = d.get("opening_signal") or {}
    briefing = d.get("briefing", "").strip()
    tape = d.get("market_tape") or []
    why = d.get("why_it_matters") or []
    watchlist = d.get("watchlist") or []

    if not any([signal, tape, why, watchlist]):
        para_style = 'margin:0 0 16px;font-size:16px;color:#222;line-height:1.75;font-family:Georgia,serif;'
        parts = []
        for para in re.split(r'\n{2,}', briefing):
            para = para.strip()
            if para:
                parts.append(f'<p style="{para_style}">{_e(para)}</p>')
        return "".join(parts)

    def _signal_cell(label: str, value: str) -> str:
        return f"""
        <td width="33.33%" style="padding:12px 10px;border-right:1px solid #e6e1d8;vertical-align:top;">
          <p style="margin:0 0 5px;font-size:9px;color:#8b8276;letter-spacing:.12em;text-transform:uppercase;font-family:Arial,sans-serif;">{label}</p>
          <p style="margin:0;font-size:13px;color:#111;font-weight:700;line-height:1.35;font-family:Arial,sans-serif;">{_e(value)}</p>
        </td>"""

    def _items_html(items: list[str], color: str = "#111") -> str:
        return "".join(
            f'<tr><td style="padding:8px 0;border-bottom:1px solid #eee;font-size:14px;color:{color};line-height:1.45;font-family:Arial,sans-serif;">{_e(item)}</td></tr>'
            for item in items
        )

    watch_rows = "".join(
        f'<tr><td style="padding:9px 0;border-bottom:1px solid #eee;font-size:14px;color:#111;line-height:1.45;font-family:Arial,sans-serif;">{_e(item)}</td></tr>'
        for item in watchlist
    )

    briefing_parts = []
    for para in re.split(r'\n{2,}', briefing):
        para = para.strip()
        if para:
            briefing_parts.append(f'<p style="margin:0 0 15px;font-size:17px;color:#222;line-height:1.65;font-family:Georgia,serif;">{_e(para)}</p>')
    briefing_html = "".join(briefing_parts)

    return f"""
    <table width="100%" cellpadding="0" cellspacing="0" style="background:#f7f4ee;border-top:3px solid #111;border-bottom:1px solid #e6e1d8;margin-bottom:22px;">
      <tr>
        {_signal_cell("Market Bias", signal.get("risk_tone", ""))}
        {_signal_cell("ASX Read", signal.get("asx_read", ""))}
        {_signal_cell("Main Driver", signal.get("key_driver", ""))}
      </tr>
    </table>
    {briefing_html}
    <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:24px;">
      <tr>
        <td width="50%" style="vertical-align:top;padding-right:18px;">
          <p style="margin:0 0 8px;font-size:10px;color:#888;letter-spacing:.12em;text-transform:uppercase;font-family:Arial,sans-serif;font-weight:700;">Market Tape</p>
          <table width="100%" cellpadding="0" cellspacing="0">{_items_html(tape)}</table>
        </td>
        <td width="50%" style="vertical-align:top;padding-left:18px;">
          <p style="margin:0 0 8px;font-size:10px;color:#888;letter-spacing:.12em;text-transform:uppercase;font-family:Arial,sans-serif;font-weight:700;">The Read</p>
          <table width="100%" cellpadding="0" cellspacing="0">{_items_html(why)}</table>
        </td>
      </tr>
    </table>
    <p style="margin:0 0 8px;font-size:10px;color:#888;letter-spacing:.12em;text-transform:uppercase;font-family:Arial,sans-serif;font-weight:700;">Stocks In Play</p>
    <table width="100%" cellpadding="0" cellspacing="0">{watch_rows}</table>"""


def _market_snapshot_html(market_data: list[dict]) -> str:
    if not market_data:
        return ""

    def _row(item: dict) -> str:
        color = "#1a7a3a" if item["positive"] else "#c0392b"
        arrow = "▲" if item["positive"] else "▼"
        return f"""
      <tr>
        <td style="padding:9px 0;font-size:13px;color:#555;font-family:Arial,sans-serif;border-bottom:1px solid #f0f0f0;">{_e(item['name'])}</td>
        <td style="padding:9px 0;font-size:14px;font-weight:700;color:#111;font-family:Arial,sans-serif;text-align:right;border-bottom:1px solid #f0f0f0;">{_e(item['value'])}</td>
        <td style="padding:9px 8px;font-size:13px;font-weight:600;color:{color};font-family:Arial,sans-serif;text-align:right;border-bottom:1px solid #f0f0f0;white-space:nowrap;">{arrow}&nbsp;{_e(item['pct'])}</td>
      </tr>"""

    groups_order = ["Indices", "FX", "Rates", "Commodities", "Crypto"]
    grouped: dict[str, list] = {}
    for item in market_data:
        grouped.setdefault(item["group"], []).append(item)

    all_groups = [g for g in groups_order if g in grouped]
    mid = (len(all_groups) + 1) // 2
    left_groups  = all_groups[:mid]
    right_groups = all_groups[mid:]

    def _col_html(group_names: list[str]) -> str:
        parts = []
        for gname in group_names:
            items = grouped.get(gname, [])
            if not items:
                continue
            rows = "".join(_row(i) for i in items)
            parts.append(f"""
<p style="margin:0 0 4px;font-size:10px;color:#aaa;letter-spacing:.12em;text-transform:uppercase;font-family:Arial,sans-serif;">{_e(gname)}</p>
<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:20px;border-collapse:collapse;">
  <tbody>{rows}
  </tbody>
</table>""")
        return "".join(parts)

    return f"""
  <tr><td style="padding:0 48px 32px;">
    <p style="margin:0 0 20px;font-size:11px;color:#888;letter-spacing:.12em;text-transform:uppercase;font-family:Arial,sans-serif;">Markets at a Glance</p>
    <table width="100%" cellpadding="0" cellspacing="16">
      <tr>
        <td width="48%" style="vertical-align:top;padding-right:16px;">{_col_html(left_groups)}</td>
        <td width="4%"></td>
        <td width="48%" style="vertical-align:top;">{_col_html(right_groups)}</td>
      </tr>
    </table>
  </td></tr>
  <tr><td style="padding:0 48px;"><hr style="border:none;border-top:1px solid #ddd;margin:0 0 32px;"></td></tr>"""


def _movers_html(gainers: list[dict], losers: list[dict]) -> str:
    if not gainers and not losers:
        return ""

    def _mover_row(m: dict) -> str:
        color = "#1a7a3a" if m["positive"] else "#c0392b"
        arrow = "▲" if m["positive"] else "▼"
        return f"""
      <tr>
        <td style="padding:8px 0;border-bottom:1px solid #f0f0f0;">
          <p style="margin:0;font-size:13px;font-weight:700;color:#111;font-family:Arial,sans-serif;">{_e(m['ticker'])}</p>
          <p style="margin:1px 0 0;font-size:11px;color:#888;font-family:Arial,sans-serif;">{_e(m['name'])}</p>
        </td>
        <td style="padding:8px 0;font-size:13px;color:#555;font-family:Arial,sans-serif;text-align:right;border-bottom:1px solid #f0f0f0;">${m['last']:.2f}</td>
        <td style="padding:8px 8px;font-size:13px;font-weight:700;color:{color};font-family:Arial,sans-serif;text-align:right;border-bottom:1px solid #f0f0f0;white-space:nowrap;">{arrow}&nbsp;{m['pct']:+.2f}%</td>
      </tr>"""

    gainers_rows = "".join(_mover_row(m) for m in gainers)
    losers_rows  = "".join(_mover_row(m) for m in losers)

    return f"""
  <tr><td style="padding:0 48px 32px;">
    <p style="margin:0 0 20px;font-size:11px;color:#888;letter-spacing:.12em;text-transform:uppercase;font-family:Arial,sans-serif;">ASX Market Movers · Previous Session</p>
    <table width="100%" cellpadding="0" cellspacing="16">
      <tr>
        <td width="48%" style="vertical-align:top;padding-right:16px;">
          <p style="margin:0 0 4px;font-size:10px;color:#1a7a3a;letter-spacing:.12em;text-transform:uppercase;font-family:Arial,sans-serif;font-weight:700;">▲ Top Gainers</p>
          <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
            <tbody>{gainers_rows}</tbody>
          </table>
        </td>
        <td width="4%"></td>
        <td width="48%" style="vertical-align:top;">
          <p style="margin:0 0 4px;font-size:10px;color:#c0392b;letter-spacing:.12em;text-transform:uppercase;font-family:Arial,sans-serif;font-weight:700;">▼ Top Losers</p>
          <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
            <tbody>{losers_rows}</tbody>
          </table>
        </td>
      </tr>
    </table>
  </td></tr>
  <tr><td style="padding:0 48px;"><hr style="border:none;border-top:1px solid #ddd;margin:0 0 32px;"></td></tr>"""


def _section(label: str, overview: str, stories: list) -> str:
    stories_html = "".join(_story_card(s) for s in stories)
    return f"""
  <tr><td style="padding:0 48px 32px;">
    <p style="margin:0 0 20px;font-size:11px;color:#888;letter-spacing:.12em;text-transform:uppercase;font-family:Arial,sans-serif;">{_e(label)}</p>
    <h2 style="margin:0 0 10px;font-size:14px;font-weight:700;color:#111;text-transform:uppercase;letter-spacing:.08em;font-family:Arial,sans-serif;border-left:3px solid #111;padding-left:10px;">Overview</h2>
    <p style="margin:0 0 24px;font-size:16px;color:#222;line-height:1.75;font-family:Georgia,serif;">{_e(overview)}</p>
    {stories_html}
  </td></tr>
  <tr><td style="padding:0 48px;"><hr style="border:none;border-top:1px solid #ddd;margin:0 0 32px;"></td></tr>"""


def _market_impact_html(items: list[str]) -> str:
    if not items:
        return ""

    rows = "".join(
        f"""
      <tr><td style="padding:14px 0;border-bottom:1px solid #e8e8e8;">
        <p style="margin:0;font-size:15px;color:#111;line-height:1.55;font-family:Arial,sans-serif;">{_e(item)}</p>
      </td></tr>"""
        for item in items
    )

    return f"""
  <tr><td style="padding:0 48px 32px;">
    <p style="margin:0 0 20px;font-size:11px;color:#888;letter-spacing:.12em;text-transform:uppercase;font-family:Arial,sans-serif;">What Moves Markets</p>
    <table width="100%" cellpadding="0" cellspacing="0" style="border-top:3px solid #111;border-collapse:collapse;background:#fbfaf7;">
      {rows}
    </table>
  </td></tr>
  <tr><td style="padding:0 48px;"><hr style="border:none;border-top:1px solid #ddd;margin:0 0 32px;"></td></tr>"""


def render_html(d: dict, date_str: str, market_data: list[dict], gainers: list[dict], losers: list[dict]) -> str:
    briefing_html = _opening_briefing_html(d)
    snapshot_html = _market_snapshot_html(market_data)
    movers_html   = _movers_html(gainers, losers)
    impact_html   = _market_impact_html(d.get("market_impact") or [])

    sections_html = (
        _section("ASX Focus", d["asx_overview"], d["asx_stories"][:3]) +
        _section("Macro & Policy", d["macro_overview"], d["macro_stories"][:3]) +
        _section("Commodities", d["commodity_overview"], d["commodity_stories"][:2]) +
        _section("Global Markets", d["global_overview"], d["global_stories"][:2])
    )

    the_number_html = ""
    if d.get("the_number_stat"):
        the_number_html = f"""
  <tr><td style="padding:0 48px 32px;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background:#111;">
      <tr><td style="padding:28px 32px;" align="left">
        <p style="margin:0 0 4px;font-size:11px;color:#888;letter-spacing:.15em;text-transform:uppercase;font-family:Arial,sans-serif;">The Number</p>
        <p style="margin:0 0 8px;font-size:42px;font-weight:700;color:#fff;font-family:Georgia,serif;line-height:1.1;">{_e(d['the_number_stat'])}</p>
        <p style="margin:0;font-size:14px;color:#ccc;line-height:1.6;font-family:Arial,sans-serif;">{_e(d['the_number_context'])}</p>
      </td></tr>
    </table>
  </td></tr>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>The Markets Brief – {date_str}</title></head>
<body style="margin:0;padding:0;background:#f5f4f0;font-family:Georgia,serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f4f0;padding:40px 16px;">
<tr><td align="center">
<table width="620" cellpadding="0" cellspacing="0" style="max-width:620px;width:100%;background:#fff;">

  <!-- Header -->
  <tr><td style="padding:40px 48px 24px;border-bottom:3px solid #111;">
    <p style="margin:0 0 6px;font-size:11px;color:#888;letter-spacing:.15em;text-transform:uppercase;font-family:Arial,sans-serif;">{date_str}</p>
    <h1 style="margin:0;font-size:40px;font-weight:700;color:#111;font-family:Georgia,serif;letter-spacing:-1px;line-height:1;">The Markets Brief</h1>
    <p style="margin:4px 0 0;font-size:11px;color:#888;letter-spacing:.12em;text-transform:uppercase;font-family:Arial,sans-serif;">ASX Pre-Market · 7:30am AEST</p>
  </td></tr>

  <!-- Briefing -->
  <tr><td style="padding:32px 48px 24px;">
    <p style="margin:0 0 20px;font-size:11px;color:#888;letter-spacing:.12em;text-transform:uppercase;font-family:Arial,sans-serif;">Opening Note</p>
    {briefing_html}
  </td></tr>

  <tr><td style="padding:0 48px;"><hr style="border:none;border-top:1px solid #ddd;margin:0 0 32px;"></td></tr>

  {snapshot_html}

  {movers_html}

  {impact_html}

  {sections_html}

  {the_number_html}

  <!-- Footer -->
  <tr><td style="padding:24px 48px;border-top:2px solid #111;">
    <table width="100%" cellpadding="0" cellspacing="0">
      <tr>
        <td><p style="margin:0;font-size:12px;color:#888;font-family:Arial,sans-serif;">Your daily pre-market briefing</p></td>
        <td align="right">
          <a href="mailto:hello@themarketsbrief.com?subject=Subscribe%20to%20The%20Markets%20Brief" style="font-size:11px;color:#111;font-family:Arial,sans-serif;text-decoration:none;border-bottom:1px solid #111;padding-bottom:1px;margin-right:16px;">Subscribe</a>
          <a href="mailto:hello@themarketsbrief.com?subject=Unsubscribe%20from%20The%20Markets%20Brief" style="font-size:11px;color:#888;font-family:Arial,sans-serif;text-decoration:none;border-bottom:1px solid #ccc;padding-bottom:1px;">Unsubscribe</a>
        </td>
      </tr>
    </table>
  </td></tr>

</table></td></tr></table>
</body></html>"""


# ---------------------------------------------------------------------------
# Social card — markets stat image (1080x1080, Instagram/LinkedIn ready)
# ---------------------------------------------------------------------------
def generate_markets_card(stat: str, context: str) -> str | None:
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

    # Label
    draw.text((W // 2, 190), "THE NUMBER", font=label_font, fill="#888888", anchor="mm")
    draw.line([(W // 2 - 60, 226), (W // 2 + 60, 226)], fill="#333333", width=1)

    # Stat
    stat_line_h = stat_size + 12
    stat_block_h = len(stat_lines) * stat_line_h
    stat_y = H // 2 - stat_block_h // 2
    for line in stat_lines:
        draw.text((W // 2, stat_y), line, font=stat_font, fill="#ffffff", anchor="mm")
        stat_y += stat_line_h

    # Context
    context_lines = wrap_text(context, context_font, W - 140)
    y = H // 2 + stat_block_h // 2 + 36
    for line in context_lines:
        draw.text((W // 2, y), line, font=context_font, fill="#cccccc", anchor="mm")
        y += 52

    # Branding
    draw.text((W // 2, H - 100), "The Markets Brief", font=brand_font, fill="#555555", anchor="mm")

    images_dir = os.path.join(os.path.dirname(__file__), "social_images")
    os.makedirs(images_dir, exist_ok=True)
    slug = datetime.now(ZoneInfo("Australia/Sydney")).strftime("%Y-%m-%d")
    path = os.path.join(images_dir, f"{slug}_markets_card.png")
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
    result = sb.table("markets_subscribers").select("email,token").eq("active", True).execute()
    print(f"  {len(result.data)} active subscriber(s)")
    return result.data


def log_send(subject: str, recipient_count: int, resend_id: str) -> None:
    try:
        sb = get_supabase()
        sb.table("markets_send_log").insert({
            "subject": subject,
            "recipient_count": recipient_count,
            "resend_id": resend_id,
        }).execute()
    except Exception as ex:
        print(f"  WARN: could not log send: {ex}")


def save_edition(slug: str, subject: str, preview_text: str, html_body: str) -> None:
    try:
        sb = get_supabase()
        sb.table("markets_editions").upsert({
            "slug": slug,
            "subject": subject,
            "preview_text": preview_text,
            "html": html_body,
        }, on_conflict="slug").execute()
        print(f"  Edition saved: {slug}")
    except Exception as ex:
        print(f"  WARN: could not save edition: {ex}")


# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------
def send_email(to: list[str], subject: str, html_body: str) -> str:
    resend.api_key = os.environ["RESEND_API_KEY"]
    params: resend.Emails.SendParams = {
        "from": os.environ.get("MARKETS_FROM_EMAIL", "brief@theoperatingbrief.com"),
        "to": to,
        "reply_to": os.environ.get("MARKETS_REPLY_TO_EMAIL", "hello@theoperatingbrief.com"),
        "subject": subject,
        "html": html_body,
    }
    resp = resend.Emails.send(params)
    resend_id = resp.get("id", str(resp))
    print(f"    → {to[0]} ({resend_id})")
    return resend_id


def _sent_log_path() -> str:
    slug = datetime.now(ZoneInfo("Australia/Sydney")).strftime("%Y-%m-%d")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), f".sent_markets_{slug}.json")


def _load_sent_log() -> dict:
    path = _sent_log_path()
    if os.path.exists(path):
        with open(path) as f:
            import json as _json
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
    skipped = list(sent_log.keys())
    if skipped:
        print(f"  Skipping {len(skipped)} already sent: {', '.join(skipped)}")

    pending = [s for s in subscribers if s["email"] not in sent_log]
    for i, sub in enumerate(pending):
        if i > 0:
            time.sleep(0.6)
        token = sub.get("token", "")
        email = sub["email"]
        unsub_url = f"https://theoperatingbrief.com/markets/unsubscribe?token={token}"
        sub_url = "https://theoperatingbrief.com/markets"
        personalised = base_html.replace(
            'href="mailto:hello@themarketsbrief.com?subject=Subscribe%20to%20The%20Markets%20Brief"',
            f'href="{sub_url}"'
        ).replace(
            'href="mailto:hello@themarketsbrief.com?subject=Unsubscribe%20from%20The%20Markets%20Brief"',
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
# Main
# ---------------------------------------------------------------------------
def main():
    import argparse, webbrowser
    parser = argparse.ArgumentParser(description="The Markets Brief — daily ASX pre-market digest")
    parser.add_argument("--preview", action="store_true", help="Generate HTML and open in browser without sending.")
    parser.add_argument("--send", action="store_true", help="Send the last generated preview to all subscribers without regenerating.")
    args = parser.parse_args()

    aest = ZoneInfo("Australia/Sydney")
    now_aest = datetime.now(aest)
    date_str = now_aest.strftime("%B %d, %Y")
    subject_default = f"The Markets Brief – {date_str}"
    preview_path = os.path.join(os.path.dirname(__file__), "preview_markets.html")
    subject_path = os.path.join(os.path.dirname(__file__), "preview_markets_subject.txt")

    # --send: read saved preview and send it exactly as reviewed
    if args.send:
        if not os.path.exists(preview_path):
            print("No preview found. Run --preview first.")
            return
        with open(preview_path) as f:
            html_body = f.read()
        subject = subject_default
        if os.path.exists(subject_path):
            with open(subject_path) as f:
                subject = f.read().strip() or subject
        print(f"  Subject: {subject}")
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

    print("Fetching market data…")
    market_data_text, market_data_structured = fetch_market_data()
    print(f"  {len(market_data_structured)} instruments loaded")

    print("Fetching ASX market movers…")
    movers_text, gainers, losers = fetch_asx_movers()

    print("Fetching RSS feeds…")
    entries = fetch_entries(FEEDS)
    total = sum(len(v) for v in entries.values())
    print(f"  {total} stories total after deduplication")

    if total == 0 and not market_data_structured:
        print("No data found. Exiting.")
        return

    print("Summarising with Claude…")
    day_of_week = now_aest.strftime("%A")
    prompt = build_prompt(entries, market_data_text, movers_text, day_of_week=day_of_week)
    print(f"  Prompt length: {len(prompt):,} chars (~{len(prompt)//4:,} tokens)")
    raw = call_claude(prompt)

    with open("debug_markets_response.txt", "w") as f:
        f.write(raw)

    print("Parsing response…")
    digest = parse_response(raw)
    subject = digest.get("subject_line") or subject_default
    print(f"  Subject: {subject}")
    print(f"  briefing: {len(digest['briefing'])} chars")

    print("Rendering HTML…")
    html_body = render_html(digest, date_str, market_data_structured, gainers, losers)

    # Save the number so daily_digest can combine both in the social caption
    import json as _json
    markets_number_path = os.path.join(os.path.dirname(__file__), "markets_number.json")
    with open(markets_number_path, "w") as f:
        _json.dump({
            "date": now_aest.date().isoformat(),
            "stat": digest.get("the_number_stat", ""),
            "context": digest.get("the_number_context", ""),
        }, f)
    print(f"  Markets number saved → {markets_number_path}")

    # Always save preview file so --send uses exactly what was reviewed
    with open(preview_path, "w") as f:
        f.write(html_body)
    with open(subject_path, "w") as f:
        f.write(subject)

    if args.preview:
        preview_text = digest.get("briefing", "")[:120]
        save_edition("draft", subject, preview_text, html_body)

        print(f"Preview saved → {preview_path}")
        webbrowser.open(f"file://{preview_path}")
        # Generate social card and pop it open
        card_path = generate_markets_card(
            digest.get("the_number_stat", ""),
            digest.get("the_number_context", ""),
        )
        if card_path:
            import subprocess as _sp
            _sp.run(["open", card_path])
        print(f"  Web preview: https://theoperatingbrief.com/preview/{os.environ.get('PREVIEW_TOKEN', '<PREVIEW_TOKEN>')}")
        if not sys.stdin.isatty():
            print("Running unattended — draft saved. Approve and send from the web preview.")
            return
        webbrowser.open(f"file://{preview_path}")
        print("\nReview the email, then type y to send.\n")
        answer = input("Send to subscribers now? (y/n): ").strip().lower()
        if answer != "y":
            print("Not sent. Run --send when ready.")
            return
        args.send = True

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
