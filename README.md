# The Operating Brief

The Operating Brief is an AI-assisted editorial newsletter system for Australian operators. It combines Python digest generators, a Supabase-backed subscriber/archive database, Resend email delivery, and a Next.js public/admin website.

The product language and visual system are deliberately restrained: editorial, black ink on white paper, closer to the FT/Economist/NYT than a SaaS landing page. See `STYLE_GUIDE.md` before changing email or site presentation.

## What Has Been Built

This repo currently supports a small suite of briefings:

| Brief | Audience | Cadence | Public surface | Generator |
| --- | --- | --- | --- | --- |
| The Operating Brief | Australian business operators | Weekday mornings before 7am | `/`, `/archive` | `daily_digest.py` |
| The Markets Brief | Australian investors/operators watching the ASX | Weekday mornings before ASX open | `/markets`, `/markets/archive` | `markets_digest.py` |
| The Sporting Brief | Australian sports readers | Weekend/round wrap | `/sporting`, `/sporting/archive` | `sports_digest.py` |
| The Paddock Brief | Australian producers, agronomists, rural advisors | Weekly/agriculture-focused | Admin/backend currently; no main public nav page yet | `paddock_digest.py` |
| Budget Brief | Special-purpose budget edition | On demand | No dedicated public surface | `budget_brief.py` |

The system can:

- Fetch RSS/news feeds and market/sports data.
- Deduplicate stories by title similarity and, for the main brief, against recently sent links/topics.
- Ask Claude to produce structured editorial output.
- Render responsive HTML email in the house style.
- Save local previews for review.
- Generate social assets such as "The Number" cards and captions for the main/markets/sports briefs.
- Send approved previews to active subscribers via Resend.
- Save sent editions to Supabase archive tables.
- Expose public subscribe, unsubscribe, and archive pages through the Next.js app.
- Provide a local admin dashboard for preview/send operations.

## Repository Shape

### Python generators

- `daily_digest.py` - main Operating Brief. Pulls AI, business, world, Australian, podcast, and Monday big-tech feeds. Generates the email, PDF, social captions, LinkedIn copy, and "The Number" card.
- `markets_digest.py` - Markets Brief. Pulls ASX/macro/global/commodity feeds, uses `yfinance` for market data and ASX movers, writes `markets_number.json` for possible combined social copy.
- `sports_digest.py` - Sporting Brief. Pulls sport feeds, ESPN scoreboards, supports daily ingest into `sports_daily_summaries`, then weekend-style preview/send.
- `paddock_digest.py` - Paddock Brief. Pulls Australian agriculture, commodity, global, weather, agtech, and policy feeds.
- `budget_brief.py` - special budget digest sent to the combined Operating Brief and Markets Brief subscriber lists.
- `backfill_editions.py` - historical Operating Brief archive backfill helper.
- `serve.py` - lightweight local static server, mainly for opening preview HTML from the admin dashboard.

### Website

The `website/` directory is a Next.js App Router app.

Important routes:

- `/` - Operating Brief subscribe page with referral handling.
- `/markets` - Markets Brief subscribe page.
- `/sporting` - Sporting Brief subscribe page.
- `/archive`, `/archive/[slug]` - Operating Brief archive.
- `/markets/archive`, `/markets/archive/[slug]` - Markets archive.
- `/sporting/archive`, `/sporting/archive/[slug]` - Sporting archive.
- `/unsubscribe`, `/markets/unsubscribe`, `/sporting/unsubscribe` - unsubscribe flows.
- `/admin` - password-protected local admin dashboard.
- `/preview/[token]` - token-protected Operating Brief draft approval/send surface.
- `/markets/preview/[token]` - token-protected Markets draft preview surface.

Important API routes:

- `/api/subscribe`, `/api/markets/subscribe`, `/api/sporting/subscribe` - subscriber creation/reactivation and welcome email.
- `/api/unsubscribe`, `/api/markets/unsubscribe`, `/api/sporting/unsubscribe` - token-based unsubscribe.
- `/api/admin/login` - sets the admin auth cookie.
- `/api/admin/subscribers` - returns active subscriber counts across the four brief families.
- `/api/admin/run` - streams Python generator output for preview/send jobs.
- `/api/preview/[token]/generate` - triggers the GitHub Action that generates an Operating Brief draft.
- `/api/preview/[token]/send` - sends the Supabase `draft` Operating Brief to active subscribers.

