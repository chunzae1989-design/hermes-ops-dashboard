---
version: alpha
name: Hermes Ops Dashboard — Teal Command Center
description: Public GitHub Pages design spec for a Hermes Agent operations dashboard that borrows the official Hermes Web Dashboard lens system while making a stronger departure from the old GitHub-dark card grid through an editorial command-center layout, fixed rail navigation, dense modules, terminal motifs, grain, grid, and warm glow.
colors:
  background: "#041C1C"
  primary: "#FFE6CB"
  secondary: "#FFBD38"
  accent: "#34D399"
  info: "#6EE7F9"
  danger: "#FB7185"
  purple: "#C4B5FD"
  terminal: "#020808"
  card: "#102928"
  cardStrong: "#203734"
  rail: "#0A2222"
  border: "#35514D"
typography:
  display:
    fontFamily: "Arial Narrow, Apple SD Gothic Neo, Malgun Gothic, system-ui, sans-serif"
    fontSize: "96px"
    fontWeight: 900
    lineHeight: "0.82"
    letterSpacing: "-0.085em"
  headline:
    fontFamily: "system-ui, -apple-system, Apple SD Gothic Neo, Malgun Gothic, Segoe UI, sans-serif"
    fontSize: "44px"
    fontWeight: 850
    lineHeight: "0.95"
    letterSpacing: "-0.06em"
  body:
    fontFamily: "system-ui, -apple-system, Apple SD Gothic Neo, Malgun Gothic, Segoe UI, sans-serif"
    fontSize: "15px"
    fontWeight: 450
    lineHeight: "1.55"
    letterSpacing: "-0.01em"
  label:
    fontFamily: "ui-monospace, SF Mono, JetBrains Mono, Menlo, Consolas, monospace"
    fontSize: "11px"
    fontWeight: 700
    lineHeight: "1.2"
    letterSpacing: "0.16em"
  mono:
    fontFamily: "ui-monospace, SF Mono, JetBrains Mono, Menlo, Consolas, monospace"
    fontSize: "12px"
    fontWeight: 500
    lineHeight: "1.45"
    letterSpacing: "-0.01em"
rounded:
  none: "0px"
  small: "8px"
  medium: "14px"
  large: "22px"
  xlarge: "34px"
  pill: "999px"
spacing:
  none: "0px"
  unit: "4px"
  xs: "6px"
  sm: "10px"
  md: "16px"
  lg: "24px"
  xl: "36px"
  xxl: "56px"
  railWidth: "88px"
  sidebarWidth: "292px"
  contentMaxWidth: "1480px"
components:
  canvas:
    backgroundColor: "{colors.background}"
    textColor: "{colors.primary}"
    typography: "{typography.body}"
    rounded: "{rounded.none}"
    padding: "{spacing.none}"
    size: "full"
    height: "100vh"
    width: "100%"
  rail:
    backgroundColor: "{colors.rail}"
    textColor: "{colors.primary}"
    typography: "{typography.label}"
    rounded: "{rounded.none}"
    padding: "{spacing.md}"
    size: "fixed"
    height: "100vh"
    width: "{spacing.railWidth}"
  sidebar:
    backgroundColor: "{colors.card}"
    textColor: "{colors.primary}"
    typography: "{typography.body}"
    rounded: "{rounded.large}"
    padding: "{spacing.lg}"
    size: "fixed"
    height: "calc(100vh - 32px)"
    width: "{spacing.sidebarWidth}"
  hero:
    backgroundColor: "{colors.cardStrong}"
    textColor: "{colors.primary}"
    typography: "{typography.display}"
    rounded: "{rounded.xlarge}"
    padding: "{spacing.xl}"
    size: "wide"
    height: "300px"
    width: "100%"
  module:
    backgroundColor: "{colors.card}"
    textColor: "{colors.primary}"
    typography: "{typography.body}"
    rounded: "{rounded.large}"
    padding: "{spacing.md}"
    size: "dense"
    height: "auto"
    width: "100%"
  metric:
    backgroundColor: "{colors.terminal}"
    textColor: "{colors.primary}"
    typography: "{typography.headline}"
    rounded: "{rounded.medium}"
    padding: "{spacing.md}"
    size: "compact"
    height: "auto"
    width: "100%"
  badge:
    backgroundColor: "{colors.cardStrong}"
    textColor: "{colors.primary}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "{spacing.xs}"
    size: "compact"
    height: "auto"
    width: "fit-content"
  terminalPanel:
    backgroundColor: "{colors.terminal}"
    textColor: "{colors.accent}"
    typography: "{typography.mono}"
    rounded: "{rounded.medium}"
    padding: "{spacing.md}"
    size: "dense"
    height: "auto"
    width: "100%"
  table:
    backgroundColor: "{colors.card}"
    textColor: "{colors.primary}"
    typography: "{typography.mono}"
    rounded: "{rounded.medium}"
    padding: "{spacing.sm}"
    size: "dense"
    height: "auto"
    width: "100%"
  actionButton:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.background}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "{spacing.sm}"
    size: "compact"
    height: "auto"
    width: "fit-content"
