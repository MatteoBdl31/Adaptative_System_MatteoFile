 # Frontend
 
 ## Overview
 The frontend is server-rendered (Jinja templates) with progressive enhancement via vanilla
 JavaScript modules. Maps use Leaflet, charts use Chart.js, and styling is in `static/style.css`.
 
 ## Templates
 - `base.html`: global layout, navigation, and CSS include.
 - `demo.html`: demo mode and comparison UI.
 - `recommendations.html`: recommendation map and cards.
 - `trail_detail.html`: trail detail view from recommendations.
 - `profile.html`: profile dashboard and trail management.
 - `profile_trail_detail.html`: extended detail view with analytics.
 - `all_trails.html`: global trails list and map view.
 - `admin_rules.html`: rules inspection.
 - `dashboard.html`: legacy dashboard view.
 
 ## Static JavaScript modules
 | File | Purpose | Primary pages |
 | --- | --- | --- |
 | `static/app.js` | Shared app utilities, API client, map manager, view helpers | multiple |
 | `static/demo.js` | Demo mode, comparison, form handling, maps | `demo.html` |
 | `static/recommendations.js` | View toggles and map rendering | `recommendations.html` |
 | `static/profile.js` | Dashboard switching and charts | `profile.html` |
 | `static/trail_list.js` | Saved/started/completed trail lists, filters, actions | `profile.html` |
 | `static/trail_detail_page.js` | Detail page data rendering, map, charts | `profile_trail_detail.html` |
 | `static/upload.js` | Upload performance data and matching | `profile.html` |
 
 ## External libraries
 - Leaflet (map rendering; loaded per template).
 - Chart.js (dashboard and elevation charts).
 
 ## Client-side data flow (examples)
 - Recommendations:
   - Server renders `recommendations.html` with `combined_trails`.
   - `recommendations.js` initializes Leaflet and plots trails.
 - Profile dashboards:
   - `profile.js` calls `/api/profile/<user_id>/dashboard/<dashboard_type>`.
   - Charts are rendered dynamically.
 - Trail detail (profile):
   - `trail_detail_page.js` fetches trail data and performance time series.
 
 ## Accessibility and performance
 - Templates use semantic sections and aria labels in the base layout.
 - Weather enrichment is limited server-side to reduce API calls.
 - Maps are initialized lazily and invalidated on view change.
 
## See also
- Backend routes: `docs/backend.md`
- Recommendation engine: `docs/recommendation_engine.md`
- Functional documentation: `docs/functional.md`
