# Patchbeast design system: "launch control"

Package: `packages/design-system` (`@patchbeast/design-system`). Tailwind + CSS-variable tokens, Radix primitives
(shadcn-style: the code is in the package, not a black-box library), Storybook for every component.
Run `npm run storybook` (port 6006) or `npm run build-storybook`.

Direction: a dark, high-contrast mission console for people watching a countdown. Original identity only: no
publisher branding, no neon-sunset palettes, no game artwork. The wordmark and the three-claw `BeastMark` are original SVG.

## Tokens (`src/styles/tokens.css`)

| Token | Dark | Purpose |
|---|---|---|
| `--pb-bg` | `#0B0D10` | page background |
| `--pb-surface-1/2/3` | `#12151A / #181C23 / #20252E` | layered surfaces |
| `--pb-text`, `--pb-text-muted` | `#ECEEF2`, `#9AA3B2` | text |
| `--pb-accent` | `#7C5CFF` (ultraviolet) | the single signature accent (rings, glow, marks) |
| `--pb-accent-strong` / `--pb-accent-text` | `#6846EE` / `#A896FF` | AA-safe button background / accent text |
| `--pb-confirmed` | `#2EE59D` | **only** for Confirmed |
| `--pb-reported` | `#FFB020` | **only** for Reported |
| `--pb-rumour` | `#8A93A6` | **only** for Rumour/Unverified |
| `--pb-alert` | `#FF5A5F` | **only** for alerts/errors |

Radius, elevation, motion (`--pb-ease`, `--pb-dur*`) are defined once. Light theme is an opt-in toggle
(`[data-theme="light"]`, persisted in `localStorage`, applied before paint by `themeInitScript`).
`tests/tokens.test.ts` computes WCAG contrast for every text/surface pair in both themes (>= 4.5:1) and the
focus ring (>= 3:1); CI fails if a token edit breaks AA.

## Type
Display **Space Grotesk**, body **Inter**, data/countdown **JetBrains Mono** (self-hosted woff2 in `fonts/`, loaded with
`next/font/local`: swap + size-adjusted fallback, no layout shift, no request to a third party).

## Signature components

* **Countdown**: large mono digits, the seconds digit "ticks" (CSS only, off for reduced motion), `role="timer"` text alternative that updates per minute, and **freezes honestly to "Date unconfirmed"** unless the API says `countdown_mode = live` (a date exists, is Reported/Confirmed and is not a placeholder).
* **SignalMeter**: 3-bar confidence meter (Confirmed 3 / Reported 2 / Rumour 1 bars) with a text label and source count; colour is never the only signal. `ExplainedSignalMeter` adds a keyboard-accessible Radix tooltip.
* **ChangeLog**: "patch log" timeline: version chips, `old → new` diffs, `SourceChip`, `SignalMeter`.
* **StatusTicker**: slim top ticker of *confirmed* changes; pauses on hover/focus; static + scrollable under `prefers-reduced-motion`.
* **SourceChip** (every item attributes its source), **HardwareCard** (affiliate; disclosure is built in and not removable), **AdSlot** (renders nothing unless enabled; when enabled reserves its height so there is no CLS), **SpecCompare** (min vs recommended; "Not published" instead of guesses).
* Primitives: `Button` (Radix Slot), `Card`, `Section`, `ThemeToggle`, `Wordmark`/`BeastMark`.

## Motion
Purposeful, light, CSS-only (no animation library). Everything animated is disabled by `prefers-reduced-motion`.

## Budgets
LCP < 2.5 s, CLS < 0.1, JS on the game hub < ~170 KB (first load currently ~141 KB). Hero is text-only; videos are click-to-load
(`youtube-nocookie`); no `next/image` optimisation cost on a small VPS; fonts preloaded.

## Accessibility
Skip link, semantic landmarks and headings, visible focus ring on every interactive element, `aria-label`s on meters/tickers,
tables with captions and scoped headers, `aria-live` regions for tool output. Storybook runs `addon-a11y` (`test: "error"`).

## Content rules (UI)
Every item shows its source and verification status. No fake urgency, no clickbait. Signal colours are reserved for meaning.

## Adding a component
Create `src/components/X.tsx` (no Next imports; accept links via props), export it from `src/index.ts`, add a story, use only token-based
Tailwind classes. Prefer server-safe components; add `"use client"` only when state/effects are required.
