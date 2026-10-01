# Atmos Weather Lab Design Specification

## Product surface
Operational weather dashboard used as the application payload for a CI/CD and GitOps learning lab.

## Audience
Engineers learning application delivery. The interface should feel credible enough to make deployment verification visually obvious without adding framework complexity.

## Composition
- Compact top command bar with product identity, source status, and version.
- Search/action rail directly below the header.
- Main current-conditions panel with a restrained animated atmospheric visualization.
- Flash Report strip for derived condition summaries. It is explicitly not an official alert feed.
- Metric rail for humidity, wind, gusts, pressure, cloud cover, precipitation probability, and UV.
- Eight-hour forecast timeline and today/next-day summaries.

## Typography
- Primary: Manrope, loaded from Google Fonts when available.
- Numeric/operational: IBM Plex Mono, loaded from Google Fonts when available.
- Durable fallbacks: Avenir Next, Segoe UI, sans-serif.

## Color system
- Canvas: #061119
- Surface: #0b1821 / #10232d
- Text: #ecf8f4
- Muted text: #96aeb5
- Aqua signal: #72e0c4
- Sky signal: #78b9ff
- Warm signal: #f2c46d
- Risk signal: #ff8a7a

The palette is atmospheric and functional. Gradients are limited to environmental lighting and the animated weather orb.

## Shape and spacing
- 8px spacing unit.
- 14-20px corner radii for major panels.
- Small badges use 999px radius only where the pill form conveys status.
- Dense enough for a dashboard, not a marketing landing page.

## Motion
- Ambient grid drift, weather orb breathing, report entrance, and loading shimmer.
- No animation is required to understand content.
- `prefers-reduced-motion: reduce` disables nonessential motion.

## Accessibility
- Keyboard-visible focus states.
- High-contrast text against dark surfaces.
- ARIA live region for request status.
- Buttons have explicit labels.
- Responsive layout collapses to one column below 860px.

## Content integrity
All weather values come from live Open-Meteo responses. Flash Reports are deterministic summaries derived from those values and are labeled as such. No fabricated reviews, statistics, alerts, or location data are displayed.
