# UI Adaptive Interfaces — Policy (Scope: UI only)

## Scope
This policy applies ONLY to UI work:
- HTML templates (Jinja2, *.html)
- CSS (style.css)
- Vanilla JS (DOM interactions)
It does NOT define business rules, backend logic, or recommendation behavior.

## Goal
Build interfaces that adapt to:
1) user preferences (system/browser)
2) device capabilities (input & interaction)
3) accessibility needs
…while remaining usable with progressive enhancement.

---

## A) Preferences — CSS-first (Mandatory)

### 1) Color scheme (light/dark)
- Must support dark mode via `@media (prefers-color-scheme: dark)`
- Prefer CSS variables (tokens) to drive theming
- Do NOT require JavaScript for basic theming

### 2) Motion
- Must respect `@media (prefers-reduced-motion: reduce)`
- Reduce/disable:
  - animations
  - transitions where possible
  - smooth scrolling
  - parallax / attention-grabbing motion
- Use CSS-first; JS only if a library forces motion and has an explicit switch

### 3) Contrast / Forced colors
- Must remain usable in `@media (forced-colors: active)`
- Avoid color-only meaning (ensure icons/text affordances remain clear)
- Do not hardcode colors that break forced-colors expectations

---

## B) Device capabilities (Mandatory)

### 1) Pointer / touch friendliness
- Support coarse pointers: `@media (pointer: coarse)`
- Ensure tap targets are large enough and spaced (avoid tiny click areas)
- Avoid interactions that require precision

### 2) Hover
- Do not rely on hover-only UI for critical actions
- Support `@media (hover: none)` (no hidden-on-hover-only controls)

### 3) Responsive layout
- Mobile-first, responsive behavior across breakpoints
- Avoid brittle layout assumptions (fixed heights, overflow traps) unless justified

---

## C) Accessibility (Mandatory)

### 1) Semantics first
- Prefer semantic HTML elements over div-based UI
- Inputs must have a correct accessible name:
  - `<label for="...">` is preferred
  - ARIA only when semantics cannot express the intent

### 2) Focus management
- Visible focus is required (use `:focus-visible`)
- Do not remove outlines without an equivalent accessible alternative
- Keyboard navigation must remain possible and logical

### 3) ARIA discipline
- Avoid “ARIA noise”: do not add ARIA unless it fixes a real issue
- Never set `aria-labelledby` to the element’s own id
- Do not add roles that duplicate native semantics

---

## D) Progressive enhancement (Mandatory)

- Core pages must remain usable with JS disabled (basic read + basic actions)
- JS can enhance (e.g., map, dynamic filters) but should degrade gracefully
- Avoid hard dependencies on JS for critical accessibility features

---

## E) Implementation guidance (Recommended patterns)

### Preferred patterns
- Use semantic tokens (variables) for:
  - surfaces/backgrounds
  - text colors
  - borders
  - focus ring
  - motion durations/easings
- Place “Preferences overrides” in a clearly delimited section of CSS
- Keep changes minimal and reviewable

### Avoid
- JS-driven theme toggles if CSS preference is sufficient
- Large refactors mixed with preference changes (split into lots)
- Changing media query conditions/breakpoints without explicit approval

---

## Definition of Done
Any UI change must:
- preserve non-regression constraints
- meet the checklist in UI_ADAPTIVE_CHECKLIST.md
- be implemented with minimal risk (token- or layer-based where possible)
