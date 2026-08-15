---
version: alpha
name: Hermes Ops — Exception First
description: Editorial operations dashboard that prioritizes exceptions, recovery, and next actions while preserving the public-safe Hermes telemetry boundary.
colors:
  background: "#EEF1EC"
  primary: "#13201C"
  secondary: "#B83D29"
  accent: "#196448"
  neutral: "#FFFDF7"
  muted: "#46514C"
  line: "#C1C7C0"
  warm: "#EAD2B4"
typography:
  display:
    fontFamily: "Avenir Next, Pretendard Variable, Apple SD Gothic Neo, system-ui, sans-serif"
    fontSize: "9rem"
    fontWeight: 900
    lineHeight: "0.72"
    letterSpacing: "-0.08em"
  headline:
    fontFamily: "Avenir Next, Apple SD Gothic Neo, system-ui, sans-serif"
    fontSize: "2.5rem"
    fontWeight: 800
    lineHeight: "1.0"
    letterSpacing: "-0.05em"
  body:
    fontFamily: "Avenir Next, Apple SD Gothic Neo, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 450
    lineHeight: "1.55"
    letterSpacing: "-0.01em"
  label:
    fontFamily: "SF Mono, ui-monospace, monospace"
    fontSize: "0.6875rem"
    fontWeight: 750
    lineHeight: "1.2"
    letterSpacing: "0.13em"
rounded:
  none: "0px"
  subtle: "2px"
  pill: "999px"
spacing:
  none: "0px"
  xs: "6px"
  sm: "10px"
  md: "16px"
  lg: "24px"
  xl: "38px"
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
  navigation:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.neutral}"
    typography: "{typography.label}"
    rounded: "{rounded.subtle}"
    padding: "{spacing.sm}"
    size: "compact"
    height: "56px"
    width: "224px"
  statusCritical:
    backgroundColor: "{colors.secondary}"
    textColor: "{colors.neutral}"
    typography: "{typography.headline}"
    rounded: "{rounded.none}"
    padding: "{spacing.md}"
    size: "prominent"
    height: "auto"
    width: "100%"
  panel:
    backgroundColor: "{colors.neutral}"
    textColor: "{colors.primary}"
    typography: "{typography.body}"
    rounded: "{rounded.none}"
    padding: "{spacing.md}"
    size: "dense"
    height: "auto"
    width: "100%"
  stateOk:
    backgroundColor: "{colors.neutral}"
    textColor: "{colors.accent}"
    typography: "{typography.label}"
    rounded: "{rounded.subtle}"
    padding: "{spacing.xs}"
    size: "compact"
    height: "auto"
    width: "fit-content"
  supportingText:
    backgroundColor: "{colors.neutral}"
    textColor: "{colors.muted}"
    typography: "{typography.body}"
    rounded: "{rounded.none}"
    padding: "{spacing.none}"
    size: "secondary"
    height: "auto"
    width: "100%"
  divider:
    backgroundColor: "{colors.line}"
    textColor: "{colors.primary}"
    rounded: "{rounded.none}"
    padding: "{spacing.none}"
    size: "hairline"
    height: "1px"
    width: "100%"
  scoreBlock:
    backgroundColor: "{colors.warm}"
    textColor: "{colors.primary}"
    typography: "{typography.headline}"
    rounded: "{rounded.none}"
    padding: "{spacing.lg}"
    size: "prominent"
    height: "auto"
    width: "100%"
---

## Overview

`Exception First` is the selected production direction. The page acts as an operational decision surface rather than a brand poster: what needs attention, what changed, and what recovers next should be understood before the operator reads system detail.

The production source is `generate_dashboard.py` plus `exception_first_theme.py`. The public-data contract remains unchanged. Only aggregated job status, counts, sanitized error buckets, and public-safe timestamps are rendered. Local home paths, transcript content, task titles, source note names, secrets, and evidence snippets remain forbidden.

## Colors

- **Paper (`#EEF1EC`)** reduces the visual fatigue of the current textured dark canvas.
- **Ink (`#13201C`)** carries primary text and the fixed mission/navigation surfaces.
- **Action red (`#B83D29`)** is used once, for real attention or the page's action horizon and passes WCAG AA with white text.
- **Operational green (`#196448`)** marks healthy state and score continuity.
- **Warm (`#EAD2B4`)** supports the main score without looking like another generic card.

## Typography

The display face is deliberately oversized and compressed, but only in the hero. Operational labels use monospace. Korean body copy remains in a system-readable sans stack. KPI values are large; long detail text stays at normal body scale.

## Layout

Desktop uses a dark 270px mission column and an editorial canvas. A compact floating navigation dock keeps section access available without adding a second full sidebar. The content order is:

1. Current state and score.
2. Six telemetry facts.
3. Attention and sanitized logs.
4. Trend/benchmark context.
5. Full cron recovery board.
6. Recording, tasks, agents, and People Team detail.

Mobile collapses to one column, pins navigation at the top of the viewport, and keeps the attention state before detail tables without obscuring content.

## Elevation & Depth

Depth comes from contrast and rules, not soft shadows. Panels are flat paper surfaces with one-pixel borders. The action and benchmark panels use a restrained two-pixel top rule. No grain, glow, or glass effects.

## Shapes

Rectangles are mostly square. Two-pixel corners are reserved for compact controls and state labels. Pills are allowed only for existing state chips. This prevents the repeated rounded-card language of the production design.

## Components

- **Mission column:** identity, public-safe statement, generated time, version, and active cron count.
- **Status block:** score, health label, success/error context.
- **Telemetry strip:** six small facts, with Attention receiving the only filled action color.
- **Exception panel:** sanitized log buckets and attention count.
- **Cron board:** existing public-safe rows, no hidden job content added.

## Do's and Don'ts

### Do

- Put actionable exceptions before descriptive system detail.
- Preserve every existing public-safe metric and table row.
- Keep local paths out of generated PoC HTML.
- Maintain keyboard focus and reduced-motion support.
- Keep production `index.html` and `generate_dashboard.py` untouched until a direction is selected.

### Don't

- Do not use motion to simulate liveness.
- Do not convert every metric into a card.
- Do not use red for healthy or neutral data.
- Do not add raw logs, task titles, filenames, transcript content, or secrets.
- Do not commit a design direction to production before desktop/mobile comparison and data parity checks.
