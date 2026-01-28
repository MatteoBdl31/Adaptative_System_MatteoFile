# UI Adaptive Interfaces — Checklist (UI Only)

Use this checklist to validate any UI change (HTML/CSS/JS).

---

## 1) Preferences

### Color scheme
- [ ] `prefers-color-scheme: dark` is supported
- [ ] Theming is driven by CSS variables (tokens) when possible
- [ ] No requirement for JavaScript to get a correct theme

### Reduced motion
- [ ] `prefers-reduced-motion: reduce` reduces or disables animations
- [ ] Smooth scrolling is disabled when reduced motion is requested
- [ ] Transitions are reduced where safe (or scoped appropriately)

### Forced colors / high contrast
- [ ] `forced-colors: active` remains usable (text readable, controls visible)
- [ ] No critical information is conveyed by color alone
- [ ] Focus remains visible

---

## 2) Input & capabilities

- [ ] No critical UI is hover-only (works with hover: none)
- [ ] Tap targets are usable on touch (pointer: coarse)
- [ ] Responsive behavior holds at narrow widths (no clipped controls)

---

## 3) Accessibility

- [ ] Inputs have correct accessible names (label/for preferred)
- [ ] Keyboard navigation works (tab order logical)
- [ ] Visible focus is present (`:focus-visible`) on interactive elements
- [ ] ARIA is correct and minimal (no redundant roles/labels)

---

## 4) Progressive enhancement

- [ ] Core pages remain readable and usable if JS is disabled
- [ ] Enhancements do not block critical actions (graceful fallback)

---

## 5) Evidence (required for refactor lots)

- [ ] Provide a short changelog of what changed
- [ ] List the files and selectors impacted
- [ ] List the “risks to verify” (focus/hover/responsive/etc.)
