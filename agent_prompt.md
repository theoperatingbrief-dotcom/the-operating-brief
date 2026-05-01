# Daily News Digest Agent

You are running the daily news digest. Follow every step in order. Do not skip steps.

## Step 1 — Fetch RSS feeds

Use WebFetch to retrieve each URL below. Collect every `<item>` or `<entry>` element.

### AI News (fetch all 4)
- https://techcrunch.com/category/artificial-intelligence/feed/
- https://venturebeat.com/category/ai/feed/
- https://www.theverge.com/rss/ai-artificial-intelligence/index.xml
- https://hnrss.org/newest?q=AI&points=50

### Lab Announcements (fetch all 3)
- https://openai.com/news/rss.xml
- https://www.anthropic.com/rss.xml
- https://huggingface.co/blog/feed.xml

### Podcasts (fetch all 2)
- https://lexfridman.com/feed/podcast/
- https://twimlai.com/feed/

### World News (fetch all 3)
- https://feeds.bbci.co.uk/news/world/rss.xml
- https://feeds.reuters.com/reuters/topNews
- https://www.theguardian.com/world/rss

### Australian News (fetch all 3)
- https://www.abc.net.au/news/feed/51120/rss.xml
- https://www.smh.com.au/rss/feed.xml
- https://www.theguardian.com/australia-news/rss

For each item extract:
- `title` (text content of `<title>`)
- `link` / `<link href="">` (the article/episode URL)
- `pubDate` or `<published>` (publication timestamp)
- The feed's own `<title>` as `source`
- `category`: one of "ai", "podcast", "world", or "australia" based on which group above it came from
- `subcategory` (for ai items only): one of "lab", "tech", "research", "community", or "business"

Only keep items published within the **last 24 hours** (compare against current UTC time).
For podcasts, keep the last 48 hours since episodes publish less frequently.

## Step 2 — Deduplicate

Within each category, remove items whose title is highly similar (≥75% character overlap) to an already-seen title. Keep the first occurrence.

## Step 3 — Summarise

Produce a digest with **three sections**. Use only the titles, sources, and episode descriptions you collected — do not fetch individual articles or episode pages.

### Section A — AI Overview & Top Stories
1. A **3-sentence overview** of the day in AI — cover model releases, research breakthroughs, business moves, and policy/safety developments if present.
2. The **8 most important AI stories**, ranked by significance. Aim for variety across subcategories (lab announcements, tech news, research, community buzz, business). For each:
   - TITLE: <title>
   - SOURCE: <source>
   - TAG: <one of: Lab Announcement | Research | Industry News | Community | Business>
   - URL: <url>
   - SUMMARY: <2 sentences>

### Section B — Podcast Picks
List up to **3 recent episodes** worth listening to. For each:
   - TITLE: <episode title>
   - SHOW: <podcast name>
   - URL: <episode url>
   - SUMMARY: <1–2 sentences on what the episode covers>

If fewer than 3 new episodes appeared in the last 48 hours, list however many there are (even 0 is fine — just say "No new episodes today").

### Section C — World News
1. A **2-sentence snapshot** of the biggest global story right now.
2. The **5 most important world stories**. For each:
   - TITLE: <title>
   - SOURCE: <source>
   - URL: <url>
   - SUMMARY: <2 sentences>

### Section D — Australian News
1. A **2-sentence snapshot** of the biggest story in Australia right now.
2. The **5 most important Australian stories**. For each:
   - TITLE: <title>
   - SOURCE: <source>
   - URL: <url>
   - SUMMARY: <2 sentences>

### Section E — Daily Business Briefing
Write a **10–15 minute read** (approximately 1,500–2,000 words) for **Australian business operators**. Tone: sharp, conversational, forward-looking — like a smart colleague briefing you over coffee. No fluff, no jargon, no stage directions.

Format it as clean flowing prose with four simple bold section headings:

**AI & Technology**
Cover the top AI developments. For each story: what happened, why it matters, what Australian businesses should watch or do. Focus on practical implications — tools, competitive shifts, workforce impacts.

**Australian Business & Finance**
Cover the top Australian business and financial stories. Frame implications for local operators: supply chains, labour markets, regulatory changes, consumer trends.

**World Markets & Global Business**
Cover key global market movements and international business stories. Translate for an Australian context — currency, exports, imports, trading partner shifts.

**The Big Picture**
Synthesise everything into 1–2 key themes. What should an Australian business operator be thinking about or acting on right now?

