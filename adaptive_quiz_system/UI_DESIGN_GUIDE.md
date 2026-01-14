# UI Design Guide - All Trails Page

## Quick Reference for Design Elements

---

## 🎨 Color Palette

### Primary Colors
```css
--color-primary: #6366f1 (Indigo)
--color-primary-dark: #4f46e5 (Dark Indigo)
--color-primary-light: #818cf8 (Light Indigo)
```

### Brand Gradient
```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

### Semantic Colors
```css
--color-secondary: #10b981 (Green - Easy trails)
--color-accent: #f59e0b (Orange - Medium trails)
--color-danger: #ef4444 (Red - Hard trails)
```

### Neutral Colors
```css
--color-bg: #ffffff (Background)
--color-bg-secondary: #f8fafc (Secondary background)
--color-text: #1e293b (Primary text)
--color-text-secondary: #64748b (Secondary text)
--color-border: #e2e8f0 (Borders)
```

---

## 📏 Spacing Scale

```css
--space-xs: 0.25rem (4px)
--space-sm: 0.5rem (8px)
--space-md: 1rem (16px)
--space-lg: 1.5rem (24px)
--space-xl: 2rem (32px)
--space-2xl: 3rem (48px)
--space-3xl: 4rem (64px)
```

---

## 🔤 Typography Scale

```css
--font-size-xs: 0.75rem (12px)
--font-size-sm: 0.875rem (14px)
--font-size-base: 1rem (16px)
--font-size-lg: 1.125rem (18px)
--font-size-xl: 1.25rem (20px)
--font-size-2xl: 1.5rem (24px)
--font-size-3xl: 2rem (32px)
--font-size-4xl: 2.5rem (40px)
```

### Font Weights
```css
--font-weight-normal: 400
--font-weight-medium: 500
--font-weight-semibold: 600
--font-weight-bold: 700
```

---

## 🎪 Component Styles

### Buttons

#### Primary Button
```css
.btn-primary {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 0.5rem 1.5rem;
    border-radius: 0.5rem;
    font-weight: 600;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

.btn-primary:hover {
    background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    transform: translateY(-2px);
    box-shadow: 0 10px 15px rgba(0,0,0,0.1);
}
```

#### Secondary Button
```css
.btn-secondary {
    background-color: #f8fafc;
    color: #1e293b;
    border: 1px solid #e2e8f0;
    padding: 0.5rem 1.5rem;
    border-radius: 0.5rem;
    font-weight: 500;
}

.btn-secondary:hover {
    background-color: #f1f5f9;
}
```

---

### Cards

#### Trail Card
```css
.trail-card {
    background-color: white;
    border: 2px solid #e2e8f0;
    border-radius: 1rem;
    padding: 1.5rem;
    transition: all 0.2s ease;
}

.trail-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 20px 25px rgba(0,0,0,0.1);
    border-color: #6366f1;
}
```

---

### Badges

#### Difficulty Badges
```css
/* Easy */
.difficulty-easy {
    background-color: #10b981;
    color: white;
    padding: 0.25rem 1rem;
    border-radius: 9999px;
    font-weight: 700;
}

/* Medium */
.difficulty-medium {
    background-color: #f59e0b;
    color: white;
}