---

## Overview

This dashboard should feel like a **public-safe Hermes operations command center**, not another GitHub-dark status grid. The official Hermes Web Dashboard establishes the canonical visual DNA:

- **Hermes Teal lens:** deep teal canvas `#041C1C`, cream midground `#FFE6CB`, warm glow `#FFBD38`.
- **Backdrop stack:** fixed dark base, low-opacity filler texture, warm top-left vignette, optional inversion layer, and noise grain above the UI.
- **Dashboard language:** dense admin modules, live status, logs, cron, analytics, sessions, system operations, terminal/chat motifs.
- **Typography mix:** large display moments, readable system UI text, and monospace data/log readouts.

For the user’s GitHub Pages Hermes Ops Dashboard, keep the Hermes palette but change the composition:

- Move from a conventional left-sidebar + equal card grid into a **rail + cockpit + editorial hero** structure.
- Use a **massive command-center headline** and compact data bands.
- Make modules feel more like **instrument panels, terminals, gauges, and dispatch boards** than generic cards.
- Preserve strict public-safety: expose only aggregate operational metrics and statuses, never private meeting/call filenames, transcript content, source note names, quotes, evidence snippets, or raw personal task titles.

The design direction is: **“Hermes Teal editorial cockpit for public operations telemetry.”**

## Colors

Use the official Hermes default theme as the base, then increase contrast through layering, glow, grid, and terminal surfaces.

- **Canvas / page base — `#041C1C`:** dominates the page. Use as full-viewport background. Add subtle radial glow and texture, not flat black.
- **Primary text / cream midground — `#FFE6CB`:** primary copy, titles, important numbers. This is the Hermes visual anchor.
- **Warm glow — `#FFBD38`:** attention, hero vignette, active focus rings, “needs attention” badges. Atmospheric rather than alarmist.
- **Success / agent-ready — `#34D399`:** healthy cron, ready specialists, connected states, positive deltas.
- **Info / telemetry cyan — `#6EE7F9`:** links, live indicators, graph highlights, scan lines. Use sparingly.
- **Danger / error — `#FB7185`:** only for real errors or failed jobs.
- **Terminal surface — `#020808`:** log panels, command captions, dense metrics.

Background treatment should layer radial glows over the teal canvas:

```css
background:
  radial-gradient(circle at 0% 0%, rgba(255, 189, 56, 0.16), transparent 34%),
  radial-gradient(circle at 85% 12%, rgba(52, 211, 153, 0.12), transparent 30%),
  radial-gradient(circle at 50% 115%, rgba(110, 231, 249, 0.08), transparent 38%),
  #041C1C;
```

Add two global overlays:

- **Grid:** cream 1px grid at 40–56px spacing, opacity 0.05–0.09.
- **Grain/noise:** very subtle, opacity 0.08–0.16, never enough to reduce readability.

## Typography

