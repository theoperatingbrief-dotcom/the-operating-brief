#!/usr/bin/env python3
"""Backfill 4 past editions into Supabase editions table."""
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = "https://gekmmwromtzstqpadafd.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)


EDITION_1_HTML = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>The Operating Brief – April 14, 2026</title></head>
<body style="margin:0;padding:0;background:#f5f4f0;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f4f0;padding:32px 16px;">
<tr><td align="center">
<table width="620" cellpadding="0" cellspacing="0" style="max-width:620px;width:100%;background:#ffffff;">

  <tr><td style="padding:32px 40px 0;background:#ffffff;">
    <p style="margin:0 0 8px;font-size:11px;font-family:Arial,sans-serif;font-weight:700;color:#888888;text-transform:uppercase;letter-spacing:.12em;">Monday, April 14 2026</p>
    <h1 style="margin:0;font-size:40px;font-weight:700;color:#111111;font-family:Georgia,serif;line-height:1.1;">The Operating Brief</h1>
    <p style="margin:6px 0 20px;font-size:13px;font-family:Arial,sans-serif;color:#555555;">For Australian business operators</p>
    <div style="border-top:3px solid #111111;"></div>
  </td></tr>

  <tr><td style="padding:28px 40px 24px;background:#ffffff;">
    <h2 style="margin:0 0 16px;font-size:14px;font-family:Arial,sans-serif;font-weight:700;color:#111111;text-transform:uppercase;letter-spacing:.08em;border-left:3px solid #111111;padding-left:10px;">Today's Briefing</h2>
    <h3 style="margin:20px 0 8px;font-size:16px;font-weight:700;font-family:Georgia,serif;color:#111111;border-left:3px solid #111111;padding-left:10px;">AI &amp; Technology</h3>
    <p style="margin:0 0 14px;font-size:16px;font-family:Georgia,serif;color:#222222;line-height:1.75;">Meta dropped Llama 4 overnight, a 405-billion-parameter open-weights model that beats GPT-4o on most benchmarks. It's free for commercial use under Meta's community licence — and that changes everything for enterprises tired of paying per token. Google responded within hours, pushing a Gemini Ultra update that extends context windows to two million tokens.</p>
    <h3 style="margin:20px 0 8px;font-size:16px;font-weight:700;font-family:Georgia,serif;color:#111111;border-left:3px solid #111111;padding-left:10px;">Australian Business &amp; Finance</h3>
    <p style="margin:0 0 14px;font-size:16px;font-family:Georgia,serif;color:#222222;line-height:1.75;">The Reserve Bank held the cash rate at 3.85% as expected, though Governor Bullock flagged that persistent services inflation gives the board little room to cut before Q3. The ASX 200 finished flat, with energy names dragging after Brent crude slipped below US$72 on renewed demand fears out of China.</p>
    <h3 style="margin:20px 0 8px;font-size:16px;font-weight:700;font-family:Georgia,serif;color:#111111;border-left:3px solid #111111;padding-left:10px;">World Markets &amp; Global Business</h3>
    <p style="margin:0 0 14px;font-size:16px;font-family:Georgia,serif;color:#222222;line-height:1.75;">Oil slid 2.4% after the IEA trimmed its 2026 demand growth forecast by 300,000 barrels per day, citing slowing industrial activity in China and Germany. The USD gained ground against most majors, while European markets drifted lower ahead of ECB policy minutes due Wednesday.</p>
    <h3 style="margin:20px 0 8px;font-size:16px;font-weight:700;font-family:Georgia,serif;color:#111111;border-left:3px solid #111111;padding-left:10px;">The Big Picture</h3>
    <p style="margin:0 0 14px;font-size:16px;font-family:Georgia,serif;color:#222222;line-height:1.75;">The open-source AI moment is accelerating. With Llama 4 now available to any developer, the moat around closed frontier models narrows week by week. Australian businesses that have been waiting to experiment with AI have never had a cheaper entry point — the question is no longer whether to adopt, but how fast.</p>
  </td></tr>

  <tr><td style="padding:0 40px;"><div style="border-top:1px solid #dddddd;"></div></td></tr>

  <tr><td style="padding:28px 40px 8px;background:#ffffff;">
    <h2 style="margin:0 0 12px;font-size:14px;font-family:Arial,sans-serif;font-weight:700;color:#111111;text-transform:uppercase;letter-spacing:.08em;border-left:3px solid #111111;padding-left:10px;">Artificial Intelligence</h2>
    <p style="margin:0 0 20px;font-size:16px;font-family:Georgia,serif;color:#222222;line-height:1.75;border-left:3px solid #111111;padding-left:10px;">Meta's Llama 4 launch reshapes the open-source AI landscape, while Google and Anthropic each move to defend their positions with model updates and new enterprise partnerships.</p>

    <div style="padding:16px 0;border-bottom:1px solid #eeeeee;">
      <p style="margin:0 0 4px;font-size:11px;font-family:Arial,sans-serif;color:#888888;text-transform:uppercase;letter-spacing:.12em;">META AI</p>
      <h3 style="margin:0 0 6px;font-size:17px;font-weight:700;line-height:1.4;font-family:Georgia,serif;"><a href="#" style="color:#111111;text-decoration:none;">Meta Releases Llama 4: A 405B Open-Weights Model Free for Commercial Use</a></h3>
      <p style="margin:0;font-size:14px;font-family:Arial,sans-serif;color:#444444;line-height:1.6;">Meta's latest open-source model tops public benchmarks across reasoning, coding, and multilingual tasks. The Apache-2.0-style licence removes most commercial restrictions, immediately threatening the paid API market.</p>
    </div>

    <div style="padding:16px 0;border-bottom:1px solid #eeeeee;">
      <p style="margin:0 0 4px;font-size:11px;font-family:Arial,sans-serif;color:#888888;text-transform:uppercase;letter-spacing:.12em;">GOOGLE DEEPMIND</p>
      <h3 style="margin:0 0 6px;font-size:17px;font-weight:700;line-height:1.4;font-family:Georgia,serif;"><a href="#" style="color:#111111;text-decoration:none;">Gemini Ultra 2M: Google Extends Context Window to Two Million Tokens</a></h3>
      <p style="margin:0;font-size:14px;font-family:Arial,sans-serif;color:#444444;line-height:1.6;">Google's updated Gemini Ultra can now process the equivalent of five full novels in a single prompt, opening new doors for legal, financial, and scientific document analysis at enterprise scale.</p>
    </div>

    <div style="padding:16px 0;border-bottom:1px solid #eeeeee;">
      <p style="margin:0 0 4px;font-size:11px;font-family:Arial,sans-serif;color:#888888;text-transform:uppercase;letter-spacing:.12em;">ANTHROPIC</p>
      <h3 style="margin:0 0 6px;font-size:17px;font-weight:700;line-height:1.4;font-family:Georgia,serif;"><a href="#" style="color:#111111;text-decoration:none;">Anthropic Launches Claude for Work: Teams Plan Starts at $25 per Seat</a></h3>
      <p style="margin:0;font-size:14px;font-family:Arial,sans-serif;color:#444444;line-height:1.6;">Anthropic's new Teams tier bundles Claude Sonnet, 100K context, and admin controls into a per-seat model aimed squarely at SMEs. The move puts pressure on Microsoft's Copilot pricing for smaller businesses.</p>
    </div>

    <div style="padding:16px 0;border-bottom:1px solid #eeeeee;">
      <p style="margin:0 0 4px;font-size:11px;font-family:Arial,sans-serif;color:#888888;text-transform:uppercase;letter-spacing:.12em;">TECHCRUNCH</p>
      <h3 style="margin:0 0 6px;font-size:17px;font-weight:700;line-height:1.4;font-family:Georgia,serif;"><a href="#" style="color:#111111;text-decoration:none;">AI Coding Tools Now Handle 40% of Code at Top 10 US Tech Companies</a></h3>
      <p style="margin:0;font-size:14px;font-family:Arial,sans-serif;color:#444444;line-height:1.6;">A new survey of engineering leaders finds that AI-assisted development has crossed a threshold, with nearly half of production code now touched by Copilot, Cursor, or similar tools. Hiring plans for junior engineers are being revised downward as a result.</p>
    </div>
  </td></tr>

  <tr><td style="padding:0 40px;"><div style="border-top:1px solid #dddddd;"></div></td></tr>

  <tr><td style="padding:28px 40px 8px;background:#ffffff;">
    <h2 style="margin:0 0 12px;font-size:14px;font-family:Arial,sans-serif;font-weight:700;color:#111111;text-transform:uppercase;letter-spacing:.08em;border-left:3px solid #111111;padding-left:10px;">World News</h2>
    <p style="margin:0 0 20px;font-size:16px;font-family:Georgia,serif;color:#222222;line-height:1.75;border-left:3px solid #111111;padding-left:10px;">Oil markets lead global risk sentiment lower as demand revisions from the IEA weigh on energy exporters and pressure broader commodity indices.</p>

    <div style="padding:16px 0;border-bottom:1px solid #eeeeee;">
      <p style="margin:0 0 4px;font-size:11px;font-family:Arial,sans-serif;color:#888888;text-transform:uppercase;letter-spacing:.12em;">REUTERS</p>
      <h3 style="margin:0 0 6px;font-size:17px;font-weight:700;line-height:1.4;font-family:Georgia,serif;"><a href="#" style="color:#111111;text-decoration:none;">IEA Cuts 2026 Oil Demand Growth Forecast Amid China Slowdown</a></h3>
      <p style="margin:0;font-size:14px;font-family:Arial,sans-serif;color:#444444;line-height:1.6;">The International Energy Agency trimmed its demand outlook by 300,000 barrels per day, citing weaker Chinese industrial data and faster-than-expected EV adoption in Europe. Brent crude fell to US$71.80, its lowest level since February.</p>
    </div>

    <div style="padding:16px 0;border-bottom:1px solid #eeeeee;">
      <p style="margin:0 0 4px;font-size:11px;font-family:Arial,sans-serif;color:#888888;text-transform:uppercase;letter-spacing:.12em;">BBC NEWS</p>
      <h3 style="margin:0 0 6px;font-size:17px;font-weight:700;line-height:1.4;font-family:Georgia,serif;"><a href="#" style="color:#111111;text-decoration:none;">UK Economy Contracts 0.2% in February as Consumer Spending Stalls</a></h3>
      <p style="margin:0;font-size:14px;font-family:Arial,sans-serif;color:#444444;line-height:1.6;">Britain's GDP shrank for the second consecutive month, raising recession fears ahead of the Bank of England's April policy meeting. Retail sales fell 1.1% as households continued to pare back discretionary spending.</p>
    </div>
  </td></tr>

  <tr><td style="padding:0 40px;"><div style="border-top:1px solid #dddddd;"></div></td></tr>

  <tr><td style="padding:28px 40px 8px;background:#ffffff;">
    <h2 style="margin:0 0 12px;font-size:14px;font-family:Arial,sans-serif;font-weight:700;color:#111111;text-transform:uppercase;letter-spacing:.08em;border-left:3px solid #111111;padding-left:10px;">Australian News</h2>
    <p style="margin:0 0 20px;font-size:16px;font-family:Georgia,serif;color:#222222;line-height:1.75;border-left:3px solid #111111;padding-left:10px;">The RBA's hold decision and weaker energy prices define a cautious start to the week for Australian markets, while retail data provides a mixed read on consumer confidence.</p>

    <div style="padding:16px 0;border-bottom:1px solid #eeeeee;">
      <p style="margin:0 0 4px;font-size:11px;font-family:Arial,sans-serif;color:#888888;text-transform:uppercase;letter-spacing:.12em;">FINANCIAL REVIEW</p>
      <h3 style="margin:0 0 6px;font-size:17px;font-weight:700;line-height:1.4;font-family:Georgia,serif;"><a href="#" style="color:#111111;text-decoration:none;">RBA Holds at 3.85%, Flags Services Inflation as Key Risk</a></h3>
      <p style="margin:0;font-size:14px;font-family:Arial,sans-serif;color:#444444;line-height:1.6;">The board voted unanimously to hold, with Governor Bullock warning that sticky services inflation could delay the first cut until at least August. Markets had priced a 15% chance of a cut; that probability collapsed to near zero post-announcement.</p>
    </div>

    <div style="padding:16px 0;border-bottom:1px solid #eeeeee;">
      <p style="margin:0 0 4px;font-size:11px;font-family:Arial,sans-serif;color:#888888;text-transform:uppercase;letter-spacing:.12em;">SMH</p>
      <h3 style="margin:0 0 6px;font-size:17px;font-weight:700;line-height:1.4;font-family:Georgia,serif;"><a href="#" style="color:#111111;text-decoration:none;">Woolworths Flags 3% Same-Store Sales Decline as Cost Pressures Bite</a></h3>
      <p style="margin:0;font-size:14px;font-family:Arial,sans-serif;color:#444444;line-height:1.6;">The supermarket giant's Q3 trading update disappointed investors, with discretionary categories particularly weak. Management cited ongoing pressure on household budgets and noted that private-label uptake has reached a five-year high.</p>
    </div>

    <div style="padding:16px 0;border-bottom:1px solid #eeeeee;">
      <p style="margin:0 0 4px;font-size:11px;font-family:Arial,sans-serif;color:#888888;text-transform:uppercase;letter-spacing:.12em;">ABC NEWS</p>
      <h3 style="margin:0 0 6px;font-size:17px;font-weight:700;line-height:1.4;font-family:Georgia,serif;"><a href="#" style="color:#111111;text-decoration:none;">Federal Government Launches $2B AI Capability Fund for Australian Businesses</a></h3>
      <p style="margin:0;font-size:14px;font-family:Arial,sans-serif;color:#444444;line-height:1.6;">The Albanese government announced a new grant and co-investment program to help Australian SMEs adopt AI tools, with priority given to manufacturing, agriculture, and professional services. Applications open in June.</p>
    </div>
  </td></tr>

  <tr><td style="padding:24px 40px 32px;background:#ffffff;border-top:2px solid #111111;">
    <table width="100%" cellpadding="0" cellspacing="0">
      <tr>
        <td style="font-size:12px;font-family:Arial,sans-serif;color:#888888;">Your daily AI-powered business briefing</td>
        <td align="right">
          <a href="https://theoperatingbrief.com" style="font-size:11px;font-family:Arial,sans-serif;color:#111111;text-decoration:none;border-bottom:1px solid #111111;margin-right:16px;">Subscribe</a>
          <a href="https://theoperatingbrief.com/unsubscribe" style="font-size:11px;font-family:Arial,sans-serif;color:#888888;text-decoration:none;border-bottom:1px solid #cccccc;">Unsubscribe</a>
        </td>
      </tr>
    </table>
  </td></tr>