### Supporting docs/assets

- `STYLE_GUIDE.md` - canonical design direction for emails/site.
- `SOURCES.md` - canonical source list for the main Operating Brief feeds.
- `*_supabase_schema.sql` - table setup for Markets, Sporting, and Paddock.
- `the_operating_brief_logo.svg`, `the_operating_brief_banner.svg` - brand assets.
- `pdfs/`, `social_images/`, `preview_*.html`, `.sent_*.json` - generated local operating artifacts.

The untracked `operating-brief-local-files/` folder and zip appear to be local exported/generated artifacts. Treat them as operating history, not primary source code.

## Data Model

Supabase is the shared data layer.

Known table families:

- Operating Brief: `subscribers`, `editions`, `send_log` or equivalent existing production tables.
- Markets Brief: `markets_subscribers`, `markets_editions`, `markets_send_log`.
- Sporting Brief: `sports_subscribers`, `sports_editions`, `sports_send_log`, `sports_daily_summaries`.
- Paddock Brief: `paddock_subscribers`, `paddock_editions`, `paddock_send_log`.

Subscriber tables store email, token, active status, and created timestamp. The main Operating Brief subscriber flow also includes referral codes and referral counts.

Edition tables store slug, subject, preview text, rendered HTML, and timestamps. Public archive pages render saved HTML directly from Supabase.

## Environment

Copy `.env.example` to `.env` and fill in the real values.

Python scripts expect:

- `ANTHROPIC_API_KEY`
- `RESEND_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_KEY`
- optional sender/reply environment variables per brief
- optional `CLAUDE_MODEL`

The Next.js app expects:

- `NEXT_PUBLIC_SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `RESEND_API_KEY`
- `ADMIN_PASSWORD` or `PREVIEW_TOKEN` as the fallback admin secret when `ADMIN_PASSWORD` is not configured
- `PREVIEW_TOKEN`
- `GITHUB_PAT` for triggering the GitHub Action from the preview page

Be careful not to commit `.env`, `.env.local`, `.env.production`, generated sent logs, or local export bundles.

## Local Setup

Install Python dependencies:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

Install website dependencies:

```bash
cd website
npm install
```

Run the website:

```bash
cd website
npm run dev
```

Run the preview file server from the repo root when using the admin "Open preview" buttons for Markets, Sporting, and Paddock. The Operating Brief preview now opens on the website at `/preview/[token]`:

```bash
python3 serve.py
```

## Common Workflows

### Generate a preview

From the repo root:

```bash
. .venv/bin/activate
python3 daily_digest.py --preview
python3 markets_digest.py --preview
python3 sports_digest.py --preview
python3 paddock_digest.py --preview
```

Preview mode writes `preview_latest.html`, `preview_markets.html`, `preview_sports.html`, or `preview_paddock.html`. The Operating Brief and Markets previews also save a Supabase draft row with slug `draft` for web approval and hosted preview routes.

### Send an approved preview

From the repo root:

```bash
. .venv/bin/activate
python3 daily_digest.py --send
python3 markets_digest.py --send
python3 sports_digest.py --send
python3 paddock_digest.py --send
```

Send mode reads the last saved preview and sends exactly what was reviewed. It then archives the edition and logs the send.

### Use the admin dashboard

1. Run the Next.js dev server from `website/`.
2. Run `python3 serve.py` from the repo root if you want preview links to open locally.
3. Open `/admin`.
4. Sign in with `ADMIN_PASSWORD`.
5. Generate previews, inspect logs, open preview HTML, then send.

The `/api/admin/run` route invokes scripts from the project root with `.venv/bin/python`, so the virtualenv must exist at repo root.

### GitHub Action preview

`.github/workflows/generate-digest.yml` runs `python3 daily_digest.py --preview` on manual dispatch. The token-protected preview route can trigger this workflow when `GITHUB_PAT` is configured.

## Editorial Intent

This project is not a generic RSS summariser. It is an operator-facing editorial product.

Core principles:

- Australian context first.
- Practical implications over abstract summaries.
- Short, sharp prose with no filler.
- The main Operating Brief should read like a concise business news bulletin, not a podcast script or coffee-chat explainer.
- Use direct declarative sentences. Prefer "X announced Y", "X rose to Y", "X faces Z" over scene-setting, metaphors, rhetorical setup, or host-style commentary.
- Be assertive when the facts support it: report the fact, state the operator relevance, then move on.
- Do not show the synthesis machinery. Avoid openers such as "Two signals point in the same direction", "A clear pattern is emerging", "The message is clear", or "The broader story is". Open with the concrete company, policy, number, market move, or regulatory decision.
- Specific names, numbers, companies, regions, markets, and policies.
- No hype around AI, markets, sport tech, or agtech.
- The email is the product; the website supports subscription, archive, and operations.
- Visual design is ruled lines, typography, and restraint, not colour, gradients, cards, or decoration.
- Every story must earn its place for an Australian operator. The test is whether it affects revenue, costs, labour, regulation, technology adoption, capital allocation, supply chains, customers, risk, productivity, or strategic timing.
- Serious general-news stories should not be forced into the brief with vague business language. Avoid hand-waving phrases like "workforce implications", "operational risk", "insurance implications", or "supply chain gaps" unless the source clearly supports that angle.
- Avoid soft presenter phrases such as "watch this one", "the signal is clear", "the shape is familiar", "tells its own story", "set the tone", "pressure is building", "what matters now", or "worth keeping an eye on".

Australian story priority:

- Tier 1: RBA, rates, inflation, wages, employment, tax, budget, regulation, energy prices, housing policy, major ASX/company news, insolvencies, industrial relations, cyber/privacy law, migration/labour supply.
- Tier 2: infrastructure, large procurement, major court/regulatory decisions, logistics, agriculture, climate/weather with direct economic impact, education/skills.
- Tier 3: public health, local government disputes, isolated procurement criticism, crime, human-impact stories, culture-war politics. Use only when clearly relevant, and keep factual.
- Tier 4: no operator/economic consequence, or stories where the business angle requires hand-waving. Exclude unless exceptional.

AI and technology priority:

- Tier 1: model releases with practical capability changes, enterprise adoption/pricing, security vulnerabilities, regulation, major funding/M&A, platform shifts, tooling that changes developer/operator workflows.
- Tier 2: research with near-term product implications, open-source infrastructure, benchmarks that alter buying/build decisions, case studies with measurable productivity or cost outcomes.
- Tier 3: speculative opinion, generic AI hype/fear, consumer novelty features, demos without adoption, culture-war arguments about AI.
- Tier 4: academic minutiae, personality drama, vague futurism, or stories where the operator angle is only "AI is changing things".

World/global business priority:

- Tier 1: geopolitics affecting energy, shipping, trade, currency, commodities, sanctions, supply chains, major elections/policy shifts, central banks, major company/market shocks.
- Tier 2: regional conflict developments with economic exposure, disease/climate events with material supply-chain or commodity impact, major overseas legal/regulatory actions.
- Tier 3: humanitarian stories without clear Australian operator exposure, isolated violence, diplomatic rhetoric with no market or trade consequence.
- Tier 4: general world news where the implication is vague anxiety rather than a practical business signal.

The Big Picture should synthesize the strongest Tier 1/Tier 2 signals across sections. It should not rescue weak stories. It should leave the reader with one or two practical strategic implications, not a mood summary.

When adding a new brief or feature, preserve the existing pattern: source ingestion, Claude structured output, strict parsing, styled HTML render, preview-first review, then send/archive.

## Current Gaps And Context

- The root docs were previously missing; this README is now the project orientation point.
- `website/README.md` was default Next.js boilerplate and has been replaced with app-specific notes.
- `agent_prompt.md` appears to be an early manual workflow prompt and is not the canonical implementation anymore. The Python scripts are the source of truth for generation behavior.
- Paddock has generator/admin/database support, but no public subscribe/archive page in the same way Markets and Sporting do.
- `SOURCES.md` documents the main Operating Brief sources. Markets, Sporting, and Paddock sources currently live primarily inside their generator scripts.