Typography should create the strongest departure from the old design.

- Use **oversized editorial display typography** for the hero: huge, compressed, tight line-height, strong negative letter spacing.
- Use **system sans** for Korean/English readability: `system-ui, -apple-system, Apple SD Gothic Neo, Malgun Gothic, Segoe UI, sans-serif`.
- Use **monospace** for operational data: `ui-monospace, SF Mono, JetBrains Mono, Menlo, Consolas, monospace`.
- Labels should be compact, uppercase when English, and feel like cockpit readouts: `11px`, `0.16em` tracking, `700` weight.
- KPI values should use big numerical typography with tight tracking. Avoid old “simple card number” treatment by pairing numbers with gauge bars, scan labels, terminal captions, or inline deltas.
- Korean copy should be concise and dashboard-native: `활성 자동화`, `주의 신호`, `공개 안전`, `Task 전환`, `녹음 파이프라인`.

## Layout

Use a **three-zone command center** instead of the current old-style card grid.

### 1. Fixed icon rail

A narrow left rail, about `88px` wide:

- Stays fixed on desktop.
- Contains compact Hermes mark, section glyphs, and status dot.
- Feels like a cockpit control strip.
- Should not contain long text.

Suggested rail items: `⌘ Overview`, `A Agents`, `● Recordings`, `↻ Cron`, `▣ Logs`, `◇ Public-safe`.

### 2. Secondary navigation / mission panel

A wider fixed/sticky panel, about `292px` wide:

- Sits next to the rail on desktop.
- Contains product title, generated timestamp, public-safety notice, and small live-status stack.
- Should look like a glassy command placard, not a typical sidebar.

### 3. Main cockpit canvas

Main content should use a dense, asymmetric 12-column layout:

- Hero: 8–12 columns.
- KPI ribbon: small, compressed modules.
- Agent panel: 5–7 columns.
- Cron board: full-width or 8 columns.
- Terminal/log panel: 4–6 columns.
- Avoid too many same-size cards.

Recommended page order:

1. Command hero with huge `OPS / HERMES`, current state badge, and `public_safe=true` command caption.
2. Telemetry ribbon: active cron, failed cron, recent notes, task candidates, ROI hours, AI Ops score.
3. Benchmark cockpit: score spark bars, conversion gauge, reliability, portfolio summary, ROI.
4. Agent dispatch board: 헤르미온느 → 아기 · 디지.
5. Public-safe recording pipeline.
6. Cron operations board.
7. Sanitized logs.

Mobile layout collapses rail and mission panel into a horizontal cockpit bar, keeps the hero oversized but unclipped, and stacks modules in the same semantic order.

## Elevation & Depth

Depth should come from the Hermes backdrop model, not generic shadows.

Use these layers:

1. **Base canvas:** solid Hermes teal `#041C1C`.
2. **Backdrop texture:** low-opacity grid, subtle grain, optional faint filler texture inspired by the official Hermes backdrop.
3. **Warm glow:** radial glow from top-left or hero corner using `#FFBD38`; keep opacity around `0.18–0.28`.
4. **Panels:** semi-transparent cream-mixed surfaces. Borders should define panels more than shadows.
5. **Terminal insets:** darker `#020808`, inner border, faint scanline/grid, monospace green/cream text.

Allowed shadow values:

```css
box-shadow: 0 24px 80px rgba(0, 0, 0, 0.28);
box-shadow: 0 12px 36px rgba(0, 0, 0, 0.22);
```

Avoid glossy SaaS gradients that feel unrelated to Hermes. The atmosphere should be technical, dark, tactile, and editorial.

## Shapes

Use rounded geometry, but make the system sharper and more cockpit-like than the current version.

- Page/canvas: square, full viewport.
- Fixed rail: square outside edge; subtle internal rounding optional.
- Mission panel: `22px` radius.
- Hero: `34px` radius.
- Dense modules: `18–22px` radius.
- Terminal/log panels: `14px` radius.
- Badges/pills: `999px`.
- Small code tokens: `7–8px`.

