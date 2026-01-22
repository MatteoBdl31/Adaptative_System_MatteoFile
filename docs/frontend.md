 # Frontend
 
 ## Overview
 The frontend is server-rendered (Jinja templates) with progressive enhancement via vanilla
 JavaScript modules. Maps use Leaflet, charts use Chart.js, and styling is in `static/style.css`.
 
## Templates
- `base.html`: global layout, navigation, and CSS include.
- `demo.html`: demo mode, comparison UI, and trail recommendations.
- `trail_detail.html`: trail detail view from demo.
- `profile.html`: profile dashboard and trail management.
- `profile_trail_detail.html`: extended detail view with analytics.
- `all_trails.html`: global trails list and map view.
- `admin_rules.html`: rules inspection.
- `dashboard.html`: legacy dashboard view.
 
## Static JavaScript modules
| File | Purpose | Primary pages |
| --- | --- | --- |
| `static/app.js` | Shared app utilities, API client, map manager, view helpers | multiple |
| `static/demo.js` | Demo mode, comparison, form handling, maps, recommendations | `demo.html` |
| `static/profile.js` | Dashboard switching and charts | `profile.html` |
| `static/trail_list.js` | Saved/started/completed trail lists, filters, actions | `profile.html` |
| `static/trail_detail_page.js` | Detail page data rendering, map, charts, recommendations UI | `profile_trail_detail.html` |
| `static/upload.js` | Upload performance data and matching | `profile.html` |

### Adaptive Navigation Implementation

The `profile_trail_detail.html` template includes adaptive navigation ordering logic in the `initStickyNavigation()` function:
- Extracts user profile from `userProfile` (string or `primary_profile` property)
- Uses a switch statement to determine tab order based on profile type
- Reorders DOM elements to match the determined order
- Sets up sticky positioning accounting for app header height
- Implements IntersectionObserver for active tab highlighting
- Handles smooth scroll-to-section on tab click
 
 ## External libraries
 - Leaflet (map rendering; loaded per template).
 - Chart.js (dashboard and elevation charts).
 
## Client-side data flow (examples)
- Demo/Recommendations:
  - Server renders `demo.html` with trail recommendations.
  - `demo.js` initializes Leaflet and plots trails on map view.
- Profile dashboards:
   - `profile.js` calls `/api/profile/<user_id>/dashboard/<dashboard_type>`.
   - Charts are rendered dynamically.
 - Trail detail (profile):
   - `trail_detail_page.js` fetches trail data and performance time series.
   - **Adaptive Navigation**: Navigation tabs are reordered based on user profile type:
     - **Performance Athlete**: Overview → Performance → Route → Weather → Recommendations
     - **Elevation Lover**: Overview → Route → Weather → Performance → Recommendations
     - **Photographer**: Overview → Weather → Recommendations → Route → Performance
     - **Contemplative**: Overview → Recommendations → Weather → Route → Performance
     - **Explorer**: Overview → Route → Recommendations → Weather → Performance
     - **Casual/Family**: Overview → Weather → Recommendations → Route → Performance
     - **Default**: Overview → Route → Weather → Performance → Recommendations
   - Navigation bar is sticky and scrolls to sections on click.
   - Active tab is highlighted based on scroll position using IntersectionObserver.
   - **Recommendations Section**: Displays concise AI-generated recommendations with:
     - Summary box with left border accent highlighting key advice
     - Responsive grid layout (2-3 columns) for actionable tips
     - Compact tip cards with hover effects
     - Similar-profile hiker insights when available
     - Profile-specific focus areas (elevation, photography, performance, etc.)
 
 ## Accessibility and performance
 - Templates use semantic sections and aria labels in the base layout.
 - Weather enrichment is limited server-side to reduce API calls.
 - Maps are initialized lazily and invalidated on view change.
 
## See also
- Backend routes: `docs/backend.md`
- Recommendation engine: `docs/recommendation_engine.md`
- Functional documentation: `docs/functional.md`
