# Cursor Rules — 10 User Adaptive Interfaces (UI scope only)

Follow adaptive_quiz_system/CSS_Guidance/UI_ADAPTIVE_POLICY.md and validate changes with adaptive_quiz_system/CSS_Guidance/UI_ADAPTIVE_CHECKLIST.md.

Scope:
- HTML templates (Jinja2)
- CSS (style.css)
- vanilla JS

Do:
- Use CSS-first solutions for:
  - prefers-color-scheme
  - prefers-reduced-motion
  - forced-colors
  - pointer/hover capabilities
- Preserve accessibility:
  - semantic HTML
  - correct input labeling
  - visible focus via :focus-visible
  - minimal correct ARIA

Do not:
- Introduce business/backend changes (unless explicitly requested)
- Add JS-driven theming when CSS preference is sufficient
- Add ARIA unless it solves a real issue

When proposing changes:
- prefer minimal diffs
- propose patch snippets + clear insertion points
- state which checklist items are satisfied