Add visual distinction through notched corners, thin top highlight lines, grid-aligned module boundaries, and small corner coordinates like `01`, `02`, `OPS`, `SAFE`, `LIVE`.

Do not rely only on rounded cards; that is what made the redesign feel too close to the old version.

## Components

### Canvas

Full viewport Hermes teal base. Includes radial glow, grid, and grain. Use `isolation: isolate` so blend effects remain controlled.

### Fixed rail

Narrow icon-first navigation. Active state uses cream background or warm dot. Include a persistent small status LED: green for healthy, warm for attention, red for failed.

### Mission panel

Shows identity and safety posture. Include a clear public-safe statement:

`GitHub Pages에는 회의/통화 원문·파일명·인용문 없이 운영 지표만 표시.`

Use compact stacked metadata, not large paragraphs. Generated time should use monospace.

### Hero

The main departure point. Title should be oversized and editorial: `OPS`, `HERMES`, or `OPS / HERMES`. Include command-line subcaption:

`public_safe=true · source=aggregated_metrics · private_content=redacted`

Use asymmetry: text on left, telemetry stack or circular score on right.

### KPI ribbon

Dense horizontal band of small instrument tiles. Each KPI includes label, big value, unit/pill, and tiny context line or delta. Avoid plain four-card layout.

### Metric module

Use for AI Ops score, ROI hours, conversion rate. Include a sparkline, mini bars, or gauge. Prefer blocky terminal-inspired visuals over generic charts.

### Agent dispatch board

Shows `헤르미온느`, `아기`, and `디지` availability, role, route count, and operating rule. Do not expose internal prompt text. Visual form should be a route diagram or dispatch matrix.

### Recording pipeline module

Allowed: counts, last run time, cache size, success/failure state, candidate counts by source type. Forbidden: file names, transcript names, meeting titles, call participants, quotes, evidence snippets, raw source note paths.

### Cron operations board

Dense dispatch board with status LED, job category/name, short ID, last result, and next run. Consider grouping jobs into `Insights`, `Recordings`, `Finance`, `Maintenance`, `Dashboard`.

### Terminal/log panel

Use dark terminal background. Prefer sanitized summaries (`errors_7d=10`, `timeouts=4`, `gateway_warnings=1`) over raw lines. If showing lines, sanitize aggressively. Header: `SANITIZED LOG STREAM`.

### Badges and pills

Pill shape, monospace label typography, state color: OK green, attention warm, error red, neutral cream tint.

### Tables

Compact rows, thin borders, sticky header optional. Avoid default browser table look. On mobile, allow horizontal scrolling or transform rows into cards.

## Do's and Don'ts

### Do

- Use the official Hermes colors: `#041C1C`, `#FFE6CB`, `#FFBD38`.
- Use grain, grid, vignette, and subtle filler texture inspired by the official Hermes backdrop.
- Make the page feel like a public command center, not a private admin dump.
- Use oversized editorial display type in the hero.
- Use a fixed rail or cockpit navigation on desktop.
- Use dense, asymmetric modules.
- Use terminal and agent motifs: command captions, route diagrams, status LEDs, monospace logs.
- Keep metrics public-safe and aggregated.
- Redact or omit private source material before rendering.
- Prefer operational categories and counts over raw personal content.
- Keep Korean labels concise and dashboard-native.

### Don't

- Do not return to a generic GitHub-dark card grid.
- Do not use evenly sized cards everywhere.
- Do not make the sidebar the dominant visual pattern.
- Do not use black/gray as the main palette when Hermes teal should own the canvas.
- Do not expose meeting/call filenames, transcript content, note names, source paths, personal task titles, quotes, or evidence snippets.
- Do not paste raw logs without sanitization.
- Do not show secrets, API keys, env values, local private paths, or credential previews.
- Do not overuse red; reserve it for true failures.
- Do not add heavy animations that hurt readability on a static GitHub Pages dashboard.
- Do not rely on external private assets; the page should work as a self-contained public artifact.
