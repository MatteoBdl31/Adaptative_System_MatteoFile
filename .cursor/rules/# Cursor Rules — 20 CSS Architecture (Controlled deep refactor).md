# Cursor Rules — 20 CSS Architecture (Controlled deep refactor)

Use adaptive_quiz_system/CSS_Guidance/CSS_REFACTOR_RULES.md as the source of truth for refactor strategy.

Method:
- Refactor by small, coherent lots (never big-bang).
- After each lot, provide:
  1) a changelog (bullets)
  2) impacted files/selectors list
  3) risks-to-verify list

Architecture target:
- Adopt a light ITCSS structure and BEM conventions:
  - Settings/Tokens
  - Generic/Base
  - Layout
  - Components (.c-*)
  - Utilities (.u-*)
  - Overrides/Pages (last)

Important constraints:
- Do not change cascade order unless explicitly stated and proven equivalent.
- Do not change @media conditions/breakpoints.
- Avoid introducing !important; reducing existing !important requires proof.

User Adaptive Interfaces integration:
- Keep preference/capability adaptations grouped in a clearly delimited section
  (e.g., "PREFERENCES / ADAPTIVE"), without changing media query conditions.
- Prefer token overrides (CSS variables) over per-component duplication.