</table></td></tr></table>
</body></html>"""


EDITION_2_HTML = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>The Operating Brief – April 17, 2026</title></head>
<body style="margin:0;padding:0;background:#f5f4f0;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f4f0;padding:32px 16px;">
<tr><td align="center">
<table width="620" cellpadding="0" cellspacing="0" style="max-width:620px;width:100%;background:#ffffff;">

  <tr><td style="padding:32px 40px 0;background:#ffffff;">
    <p style="margin:0 0 8px;font-size:11px;font-family:Arial,sans-serif;font-weight:700;color:#888888;text-transform:uppercase;letter-spacing:.12em;">Thursday, April 17 2026</p>
    <h1 style="margin:0;font-size:40px;font-weight:700;color:#111111;font-family:Georgia,serif;line-height:1.1;">The Operating Brief</h1>
    <p style="margin:6px 0 20px;font-size:13px;font-family:Arial,sans-serif;color:#555555;">For Australian business operators</p>
    <div style="border-top:3px solid #111111;"></div>
  </td></tr>

  <tr><td style="padding:28px 40px 24px;background:#ffffff;">
    <h2 style="margin:0 0 16px;font-size:14px;font-family:Arial,sans-serif;font-weight:700;color:#111111;text-transform:uppercase;letter-spacing:.08em;border-left:3px solid #111111;padding-left:10px;">Today's Briefing</h2>
    <h3 style="margin:20px 0 8px;font-size:16px;font-weight:700;font-family:Georgia,serif;color:#111111;border-left:3px solid #111111;padding-left:10px;">AI &amp; Technology</h3>
    <p style="margin:0 0 14px;font-size:16px;font-family:Georgia,serif;color:#222222;line-height:1.75;">OpenAI unveiled GPT-4.5 Turbo with a 50% price cut and double the speed of its predecessor, landing it squarely in the enterprise workflow market. The model's new structured output guarantees and improved tool-calling reliability have developers excited — expect rapid adoption in legal, finance, and operations automation.</p>
    <h3 style="margin:20px 0 8px;font-size:16px;font-weight:700;font-family:Georgia,serif;color:#111111;border-left:3px solid #111111;padding-left:10px;">Australian Business &amp; Finance</h3>
    <p style="margin:0 0 14px;font-size:16px;font-family:Georgia,serif;color:#222222;line-height:1.75;">The ASX 200 hit a fresh record high of 9,412 points, led by the big banks and lithium miners on renewed optimism about Chinese stimulus. ANZ and CBA both posted strong half-year profit updates, with net interest margins holding steadier than analysts expected despite the rate hold environment.</p>
    <h3 style="margin:20px 0 8px;font-size:16px;font-weight:700;font-family:Georgia,serif;color:#111111;border-left:3px solid #111111;padding-left:10px;">World Markets &amp; Global Business</h3>
    <p style="margin:0 0 14px;font-size:16px;font-family:Georgia,serif;color:#222222;line-height:1.75;">The Trump administration extended its 90-day tariff pause on most trading partners for a further 60 days, citing ongoing negotiations with the EU and Japan. Markets rallied on the news, with the S&amp;P 500 closing up 1.8% and the Nasdaq outperforming on renewed tech optimism.</p>
    <h3 style="margin:20px 0 8px;font-size:16px;font-weight:700;font-family:Georgia,serif;color:#111111;border-left:3px solid #111111;padding-left:10px;">The Big Picture</h3>
    <p style="margin:0 0 14px;font-size:16px;font-family:Georgia,serif;color:#222222;line-height:1.75;">A record ASX and a tariff reprieve make for a buoyant end to the week. But the structural shift underneath — AI eating into services jobs, China's economy sputtering, and a global debt reckoning deferred by political deals — means the calm is borrowed. Use the window to reposition, not to relax.</p>
  </td></tr>

  <tr><td style="padding:0 40px;"><div style="border-top:1px solid #dddddd;"></div></td></tr>

  <tr><td style="padding:28px 40px 8px;background:#ffffff;">
    <h2 style="margin:0 0 12px;font-size:14px;font-family:Arial,sans-serif;font-weight:700;color:#111111;text-transform:uppercase;letter-spacing:.08em;border-left:3px solid #111111;padding-left:10px;">Artificial Intelligence</h2>
    <p style="margin:0 0 20px;font-size:16px;font-family:Georgia,serif;color:#222222;line-height:1.75;border-left:3px solid #111111;padding-left:10px;">OpenAI's GPT-4.5 Turbo launch sets a new price-performance benchmark, while the AI agent ecosystem matures with new orchestration frameworks from Microsoft and a wave of vertical-specific deployments.</p>

    <div style="padding:16px 0;border-bottom:1px solid #eeeeee;">
      <p style="margin:0 0 4px;font-size:11px;font-family:Arial,sans-serif;color:#888888;text-transform:uppercase;letter-spacing:.12em;">OPENAI</p>
      <h3 style="margin:0 0 6px;font-size:17px;font-weight:700;line-height:1.4;font-family:Georgia,serif;"><a href="#" style="color:#111111;text-decoration:none;">OpenAI Launches GPT-4.5 Turbo: 50% Cheaper, Twice as Fast</a></h3>
      <p style="margin:0;font-size:14px;font-family:Arial,sans-serif;color:#444444;line-height:1.6;">The new model delivers near-GPT-4-quality outputs at substantially reduced cost, with improved structured output reliability and tool-call accuracy. OpenAI says it was specifically tuned for agentic workflows and long-horizon tasks.</p>
    </div>

    <div style="padding:16px 0;border-bottom:1px solid #eeeeee;">
      <p style="margin:0 0 4px;font-size:11px;font-family:Arial,sans-serif;color:#888888;text-transform:uppercase;letter-spacing:.12em;">MICROSOFT</p>
      <h3 style="margin:0 0 6px;font-size:17px;font-weight:700;line-height:1.4;font-family:Georgia,serif;"><a href="#" style="color:#111111;text-decoration:none;">Microsoft Copilot Studio Gets Multi-Agent Orchestration for Enterprise Workflows</a></h3>
      <p style="margin:0;font-size:14px;font-family:Arial,sans-serif;color:#444444;line-height:1.6;">Microsoft's new release lets enterprises build networks of AI agents that hand off tasks between each other with human-in-the-loop checkpoints. The feature is already in preview with 200 enterprise customers across financial services and healthcare.</p>
    </div>

    <div style="padding:16px 0;border-bottom:1px solid #eeeeee;">
      <p style="margin:0 0 4px;font-size:11px;font-family:Arial,sans-serif;color:#888888;text-transform:uppercase;letter-spacing:.12em;">VENTURE BEAT</p>
      <h3 style="margin:0 0 6px;font-size:17px;font-weight:700;line-height:1.4;font-family:Georgia,serif;"><a href="#" style="color:#111111;text-decoration:none;">AI in Legal: Three Big Law Firms Cut First-Year Associate Intake by 30%</a></h3>
      <p style="margin:0;font-size:14px;font-family:Arial,sans-serif;color:#444444;line-height:1.6;">Kirkland &amp; Ellis, Latham &amp; Watkins, and Sullivan &amp; Cromwell have each announced reduced graduate intakes as AI document review and drafting tools handle tasks previously assigned to junior lawyers. The shift is accelerating faster than the industry anticipated two years ago.</p>
    </div>

    <div style="padding:16px 0;border-bottom:1px solid #eeeeee;">
      <p style="margin:0 0 4px;font-size:11px;font-family:Arial,sans-serif;color:#888888;text-transform:uppercase;letter-spacing:.12em;">THE VERGE</p>
      <h3 style="margin:0 0 6px;font-size:17px;font-weight:700;line-height:1.4;font-family:Georgia,serif;"><a href="#" style="color:#111111;text-decoration:none;">NVIDIA H300 Chips Enter Mass Production Ahead of Schedule</a></h3>
      <p style="margin:0;font-size:14px;font-family:Arial,sans-serif;color:#444444;line-height:1.6;">NVIDIA confirmed its next-generation H300 AI accelerator has entered volume production two quarters early, with initial allocations going to AWS, Azure, and Google Cloud. The chip delivers a claimed 3x throughput improvement over the H100 for transformer workloads.</p>
    </div>
  </td></tr>

  <tr><td style="padding:0 40px;"><div style="border-top:1px solid #dddddd;"></div></td></tr>

  <tr><td style="padding:28px 40px 8px;background:#ffffff;">
    <h2 style="margin:0 0 12px;font-size:14px;font-family:Arial,sans-serif;font-weight:700;color:#111111;text-transform:uppercase;letter-spacing:.08em;border-left:3px solid #111111;padding-left:10px;">World News</h2>
    <p style="margin:0 0 20px;font-size:16px;font-family:Georgia,serif;color:#222222;line-height:1.75;border-left:3px solid #111111;padding-left:10px;">The US tariff pause extension provides markets with temporary relief, though trade negotiators warn that a permanent deal with the EU remains at least six months away.</p>

    <div style="padding:16px 0;border-bottom:1px solid #eeeeee;">
      <p style="margin:0 0 4px;font-size:11px;font-family:Arial,sans-serif;color:#888888;text-transform:uppercase;letter-spacing:.12em;">REUTERS</p>
      <h3 style="margin:0 0 6px;font-size:17px;font-weight:700;line-height:1.4;font-family:Georgia,serif;"><a href="#" style="color:#111111;text-decoration:none;">Trump Extends Tariff Pause by 60 Days as EU Trade Talks Progress</a></h3>
      <p style="margin:0;font-size:14px;font-family:Arial,sans-serif;color:#444444;line-height:1.6;">The White House cited "meaningful progress" in talks with Brussels as justification for the extension, though a comprehensive deal on steel, aluminium, and digital services tariffs remains elusive. Japan and South Korea are also covered by the pause.</p>
    </div>

    <div style="padding:16px 0;border-bottom:1px solid #eeeeee;">
      <p style="margin:0 0 4px;font-size:11px;font-family:Arial,sans-serif;color:#888888;text-transform:uppercase;letter-spacing:.12em;">GUARDIAN</p>
      <h3 style="margin:0 0 6px;font-size:17px;font-weight:700;line-height:1.4;font-family:Georgia,serif;"><a href="#" style="color:#111111;text-decoration:none;">China's Q1 GDP Growth Beats Forecasts at 5.1%, But Property Drag Persists</a></h3>
      <p style="margin:0;font-size:14px;font-family:Arial,sans-serif;color:#444444;line-height:1.6;">China's economy grew 5.1% in the first quarter, marginally ahead of the government's 5% target, driven by exports and state infrastructure spending. However, property investment fell 8.3%, and consumer confidence remains subdued heading into Q2.</p>
    </div>
  </td></tr>

  <tr><td style="padding:0 40px;"><div style="border-top:1px solid #dddddd;"></div></td></tr>

  <tr><td style="padding:28px 40px 8px;background:#ffffff;">
    <h2 style="margin:0 0 12px;font-size:14px;font-family:Arial,sans-serif;font-weight:700;color:#111111;text-transform:uppercase;letter-spacing:.08em;border-left:3px solid #111111;padding-left:10px;">Australian News</h2>
    <p style="margin:0 0 20px;font-size:16px;font-family:Georgia,serif;color:#222222;line-height:1.75;border-left:3px solid #111111;padding-left:10px;">The ASX record and strong bank earnings cap a strong week for Australian equities, while the government's infrastructure pipeline announcement signals intent ahead of the federal budget.</p>

    <div style="padding:16px 0;border-bottom:1px solid #eeeeee;">
      <p style="margin:0 0 4px;font-size:11px;font-family:Arial,sans-serif;color:#888888;text-transform:uppercase;letter-spacing:.12em;">FINANCIAL REVIEW</p>
      <h3 style="margin:0 0 6px;font-size:17px;font-weight:700;line-height:1.4;font-family:Georgia,serif;"><a href="#" style="color:#111111;text-decoration:none;">ASX 200 Hits Record 9,412 on Bank Earnings and Global Risk Rally</a></h3>
      <p style="margin:0;font-size:14px;font-family:Arial,sans-serif;color:#444444;line-height:1.6;">Australia's benchmark index closed at an all-time high, with financials adding 2.1% on the day after ANZ reported cash profit up 6% and CBA reaffirmed its full-year dividend guidance. Lithium stocks also rallied on Chinese stimulus speculation.</p>
    </div>

    <div style="padding:16px 0;border-bottom:1px solid #eeeeee;">
      <p style="margin:0 0 4px;font-size:11px;font-family:Arial,sans-serif;color:#888888;text-transform:uppercase;letter-spacing:.12em;">ABC NEWS</p>
      <h3 style="margin:0 0 6px;font-size:17px;font-weight:700;line-height:1.4;font-family:Georgia,serif;"><a href="#" style="color:#111111;text-decoration:none;">Government Announces $14B Fast Rail Corridor Between Sydney and Newcastle</a></h3>
      <p style="margin:0;font-size:14px;font-family:Arial,sans-serif;color:#444444;line-height:1.6;">Infrastructure Minister Catherine King confirmed the project will proceed to detailed design, with construction expected to begin in 2028. The corridor would cut travel time from 2.5 hours to under 60 minutes, and is projected to unlock significant residential development along the route.</p>
    </div>
  </td></tr>

  <tr><td style="padding:24px 40px 32px;background:#ffffff;border-top:2px solid #111111;">
    <table width="100%" cellpadding="0" cellspacing="0">
      <tr>
        <td style="font-size:12px;font-family:Arial,sans-serif;color:#888888;">Your daily AI-powered business briefing</td>
        <td align="right">
          <a href="https://theoperatingbrief.com" style="font-size:11px;font-family:Arial,sans-serif;color:#111111;text-decoration:none;border-bottom:1px solid #111111;margin-right:16px;">Subscribe</a>
          <a href="https://theoperatingbrief.com/unsubscribe" style="font-size:11px;font-family:Arial,sans-serif;color:#888888;text-decoration:none;border-bottom:1px solid #cccccc;">Unsubscribe</a>
        </td>
      </tr>
    </table>
  </td></tr>

</table></td></tr></table>
</body></html>"""


