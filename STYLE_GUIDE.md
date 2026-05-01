# The Operating Brief — Style Guide

## Overview
Editorial aesthetic. Think FT, Economist, NYT. No gradients, no coloured backgrounds, no shadows. Black ink on white paper — structured by ruled lines and typography, not colour.

---

## Colours

| Token | Hex | Usage |
|---|---|---|
| `ink` | `#111111` | Headlines, ruled lines, borders |
| `body` | `#222222` | Body copy |
| `secondary` | `#444444` | Article summaries |
| `muted` | `#888888` | Labels, datelines, metadata |
| `rule` | `#dddddd` | Thin dividers between sections |
| `page` | `#f5f4f0` | Page/email outer background |
| `card` | `#ffffff` | Content card background |

**No other colours.** No blues, no ambers, no greens, no reds.

---

## Typography

| Element | Font | Size | Weight | Style |
|---|---|---|---|---|
| Masthead / H1 | Georgia, serif | 40px | 700 | Normal |
| Section H2 | Arial, sans-serif | 14px | 700 | Uppercase, letter-spacing 0.08em |
| Article title | Georgia, serif | 17px | 700 | Normal |
| Briefing body | Georgia, serif | 16px | 400 | Line-height 1.75 |
| Article summary | Arial, sans-serif | 14px | 400 | Line-height 1.6 |
| Labels / dateline | Arial, sans-serif | 11px | 400 | Uppercase, letter-spacing 0.12–0.15em, color `#888` |
| Footer | Arial, sans-serif | 12px | 400 | color `#888` |

---

## Layout

- Max content width: **620px**
- Outer padding: **40px top/bottom, 16px sides**
- Inner padding: **48px left/right**
- No border-radius on the card (flat edges)
- No box-shadow

---

## Rules & Dividers

- **Masthead bottom border**: `3px solid #111` — the single heaviest rule, defines the header
- **Footer top border**: `2px solid #111`
- **Section dividers**: `1px solid #ddd`
- **Article row dividers**: `1px solid #eee`
- **Section H2 left accent**: `border-left: 3px solid #111; padding-left: 10px`
- **Briefing H3 left accent**: `border-left: 3px solid #111; padding-left: 10px`

---

## Header

```
[dateline — e.g. "Friday, May 1 2026"]   ← 11px uppercase Arial #888
The Operating Brief                       ← 40px Georgia bold #111
For Australian business operators         ← 13px Arial #555
──────────────────────────────────────── ← 3px solid #111
```

No background colour. White card, black type, single heavy rule underneath.

---

## Section Structure

Each section follows this pattern:

```
SECTION LABEL    ← 11px uppercase Arial #888, letter-spacing .12em
                    e.g. "AI STORIES", "WORLD NEWS", "AUSTRALIAN NEWS"

SECTION HEADING  ← 14px uppercase Arial bold #111, border-left 3px solid #111
e.g. "AI OVERVIEW" / "GLOBAL SNAPSHOT" / "AUSTRALIA SNAPSHOT"

Overview paragraph ← 16px Georgia #222, line-height 1.75

──────────────────  ← 1px solid #eee (between articles)

SOURCE · TAG        ← 11px uppercase Arial #888
Article Title       ← 17px Georgia bold #111
Summary copy        ← 14px Arial #444, line-height 1.6

──────────────────
...repeat...
```

---

## Briefing Section

The top briefing uses **four H3 subheadings**:
- AI & Technology
- Australian Business & Finance
- World Markets & Global Business
- The Big Picture

Each H3: `14px uppercase Arial bold #111`, `border-left: 3px solid #111`, `padding-left: 10px`
Body under each: `16px Georgia #222`, line-height 1.75

---

## Footer

```
──────────────────────────────────────── ← 2px solid #111
Your daily AI-powered business briefing  [Subscribe]  [Unsubscribe]
```

- Left: 12px Arial `#888`
- Right: `Subscribe` — 11px Arial `#111`, underlined with `border-bottom: 1px solid #111`
- Right: `Unsubscribe` — 11px Arial `#888`, underlined with `border-bottom: 1px solid #ccc`

---

## Email Sender

- **From**: The Operating Brief `<brief@theoperatingbrief.com>`
- **Reply-to**: `hello@theoperatingbrief.com`
- **Subject**: `The Operating Brief – May 1, 2026`

---

## What This Is Not

- ❌ No navy/dark header backgrounds
- ❌ No amber, gold, lime, coral or any accent colour
- ❌ No coloured left-border accents (only black `#111`)
- ❌ No coloured overview boxes / tinted backgrounds
- ❌ No rounded corners
- ❌ No emoji in headings
- ❌ No gradients or shadows
- ❌ No "Daily" badge / pill components