/* Hard */
.difficulty-hard {
    background-color: #ef4444;
    color: white;
}
```

#### Landscape Tags
```css
.landscape-tag {
    padding: 0.25rem 1rem;
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(118, 75, 162, 0.1));
    border: 1px solid #818cf8;
    color: #6366f1;
    border-radius: 9999px;
    font-size: 0.875rem;
    font-weight: 500;
}
```

---

## 🎬 Animations

### Fade In Up
```css
@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
```

### Slide In Up (Cards)
```css
@keyframes slideInUp {
    from {
        opacity: 0;
        transform: translateY(30px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
```

### Pulse (Connection Indicator)
```css
@keyframes pulse {
    0%, 100% {
        transform: scale(1);
    }
    50% {
        transform: scale(1.1);
    }
}
```

---

## 📐 Layout Patterns

### Filter Grid
```html
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem;">
    <!-- Filter items here -->
</div>
```

### Trail Card Grid
```css
.trails-card-view {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
    gap: 2rem;
}
```

### Button Group
```html
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
    <button>Button 1</button>
    <button>Button 2</button>
    <button>Button 3</button>
</div>
```

---

## 🌓 Dark Mode Support

The design includes automatic dark mode support based on system preferences:

```css
@media (prefers-color-scheme: dark) {
    :root {
        --color-bg: #0f172a;
        --color-bg-secondary: #1e293b;
        --color-text: #f1f5f9;
        --color-text-secondary: #cbd5e1;
        --color-border: #334155;
    }
}
```

---

## 📱 Responsive Breakpoints

```css
/* Mobile First Approach */

/* Small mobile */
@media (max-width: 480px) {
    /* Compact layouts */
}

/* Tablet */
@media (max-width: 768px) {
    /* Adjusted layouts */
}

/* Desktop */
@media (min-width: 769px) {
    /* Full layouts */
}
```

---

## ✨ Visual Effects

### Shadows
```css
--shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
--shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
--shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
--shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
--shadow-2xl: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
```

### Border Radius
```css
--radius-sm: 0.375rem (6px)
--radius-md: 0.5rem (8px)
--radius-lg: 0.75rem (12px)
--radius-xl: 1rem (16px)
--radius-2xl: 1.5rem (24px)
--radius-full: 9999px
```

### Transitions
```css
--transition-fast: 150ms ease
--transition-base: 200ms ease
--transition-slow: 300ms ease
```

---

## 🎯 Best Practices

### Do's ✅
- Use the brand gradient for primary actions
- Maintain consistent spacing using the spacing scale
- Apply hover effects to all interactive elements
- Use semantic color coding (green=easy, red=hard)
- Implement smooth transitions (200-300ms)
- Stack elements vertically on mobile
- Use border radius for friendly appearance
- Add shadows for depth and hierarchy

### Don'ts ❌
- Don't use arbitrary colors outside the palette
- Don't use spacing values that aren't in the scale
- Don't make clickable areas too small (<44px)
- Don't use too many different font sizes
- Don't forget hover and focus states
- Don't ignore mobile responsiveness
- Don't use animations longer than 500ms
- Don't sacrifice accessibility for aesthetics

---

## 🔍 Accessibility Notes

### Focus States
All interactive elements must have visible focus indicators:
```css
button:focus-visible,
a:focus-visible,
input:focus-visible {
    outline: 3px solid var(--color-primary);
    outline-offset: 2px;
}
```

### Color Contrast
- Primary text on white: 16.1:1 (AAA)
- Secondary text on white: 6.2:1 (AA)
- White text on primary gradient: 4.8:1 (AA)

### Touch Targets
Minimum size: 44x44px for all clickable elements on mobile

---

## 📦 Icon Usage

### Emoji Icons Used
- 🗺️ - Maps/Navigation
- 📋 - Lists
- 🃏 - Cards
- 🗓️ - Dates
- ⛰️ - Difficulty/Mountains
- 🏞️ - Landscapes
- 🚶 - Trail Type
- 📏 - Distance
- ⏱️ - Duration
- ☀️ - Sunny weather
- ☁️ - Cloudy weather
- 🌧️ - Rainy weather
- ❄️ - Snowy weather
- ⛈️ - Storm
- ✅ - Easy difficulty
- ⚠️ - Medium difficulty
- 🔴 - Hard difficulty
- ⭐ - Popularity
- ♿ - Accessibility
- 🔍 - Search/Filter
- ✖️ - Clear
- 📍 - Location
- ↑ - Scroll to top
- ⏳ - Loading

---

## 🎨 Usage Examples

### Creating a New Filter Input
```html
<div class="filter-group">
    <label for="my-filter">🎯 Label Text</label>
    <select id="my-filter">
        <option value="">All Options</option>
        <option value="option1">Option 1</option>
    </select>
</div>
```

### Creating a Stat Badge
```html
<span style="display: inline-flex; align-items: center; gap: 0.25rem; 
      padding: 0.5rem 1rem; background-color: #f8fafc; 
      border-radius: 9999px; font-size: 0.875rem;">
    📏 12.5 km
</span>
```

### Creating a Gradient Button
```html
<button style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; padding: 0.75rem 1.5rem; border: none;
        border-radius: 0.5rem; font-weight: 600; cursor: pointer;">
    Click Me
</button>
```

---

## 📊 Component Hierarchy

```
Page
├── Header (Gradient background)
│   ├── Title
│   └── Navigation Links
├── Container
│   ├── Filter Section
│   │   ├── Filter Grid
│   │   └── Button Group
│   ├── Connection Status
│   ├── View Toggle
│   ├── Map View
│   │   └── Leaflet Map
│   ├── List View
│   │   └── Trail Cards (Simple)
│   └── Card View
│       └── Trail Cards (With Maps)
└── Scroll to Top Button
```

---

This guide provides all the essential information needed to maintain and extend the All Trails page design system.