EDITION_3_HTML = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>The Operating Brief – April 23, 2026</title></head>
<body style="margin:0;padding:0;background:#f5f4f0;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f4f0;padding:32px 16px;">
<tr><td align="center">
<table width="620" cellpadding="0" cellspacing="0" style="max-width:620px;width:100%;background:#ffffff;">

  <tr><td style="padding:32px 40px 0;background:#ffffff;">
    <p style="margin:0 0 8px;font-size:11px;font-family:Arial,sans-serif;font-weight:700;color:#888888;text-transform:uppercase;letter-spacing:.12em;">Thursday, April 23 2026</p>
    <h1 style="margin:0;font-size:40px;font-weight:700;color:#111111;font-family:Georgia,serif;line-height:1.1;">The Operating Brief</h1>
    <p style="margin:6px 0 20px;font-size:13px;font-family:Arial,sans-serif;color:#555555;">For Australian business operators</p>
    <div style="border-top:3px solid #111111;"></div>
  </td></tr>

  <tr><td style="padding:28px 40px 24px;background:#ffffff;">
    <h2 style="margin:0 0 16px;font-size:14px;font-family:Arial,sans-serif;font-weight:700;color:#111111;text-transform:uppercase;letter-spacing:.08em;border-left:3px solid #111111;padding-left:10px;">Today's Briefing</h2>
    <h3 style="margin:20px 0 8px;font-size:16px;font-weight:700;font-family:Georgia,serif;color:#111111;border-left:3px solid #111111;padding-left:10px;">AI &amp; Technology</h3>
    <p style="margin:0 0 14px;font-size:16px;font-family:Georgia,serif;color:#222222;line-height:1.75;">Apple's WWDC preview event landed with a bang: an entirely redesigned MacBook Pro featuring Apple's M4 Ultra chip, purpose-built for on-device AI inference. The machine can run 70B parameter models locally without internet connectivity — a privacy-first pitch that enterprise security teams will welcome.</p>
    <h3 style="margin:20px 0 8px;font-size:16px;font-weight:700;font-family:Georgia,serif;color:#111111;border-left:3px solid #111111;padding-left:10px;">Australian Business &amp; Finance</h3>
    <p style="margin:0 0 14px;font-size:16px;font-family:Georgia,serif;color:#222222;line-height:1.75;">Qantas announced its largest ever network expansion, adding 40 new international and domestic routes effective from October. CEO Vanessa Hudson cited record forward bookings and said the airline is now operating at 108% of pre-COVID capacity. The announcement sent QAN shares up 4.2%.</p>
    <h3 style="margin:20px 0 8px;font-size:16px;font-weight:700;font-family:Georgia,serif;color:#111111;border-left:3px solid #111111;padding-left:10px;">World Markets &amp; Global Business</h3>
    <p style="margin:0 0 14px;font-size:16px;font-family:Georgia,serif;color:#222222;line-height:1.75;">The IMF cut its global growth forecast to 2.7% for 2026, down 0.3 percentage points from its January estimate, citing geopolitical fragmentation, elevated debt servicing costs, and weaker-than-expected productivity growth outside the United States. Advanced economies are expected to grow just 1.5%.</p>
    <h3 style="margin:20px 0 8px;font-size:16px;font-weight:700;font-family:Georgia,serif;color:#111111;border-left:3px solid #111111;padding-left:10px;">The Big Picture</h3>
    <p style="margin:0 0 14px;font-size:16px;font-family:Georgia,serif;color:#222222;line-height:1.75;">Apple's AI-native hardware shift signals that the next competitive frontier is not the cloud — it is the edge. Whoever controls the chip running AI in your laptop, phone, and factory floor controls the data. For Australian businesses, the question is whether sovereign AI infrastructure becomes a national priority before it becomes a national vulnerability.</p>
  </td></tr>

  <tr><td style="padding:0 40px;"><div style="border-top:1px solid #dddddd;"></div></td></tr>

  <tr><td style="padding:28px 40px 8px;background:#ffffff;">
    <h2 style="margin:0 0 12px;font-size:14px;font-family:Arial,sans-serif;font-weight:700;color:#111111;text-transform:uppercase;letter-spacing:.08em;border-left:3px solid #111111;padding-left:10px;">Artificial Intelligence</h2>
    <p style="margin:0 0 20px;font-size:16px;font-family:Georgia,serif;color:#222222;line-height:1.75;border-left:3px solid #111111;padding-left:10px;">Apple's on-device AI push dominates hardware news, while model efficiency breakthroughs and new multimodal capabilities continue to expand what's possible at the application layer.</p>

    <div style="padding:16px 0;border-bottom:1px solid #eeeeee;">
      <p style="margin:0 0 4px;font-size:11px;font-family:Arial,sans-serif;color:#888888;text-transform:uppercase;letter-spacing:.12em;">APPLE</p>
      <h3 style="margin:0 0 6px;font-size:17px;font-weight:700;line-height:1.4;font-family:Georgia,serif;"><a href="#" style="color:#111111;text-decoration:none;">Apple Unveils AI-Native MacBook Pro with M4 Ultra: Runs 70B Models Locally</a></h3>
      <p style="margin:0;font-size:14px;font-family:Arial,sans-serif;color:#444444;line-height:1.6;">The new MacBook Pro ships with 192GB unified memory as standard and a Neural Engine delivering 38 TOPS of local AI performance. Apple Intelligence features run entirely on-device, with no data leaving the machine — a significant differentiation from cloud-dependent competitors.</p>
    </div>

    <div style="padding:16px 0;border-bottom:1px solid #eeeeee;">
      <p style="margin:0 0 4px;font-size:11px;font-family:Arial,sans-serif;color:#888888;text-transform:uppercase;letter-spacing:.12em;">GOOGLE DEEPMIND</p>
      <h3 style="margin:0 0 6px;font-size:17px;font-weight:700;line-height:1.4;font-family:Georgia,serif;"><a href="#" style="color:#111111;text-decoration:none;">DeepMind's Gemma 3 Achieves GPT-4 Performance at 1/10th the Parameter Count</a></h3>
      <p style="margin:0;font-size:14px;font-family:Arial,sans-serif;color:#444444;line-height:1.6;">Google's latest open-weights model demonstrates that model efficiency is advancing at least as fast as raw scale. Gemma 3's architecture innovations could make capable AI feasible on consumer-grade hardware within 18 months.</p>
    </div>

    <div style="padding:16px 0;border-bottom:1px solid #eeeeee;">
      <p style="margin:0 0 4px;font-size:11px;font-family:Arial,sans-serif;color:#888888;text-transform:uppercase;letter-spacing:.12em;">TECHCRUNCH</p>
      <h3 style="margin:0 0 6px;font-size:17px;font-weight:700;line-height:1.4;font-family:Georgia,serif;"><a href="#" style="color:#111111;text-decoration:none;">Salesforce Agentforce Surpasses 5,000 Enterprise Deployments in 90 Days</a></h3>
      <p style="margin:0;font-size:14px;font-family:Arial,sans-serif;color:#444444;line-height:1.6;">Salesforce's AI agent platform has seen explosive adoption in customer service, sales operations, and field service. The company says average handle time has dropped 35% for customers using Agentforce in contact centre roles.</p>
    </div>

    <div style="padding:16px 0;border-bottom:1px solid #eeeeee;">
      <p style="margin:0 0 4px;font-size:11px;font-family:Arial,sans-serif;color:#888888;text-transform:uppercase;letter-spacing:.12em;">MIT TECHNOLOGY REVIEW</p>
      <h3 style="margin:0 0 6px;font-size:17px;font-weight:700;line-height:1.4;font-family:Georgia,serif;"><a href="#" style="color:#111111;text-decoration:none;">AI Systems Now Solve 85% of IMO Maths Problems — Experts Divided on What It Means</a></h3>
      <p style="margin:0;font-size:14px;font-family:Arial,sans-serif;color:#444444;line-height:1.6;">A new benchmark study shows frontier AI models can now correctly solve the majority of International Mathematical Olympiad problems, a level previously considered beyond near-term AI capability. Researchers disagree on whether this signals genuine reasoning or sophisticated pattern matching.</p>
    </div>
  </td></tr>

  <tr><td style="padding:0 40px;"><div style="border-top:1px solid #dddddd;"></div></td></tr>

  <tr><td style="padding:28px 40px 8px;background:#ffffff;">
    <h2 style="margin:0 0 12px;font-size:14px;font-family:Arial,sans-serif;font-weight:700;color:#111111;text-transform:uppercase;letter-spacing:.08em;border-left:3px solid #111111;padding-left:10px;">World News</h2>
    <p style="margin:0 0 20px;font-size:16px;font-family:Georgia,serif;color:#222222;line-height:1.75;border-left:3px solid #111111;padding-left:10px;">The IMF's downgraded global growth forecast casts a shadow over otherwise buoyant equity markets, as the gap between financial asset prices and underlying economic momentum widens.</p>

    <div style="padding:16px 0;border-bottom:1px solid #eeeeee;">
      <p style="margin:0 0 4px;font-size:11px;font-family:Arial,sans-serif;color:#888888;text-transform:uppercase;letter-spacing:.12em;">IMF / REUTERS</p>
      <h3 style="margin:0 0 6px;font-size:17px;font-weight:700;line-height:1.4;font-family:Georgia,serif;"><a href="#" style="color:#111111;text-decoration:none;">IMF Cuts Global Growth Forecast to 2.7% for 2026, Cites Debt and Fragmentation</a></h3>
      <p style="margin:0;font-size:14px;font-family:Arial,sans-serif;color:#444444;line-height:1.6;">The fund's World Economic Outlook flagged elevated sovereign debt servicing costs, geopolitical supply chain fragmentation, and a slowdown in total factor productivity as the three biggest drags. Emerging markets face particular pressure from a strong USD.</p>
    </div>

    <div style="padding:16px 0;border-bottom:1px solid #eeeeee;">
      <p style="margin:0 0 4px;font-size:11px;font-family:Arial,sans-serif;color:#888888;text-transform:uppercase;letter-spacing:.12em;">BBC NEWS</p>
      <h3 style="margin:0 0 6px;font-size:17px;font-weight:700;line-height:1.4;font-family:Georgia,serif;"><a href="#" style="color:#111111;text-decoration:none;">India Overtakes Japan to Become World's Third-Largest Economy</a></h3>
      <p style="margin:0;font-size:14px;font-family:Arial,sans-serif;color:#444444;line-height:1.6;">India's nominal GDP surpassed Japan's in Q1 2026 on IMF data, a milestone that reflects both India's rapid growth and Japan's persistent stagnation. The shift has significant implications for global trade routes, investment patterns, and geopolitical alliances in the Indo-Pacific.</p>
    </div>
  </td></tr>

  <tr><td style="padding:0 40px;"><div style="border-top:1px solid #dddddd;"></div></td></tr>

  <tr><td style="padding:28px 40px 8px;background:#ffffff;">
    <h2 style="margin:0 0 12px;font-size:14px;font-family:Arial,sans-serif;font-weight:700;color:#111111;text-transform:uppercase;letter-spacing:.08em;border-left:3px solid #111111;padding-left:10px;">Australian News</h2>
    <p style="margin:0 0 20px;font-size:16px;font-family:Georgia,serif;color:#222222;line-height:1.75;border-left:3px solid #111111;padding-left:10px;">Qantas's network expansion and a strong jobs report reinforce Australia's relative economic resilience, even as the global growth outlook dims.</p>

    <div style="padding:16px 0;border-bottom:1px solid #eeeeee;">
      <p style="margin:0 0 4px;font-size:11px;font-family:Arial,sans-serif;color:#888888;text-transform:uppercase;letter-spacing:.12em;">FINANCIAL REVIEW</p>
      <h3 style="margin:0 0 6px;font-size:17px;font-weight:700;line-height:1.4;font-family:Georgia,serif;"><a href="#" style="color:#111111;text-decoration:none;">Qantas Announces 40 New Routes as Air Travel Demand Hits Post-COVID Peak</a></h3>
      <p style="margin:0;font-size:14px;font-family:Arial,sans-serif;color:#444444;line-height:1.6;">The expansion includes new direct services from Melbourne to Mumbai and Sydney to Athens, plus 18 additional domestic frequencies. Qantas cited record load factors and corporate travel recovery as key drivers, with forward bookings for the next 12 months at an all-time high.</p>
    </div>

    <div style="padding:16px 0;border-bottom:1px solid #eeeeee;">
      <p style="margin:0 0 4px;font-size:11px;font-family:Arial,sans-serif;color:#888888;text-transform:uppercase;letter-spacing:.12em;">ABS / ABC NEWS</p>
      <h3 style="margin:0 0 6px;font-size:17px;font-weight:700;line-height:1.4;font-family:Georgia,serif;"><a href="#" style="color:#111111;text-decoration:none;">Australia Adds 52,000 Jobs in March; Unemployment Holds at 3.9%</a></h3>
      <p style="margin:0;font-size:14px;font-family:Arial,sans-serif;color:#444444;line-height:1.6;">The labour market continues to defy expectations, with full-time employment rising 38,000 and the participation rate at 67.1% — the highest since records began. The strong reading reduces the case for an RBA cut in May, according to most economists.</p>
    </div>

    <div style="padding:16px 0;border-bottom:1px solid #eeeeee;">
      <p style="margin:0 0 4px;font-size:11px;font-family:Arial,sans-serif;color:#888888;text-transform:uppercase;letter-spacing:.12em;">SMH</p>
      <h3 style="margin:0 0 6px;font-size:17px;font-weight:700;line-height:1.4;font-family:Georgia,serif;"><a href="#" style="color:#111111;text-decoration:none;">Sydney Housing Approvals Rise 12% on Density Reform as Vacancy Rate Ticks Up</a></h3>
      <p style="margin:0;font-size:14px;font-family:Arial,sans-serif;color:#444444;line-height:1.6;">New apartment and townhouse approvals in Greater Sydney rose sharply in March following the state government's medium-density zoning reforms. Industry groups say the pipeline is real but caution that build costs and labour shortages could delay completions by 12-18 months.</p>
    </div>
  </td></tr>

  <tr><td style="padding:24px 40px 32px;background:#ffffff;border-top:2px solid #111111;">
    <table width="100%" cellpadding="0" cellspacing="0">
      <tr>
        <td style="font-size:12px;font-family:Arial,sans-serif;color:#888888;">Your daily AI-powered business briefing</td>
        <td align="right">
          <a href="https://theoperatingbrief.com" style="font-size:11px;font-family:Arial,sans-serif;color:#111111;text-decoration:none;border-bottom:1px solid #111111;margin-right:16px;">Subscribe</a>
          <a href="https://theoperatingbrief.com/unsubscribe" style="font-size:11px;font-family:Arial,sans-serif;color:#888888;text-decoration:none;border-bottom:1px solid #cccccc;">Unsubscribe</a>
        </td>
      </tr>
    </table>
  </td></tr>