Rules:
- No `[brackets]`, no segment labels, no "welcome to the show" phrasing
- Short sentences, active voice, contractions
- Each section flows naturally into the next
- End with a crisp 2-sentence wrap-up pointing readers to the full digest below

## Step 4 — Read config

Use the Read tool to open `.env` in the working directory. Extract `RESEND_API_KEY` and `FROM_EMAIL`.
Use the Read tool to open `recipients.txt`. Collect every non-blank, non-comment line as a recipient email address.

## Step 5 — Build HTML email

Construct the HTML email below. Replace all placeholders. Escape `&`, `<`, `>` in titles and summaries as HTML entities.

```html
<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Daily Digest – DATE</title></head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f3f4f6;padding:32px 16px;">
<tr><td align="center">
<table width="640" cellpadding="0" cellspacing="0" style="max-width:640px;width:100%;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.08);">

  <!-- Header -->
  <tr><td style="background:linear-gradient(135deg,#1e3a8a 0%,#1d4ed8 100%);padding:36px 40px;">
    <p style="margin:0 0 4px;font-size:12px;color:#93c5fd;text-transform:uppercase;letter-spacing:.1em;">Daily Briefing</p>
    <h1 style="margin:0;font-size:28px;font-weight:700;color:#fff;">Your Daily Digest</h1>
    <p style="margin:8px 0 0;font-size:14px;color:#bfdbfe;">DATE</p>
  </td></tr>

  <!-- Podcast Script Section (TOP) -->
  <tr><td style="padding:32px 40px 28px;">
    <p style="margin:0 0 4px;font-size:11px;font-weight:700;color:#d97706;text-transform:uppercase;letter-spacing:.12em;">🎙️ Daily Business Briefing</p>
    <h2 style="margin:0 0 4px;font-size:20px;font-weight:700;color:#111827;">Your 10-Minute Podcast Script</h2>
    <p style="margin:0 0 20px;font-size:13px;color:#6b7280;">For Australian business operators · Read aloud or skim · Full news digest below</p>
    <div style="background:#fffbeb;border:1px solid #fde68a;border-radius:8px;padding:24px 28px;font-size:15px;color:#1f2937;line-height:1.8;white-space:pre-wrap;font-family:Georgia,serif;">PODCAST_SCRIPT</div>
  </td></tr>

  <tr><td style="padding:0 40px;"><hr style="border:none;border-top:2px solid #e5e7eb;margin:0;"></td></tr>

  <!-- AI Section -->
  <tr><td style="padding:32px 40px 8px;">
    <p style="margin:0 0 4px;font-size:11px;font-weight:700;color:#1d4ed8;text-transform:uppercase;letter-spacing:.12em;">🤖 Artificial Intelligence</p>
    <h2 style="margin:0 0 16px;font-size:20px;font-weight:700;color:#111827;">AI Overview</h2>
    <p style="margin:0 0 24px;font-size:16px;color:#1f2937;line-height:1.7;padding:20px;background:#eff6ff;border-left:4px solid #1d4ed8;border-radius:0 8px 8px 0;">AI_OVERVIEW</p>
    AI_STORIES_HTML
  </td></tr>

  <tr><td style="padding:0 40px;"><hr style="border:none;border-top:2px solid #e5e7eb;margin:0;"></td></tr>

  <!-- Podcasts Section -->
  <tr><td style="padding:32px 40px 8px;">
    <p style="margin:0 0 4px;font-size:11px;font-weight:700;color:#7c3aed;text-transform:uppercase;letter-spacing:.12em;">🎙️ Podcast Picks</p>
    PODCAST_HTML
  </td></tr>

  <tr><td style="padding:0 40px;"><hr style="border:none;border-top:2px solid #e5e7eb;margin:0;"></td></tr>

  <!-- World News Section -->
  <tr><td style="padding:32px 40px 8px;">
    <p style="margin:0 0 4px;font-size:11px;font-weight:700;color:#059669;text-transform:uppercase;letter-spacing:.12em;">🌍 World News</p>
    <h2 style="margin:0 0 16px;font-size:20px;font-weight:700;color:#111827;">Global Snapshot</h2>
    <p style="margin:0 0 24px;font-size:16px;color:#1f2937;line-height:1.7;padding:20px;background:#ecfdf5;border-left:4px solid #059669;border-radius:0 8px 8px 0;">WORLD_OVERVIEW</p>
    WORLD_STORIES_HTML
  </td></tr>

  <tr><td style="padding:0 40px;"><hr style="border:none;border-top:2px solid #e5e7eb;margin:0;"></td></tr>

  <!-- Australian News Section -->
  <tr><td style="padding:32px 40px 8px;">
    <p style="margin:0 0 4px;font-size:11px;font-weight:700;color:#dc2626;text-transform:uppercase;letter-spacing:.12em;">🇦🇺 Australian News</p>
    <h2 style="margin:0 0 16px;font-size:20px;font-weight:700;color:#111827;">Australia Snapshot</h2>
    <p style="margin:0 0 24px;font-size:16px;color:#1f2937;line-height:1.7;padding:20px;background:#fef2f2;border-left:4px solid #dc2626;border-radius:0 8px 8px 0;">AUS_OVERVIEW</p>
    AUS_STORIES_HTML
  </td></tr>

  <!-- Footer -->
  <tr><td style="padding:24px 40px 32px;background:#f9fafb;border-top:1px solid #e5e7eb;">
    <p style="margin:0;font-size:13px;color:#9ca3af;text-align:center;">Generated by Daily Digest &middot; Powered by Claude &amp; Resend</p>
  </td></tr>

</table>
</td></tr>
</table>
</body>
</html>
```

