# Cursor Rules — 00 Non-regression (Highest priority)

These rules are NON-NEGOTIABLE and apply to all changes.

1) Do not rename or delete any selector that might be used by:
   - Jinja templates (*.html)
   - vanilla JS (querySelector, classList, toggles)
   - Leaflet classes (.leaflet-*, .marker-*, etc.)
   - data-* and aria-* attributes used as hooks

2) Do not change behavioral properties unless there is evidence:
   - display / position / z-index / overflow
   - hover / focus / active interactions, transitions/animations
   - responsive @media conditions and breakpoints

3) Do not convert longhand to risky shorthands (background/font/border) when partial overrides exist.

4) Any removal (rule/property/media query) requires:
   - usage search (grep)
   - a short report explaining why it is safe

If a requested change conflicts with these rules, STOP and explain the conflict.