</table></td></tr></table>
</body></html>"""


EDITION_4_HTML = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>The Operating Brief – April 29, 2026</title></head>
<body style="margin:0;padding:0;background:#f5f4f0;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f4f0;padding:32px 16px;">
<tr><td align="center">
<table width="620" cellpadding="0" cellspacing="0" style="max-width:620px;width:100%;background:#ffffff;">

  <tr><td style="padding:32px 40px 0;background:#ffffff;">
    <p style="margin:0 0 8px;font-size:11px;font-family:Arial,sans-serif;font-weight:700;color:#888888;text-transform:uppercase;letter-spacing:.12em;">Wednesday, April 29 2026</p>
    <h1 style="margin:0;font-size:40px;font-weight:700;color:#111111;font-family:Georgia,serif;line-height:1.1;">The Operating Brief</h1>
    <p style="margin:6px 0 20px;font-size:13px;font-family:Arial,sans-serif;color:#555555;">For Australian business operators</p>
    <div style="border-top:3px solid #111111;"></div>
  </td></tr>

  <tr><td style="padding:28px 40px 24px;background:#ffffff;">
    <h2 style="margin:0 0 16px;font-size:14px;font-family:Arial,sans-serif;font-weight:700;color:#111111;text-transform:uppercase;letter-spacing:.08em;border-left:3px solid #111111;padding-left:10px;">Today's Briefing</h2>
    <h3 style="margin:20px 0 8px;font-size:16px;font-weight:700;font-family:Georgia,serif;color:#111111;border-left:3px solid #111111;padding-left:10px;">AI &amp; Technology</h3>
    <p style="margin:0 0 14px;font-size:16px;font-family:Georgia,serif;color:#222222;line-height:1.75;">Google DeepMind's AlphaFold 3 update has achieved a new benchmark in protein structure prediction, now accurately modelling 98.6% of known human proteins and extending to RNA-protein interaction complexes. Drug discovery timelines are being compressed from decades to months at the world's top pharmaceutical companies.</p>
    <h3 style="margin:20px 0 8px;font-size:16px;font-weight:700;font-family:Georgia,serif;color:#111111;border-left:3px solid #111111;padding-left:10px;">Australian Business &amp; Finance</h3>
    <p style="margin:0 0 14px;font-size:16px;font-family:Georgia,serif;color:#222222;line-height:1.75;">Queensland Premier Steven Miles has called a snap state election for June 14, six months ahead of schedule, citing a desire for a fresh mandate on the state's $28B energy transition program. Polling shows Labor trailing the LNP by four points, making this a genuine contest. Business groups have called for policy certainty on the Pioneer-Burdekin pumped hydro project.</p>
    <h3 style="margin:20px 0 8px;font-size:16px;font-weight:700;font-family:Georgia,serif;color:#111111;border-left:3px solid #111111;padding-left:10px;">World Markets &amp; Global Business</h3>
    <p style="margin:0 0 14px;font-size:16px;font-family:Georgia,serif;color:#222222;line-height:1.75;">The US dollar hit a five-year high against a trade-weighted basket of currencies after the Fed signalled it will hold rates at 5.25% through at least Q3 2026. The strong greenback is pressuring commodity prices, emerging market debt, and any company with significant USD-denominated costs.</p>
    <h3 style="margin:20px 0 8px;font-size:16px;font-weight:700;font-family:Georgia,serif;color:#111111;border-left:3px solid #111111;padding-left:10px;">The Big Picture</h3>
    <p style="margin:0 0 14px;font-size:16px;font-family:Georgia,serif;color:#222222;line-height:1.75;">AlphaFold's protein milestone is more than a science story — it is a preview of AI's economic impact in sectors we have barely begun to map. Healthcare, materials science, agriculture, and climate modelling all stand to be transformed. Australian businesses in biotech, agri-tech, and advanced manufacturing should be watching this technology category closely: the commercial applications are arriving faster than most roadmaps assumed.</p>
  </td></tr>

  <tr><td style="padding:0 40px;"><div style="border-top:1px solid #dddddd;"></div></td></tr>

  <tr><td style="padding:28px 40px 8px;background:#ffffff;">
    <h2 style="margin:0 0 12px;font-size:14px;font-family:Arial,sans-serif;font-weight:700;color:#111111;text-transform:uppercase;letter-spacing:.08em;border-left:3px solid #111111;padding-left:10px;">Artificial Intelligence</h2>
    <p style="margin:0 0 20px;font-size:16px;font-family:Georgia,serif;color:#222222;line-height:1.75;border-left:3px solid #111111;padding-left:10px;">DeepMind's protein folding breakthrough leads a week of AI advances in scientific computing, while enterprise AI deployment crosses key adoption thresholds in financial services and healthcare.</p>

    <div style="padding:16px 0;border-bottom:1px solid #eeeeee;">
      <p style="margin:0 0 4px;font-size:11px;font-family:Arial,sans-serif;color:#888888;text-transform:uppercase;letter-spacing:.12em;">GOOGLE DEEPMIND</p>
      <h3 style="margin:0 0 6px;font-size:17px;font-weight:700;line-height:1.4;font-family:Georgia,serif;"><a href="#" style="color:#111111;text-decoration:none;">AlphaFold 3 Sets New Protein Prediction Record: 98.6% of Human Proteome Solved</a></h3>
      <p style="margin:0;font-size:14px;font-family:Arial,sans-serif;color:#444444;line-height:1.6;">DeepMind's updated model now accurately predicts the structure of nearly all known human proteins, including difficult disordered regions and multi-protein complexes. Pfizer, Roche, and Novo Nordisk have all announced expanded partnerships to use AlphaFold in their drug discovery pipelines.</p>
    </div>

    <div style="padding:16px 0;border-bottom:1px solid #eeeeee;">
      <p style="margin:0 0 4px;font-size:11px;font-family:Arial,sans-serif;color:#888888;text-transform:uppercase;letter-spacing:.12em;">OPENAI</p>
      <h3 style="margin:0 0 6px;font-size:17px;font-weight:700;line-height:1.4;font-family:Georgia,serif;"><a href="#" style="color:#111111;text-decoration:none;">OpenAI's o4 Reasoning Model Passes CPA Exam with 91% Score</a></h3>
      <p style="margin:0;font-size:14px;font-family:Arial,sans-serif;color:#444444;line-height:1.6;">OpenAI's latest reasoning model scored in the 91st percentile on the Uniform CPA Exam, surpassing most human candidates. The result accelerates conversations in the accounting and audit sectors about the role of junior professionals in a world where AI handles routine compliance work.</p>
    </div>

    <div style="padding:16px 0;border-bottom:1px solid #eeeeee;">
      <p style="margin:0 0 4px;font-size:11px;font-family:Arial,sans-serif;color:#888888;text-transform:uppercase;letter-spacing:.12em;">VENTURE BEAT</p>
      <h3 style="margin:0 0 6px;font-size:17px;font-weight:700;line-height:1.4;font-family:Georgia,serif;"><a href="#" style="color:#111111;text-decoration:none;">AI Spending in Financial Services Reaches $47B Annually, Up 60% Year-on-Year</a></h3>
      <p style="margin:0;font-size:14px;font-family:Arial,sans-serif;color:#444444;line-height:1.6;">A new IDC report finds that banks, insurers, and asset managers collectively spent $47B on AI tools, infrastructure, and talent in the 12 months to March 2026. Fraud detection, credit risk modelling, and customer service automation are the top three use cases by investment volume.</p>
    </div>

    <div style="padding:16px 0;border-bottom:1px solid #eeeeee;">
      <p style="margin:0 0 4px;font-size:11px;font-family:Arial,sans-serif;color:#888888;text-transform:uppercase;letter-spacing:.12em;">WIRED</p>
      <h3 style="margin:0 0 6px;font-size:17px;font-weight:700;line-height:1.4;font-family:Georgia,serif;"><a href="#" style="color:#111111;text-decoration:none;">The First AI-Designed Drug Enters Phase III Clinical Trials</a></h3>
      <p style="margin:0;font-size:14px;font-family:Arial,sans-serif;color:#444444;line-height:1.6;">A compound designed entirely by an AI system — from target identification to molecular structure — has entered the final stage of clinical trials for a rare form of lung cancer. If approved, it would be the first AI-originated drug to reach market, a milestone that would transform the $1.4T pharmaceutical industry.</p>
    </div>
  </td></tr>

  <tr><td style="padding:0 40px;"><div style="border-top:1px solid #dddddd;"></div></td></tr>

  <tr><td style="padding:28px 40px 8px;background:#ffffff;">
    <h2 style="margin:0 0 12px;font-size:14px;font-family:Arial,sans-serif;font-weight:700;color:#111111;text-transform:uppercase;letter-spacing:.08em;border-left:3px solid #111111;padding-left:10px;">World News</h2>
    <p style="margin:0 0 20px;font-size:16px;font-family:Georgia,serif;color:#222222;line-height:1.75;border-left:3px solid #111111;padding-left:10px;">The USD's five-year high reflects the divergence between a resilient US economy and slowing growth across Europe and Asia, creating pressure on emerging market currencies and commodity exporters.</p>

    <div style="padding:16px 0;border-bottom:1px solid #eeeeee;">
      <p style="margin:0 0 4px;font-size:11px;font-family:Arial,sans-serif;color:#888888;text-transform:uppercase;letter-spacing:.12em;">FINANCIAL TIMES</p>
      <h3 style="margin:0 0 6px;font-size:17px;font-weight:700;line-height:1.4;font-family:Georgia,serif;"><a href="#" style="color:#111111;text-decoration:none;">US Dollar Hits Five-Year High as Fed Signals Extended Hold</a></h3>
      <p style="margin:0;font-size:14px;font-family:Arial,sans-serif;color:#444444;line-height:1.6;">Fed Chair Powell's remarks at the April FOMC meeting dashed hopes of a summer rate cut, sending the DXY index to 112.4, its highest since 2021. The strong dollar is complicating monetary policy in Japan, Indonesia, and Brazil, all of which are struggling with capital outflows.</p>
    </div>

    <div style="padding:16px 0;border-bottom:1px solid #eeeeee;">
      <p style="margin:0 0 4px;font-size:11px;font-family:Arial,sans-serif;color:#888888;text-transform:uppercase;letter-spacing:.12em;">BBC NEWS</p>
      <h3 style="margin:0 0 6px;font-size:17px;font-weight:700;line-height:1.4;font-family:Georgia,serif;"><a href="#" style="color:#111111;text-decoration:none;">EU Carbon Border Adjustment Mechanism Raises $4B in First Quarter of Operation</a></h3>
      <p style="margin:0;font-size:14px;font-family:Arial,sans-serif;color:#444444;line-height:1.6;">The EU's carbon tariff on imported goods from high-emission sectors collected its first significant revenue in Q1 2026, with steel, aluminium, and cement imports from China, India, and Turkey the largest contributors. Australian exporters of covered goods face a CBAM compliance deadline in Q4.</p>
    </div>
  </td></tr>

  <tr><td style="padding:0 40px;"><div style="border-top:1px solid #dddddd;"></div></td></tr>

  <tr><td style="padding:28px 40px 8px;background:#ffffff;">
    <h2 style="margin:0 0 12px;font-size:14px;font-family:Arial,sans-serif;font-weight:700;color:#111111;text-transform:uppercase;letter-spacing:.08em;border-left:3px solid #111111;padding-left:10px;">Australian News</h2>
    <p style="margin:0 0 20px;font-size:16px;font-family:Georgia,serif;color:#222222;line-height:1.75;border-left:3px solid #111111;padding-left:10px;">Queensland's snap election injects political uncertainty into Australia's largest energy transition project, while federal budget speculation intensifies ahead of the May 12 announcement.</p>

    <div style="padding:16px 0;border-bottom:1px solid #eeeeee;">
      <p style="margin:0 0 4px;font-size:11px;font-family:Arial,sans-serif;color:#888888;text-transform:uppercase;letter-spacing:.12em;">ABC NEWS</p>
      <h3 style="margin:0 0 6px;font-size:17px;font-weight:700;line-height:1.4;font-family:Georgia,serif;"><a href="#" style="color:#111111;text-decoration:none;">Queensland Election Called for June 14: Labor Trails LNP on Four-Point Gap</a></h3>
      <p style="margin:0;font-size:14px;font-family:Arial,sans-serif;color:#444444;line-height:1.6;">Premier Miles called the election six months early, framing it as a referendum on Queensland's $28B clean energy transition. The LNP has pledged to pause the Pioneer-Burdekin pumped hydro project pending an independent review, creating uncertainty for the $8B in contracts already committed.</p>
    </div>

    <div style="padding:16px 0;border-bottom:1px solid #eeeeee;">
      <p style="margin:0 0 4px;font-size:11px;font-family:Arial,sans-serif;color:#888888;text-transform:uppercase;letter-spacing:.12em;">FINANCIAL REVIEW</p>
      <h3 style="margin:0 0 6px;font-size:17px;font-weight:700;line-height:1.4;font-family:Georgia,serif;"><a href="#" style="color:#111111;text-decoration:none;">Federal Budget to Include $6B Productivity Package Targeting SME Digital Adoption</a></h3>
      <p style="margin:0;font-size:14px;font-family:Arial,sans-serif;color:#444444;line-height:1.6;">Sources close to the Treasury say the May 12 budget will include accelerated depreciation for technology investments, expanded R&amp;D tax offsets for AI and automation tools, and a new SME digital transformation voucher program. The package is designed to address Australia's persistent productivity gap relative to the OECD average.</p>
    </div>

    <div style="padding:16px 0;border-bottom:1px solid #eeeeee;">
      <p style="margin:0 0 4px;font-size:11px;font-family:Arial,sans-serif;color:#888888;text-transform:uppercase;letter-spacing:.12em;">SMH</p>
      <h3 style="margin:0 0 6px;font-size:17px;font-weight:700;line-height:1.4;font-family:Georgia,serif;"><a href="#" style="color:#111111;text-decoration:none;">Atlassian Reports 28% Revenue Growth; Opens New Sydney AI Research Hub</a></h3>
      <p style="margin:0;font-size:14px;font-family:Arial,sans-serif;color:#444444;line-height:1.6;">The Australian software giant posted Q3 revenue of US$1.42B, up 28% year-on-year, driven by strong Jira Service Management and Confluence AI feature adoption. Atlassian simultaneously announced a new 200-person AI research centre in Sydney's Tech Central precinct, its largest R&amp;D investment in Australia to date.</p>
    </div>
  </td></tr>

  <tr><td style="padding:24px 40px 32px;background:#ffffff;border-top:2px solid #111111;">
    <table width="100%" cellpadding="0" cellspacing="0">
      <tr>
        <td style="font-size:12px;font-family:Arial,sans-serif;color:#888888;">Your daily AI-powered business briefing</td>
        <td align="right">
          <a href="https://theoperatingbrief.com" style="font-size:11px;font-family:Arial,sans-serif;color:#111111;text-decoration:none;border-bottom:1px solid #111111;margin-right:16px;">Subscribe</a>
          <a href="https://theoperatingbrief.com/unsubscribe" style="font-size:11px;font-family:Arial,sans-serif;color:#888888;text-decoration:none;border-bottom:1px solid #cccccc;">Unsubscribe</a>
        </td>
      </tr>
    </table>
  </td></tr>

</table></td></tr></table>
</body></html>"""