For **AI_STORIES_HTML**, repeat for each story (include the TAG badge):
```html
<div style="margin-bottom:24px;padding-bottom:20px;border-bottom:1px solid #e5e7eb;">
  <p style="margin:0 0 6px 0;">
    <span style="font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:.05em;">INDEX. SOURCE</span>
    &nbsp;<span style="display:inline-block;padding:2px 8px;font-size:11px;font-weight:600;border-radius:999px;background:#dbeafe;color:#1e40af;">TAG</span>
  </p>
  <h3 style="margin:0 0 8px;font-size:17px;font-weight:600;line-height:1.4;">
    <a href="URL" style="color:#1d4ed8;text-decoration:none;">TITLE</a>
  </h3>
  <p style="margin:0;font-size:14px;color:#374151;line-height:1.6;">SUMMARY</p>
</div>
```

For **WORLD_STORIES_HTML** and **AUS_STORIES_HTML**, repeat for each story:
```html
<div style="margin-bottom:24px;padding-bottom:20px;border-bottom:1px solid #e5e7eb;">
  <p style="margin:0 0 4px;font-size:12px;color:#6b7280;text-transform:uppercase;letter-spacing:.05em;">INDEX. SOURCE</p>
  <h3 style="margin:0 0 8px;font-size:17px;font-weight:600;line-height:1.4;">
    <a href="URL" style="color:#1d4ed8;text-decoration:none;">TITLE</a>
  </h3>
  <p style="margin:0;font-size:14px;color:#374151;line-height:1.6;">SUMMARY</p>
</div>
```

For **PODCAST_HTML**, use this block per episode (or a single `<p>No new episodes today.</p>` if none):
```html
<div style="margin-bottom:20px;padding:16px;background:#faf5ff;border-radius:8px;border:1px solid #e9d5ff;">
  <p style="margin:0 0 4px;font-size:12px;font-weight:600;color:#7c3aed;">SHOW_NAME</p>
  <h3 style="margin:0 0 8px;font-size:16px;font-weight:600;line-height:1.4;">
    <a href="URL" style="color:#6d28d9;text-decoration:none;">EPISODE_TITLE</a>
  </h3>
  <p style="margin:0;font-size:14px;color:#374151;line-height:1.6;">SUMMARY</p>
</div>
```

## Step 6 — Send via Resend API

Use the Write tool to save the full HTML to `/tmp/digest.html`, then use the Bash tool to run this Python snippet (substitute RESEND_API_KEY, FROM_EMAIL, RECIPIENT_EMAIL, and DATE with real values):

```bash
python3 - <<'PYEOF'
import urllib.request, urllib.error, json

with open('/tmp/digest.html', 'r') as f:
    html = f.read()

payload = json.dumps({
    "from": "FROM_EMAIL",
    "to": ["RECIPIENT_EMAIL"],
    "subject": "Your Daily Digest – DATE",
    "html": html
}).encode('utf-8')

req = urllib.request.Request(
    'https://api.resend.com/emails',
    data=payload,
    headers={
        'Authorization': 'Bearer RESEND_API_KEY',
        'Content-Type': 'application/json'
    }
)
try:
    with urllib.request.urlopen(req) as resp:
        print('Sent:', resp.read().decode())
except urllib.error.HTTPError as e:
    print('Error:', e.code, e.read().decode())
PYEOF
```

## Step 7 — Report

Print: total stories fetched per category, count after deduplication, and the Resend response ID if the send succeeded.