EDITIONS = [
    {
        "slug": "2026-04-14",
        "subject": "The Operating Brief – April 14, 2026",
        "sent_at": "2026-04-14T21:00:00Z",
        "preview_text": "Meta's Llama 4 drops. RBA holds rates. Oil slides on demand fears.",
        "html": EDITION_1_HTML,
        "published": True,
    },
    {
        "slug": "2026-04-17",
        "subject": "The Operating Brief – April 17, 2026",
        "sent_at": "2026-04-17T21:00:00Z",
        "preview_text": "OpenAI launches GPT-4.5 Turbo. ASX hits record high. Trump tariff pause extended.",
        "html": EDITION_2_HTML,
        "published": True,
    },
    {
        "slug": "2026-04-23",
        "subject": "The Operating Brief – April 23, 2026",
        "sent_at": "2026-04-23T21:00:00Z",
        "preview_text": "Apple unveils AI-native MacBook. Qantas announces 40 new routes. IMF cuts global growth forecast.",
        "html": EDITION_3_HTML,
        "published": True,
    },
    {
        "slug": "2026-04-29",
        "subject": "The Operating Brief – April 29, 2026",
        "sent_at": "2026-04-29T21:00:00Z",
        "preview_text": "Google DeepMind beats protein folding record. Queensland election called. USD hits 5-year high.",
        "html": EDITION_4_HTML,
        "published": True,
    },
]


def main():
    sb = get_supabase()
    print(f"Inserting {len(EDITIONS)} editions into Supabase...")
    for edition in EDITIONS:
        print(f"  Upserting {edition['slug']}...")
        result = sb.table("editions").upsert(edition).execute()
        print(f"    Done: {edition['slug']}")
    print("All editions inserted successfully.")


if __name__ == "__main__":
    main()
