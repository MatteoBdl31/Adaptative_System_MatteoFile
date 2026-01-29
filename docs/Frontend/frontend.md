 # Frontend
 
 ## Overview
 The frontend is server-rendered (Jinja templates) with progressive enhancement via vanilla
 JavaScript modules. Maps use Leaflet, charts use Chart.js, and styling is in `static/style.css`.
 
## Templates
- `base.html`: global layout, navigation, and CSS include.
- `demo.html`: demo mode, comparison UI, and trail recommendations.
- `trail_detail.html`: trail detail view from demo.
- `profile.html`: profile dashboard.
- `my_trails.html`: My Trails (saved/started/completed), upload of performance data (smartwatch JSON).
- `profile_trail_detail.html`: extended detail view with analytics.
- `all_trails.html`: global trails list and map view.
- `recommendations.html`: dedicated recommendations page with collaborative section.
- `admin_rules.html`: rules inspection.
- `dashboard.html`: legacy dashboard view.
 
## Static JavaScript modules
| File | Purpose | Primary pages |
| --- | --- | --- |
| `static/app.js` | Shared app utilities, API client, map manager, view helpers | multiple |
| `static/demo.js` | Demo mode, comparison, form handling, maps, recommendations | `demo.html` |
| `static/profile.js` | Dashboard switching and charts | `profile.html` |
| `static/trail_list.js` | Saved/started/completed trail lists, filters, actions, upload of performance data (smartwatch JSON) | `my_trails.html` |
| `static/trail_detail_page.js` | Detail page data rendering, map, charts, recommendations UI | `profile_trail_detail.html` |

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
  - Server renders `demo.html` with trail recommendations (exact matches, suggestions, and collaborative).
  - `demo.js` initializes Leaflet and plots trails on map view.
  - Collaborative recommendations are displayed in a separate "Popular with Similar Hikers" section.
  - Trails can appear in multiple categories (exact/suggestions with collaborative markers, or standalone collaborative).
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
 
## Collaborative Recommendations UI

The system displays collaborative recommendations (trails popular with similar users) in multiple ways:

1. **Collaborative Markers**: Trails that appear in exact matches or suggestions but are also recommended by similar users display:
   - A collaborative icon (👥) with hover tooltip "Similar profiles likes it"
   - A dashed ring around map markers in collaborative color (#f71e50)
   - Collaborative metadata (average rating, user count) when available

2. **Dedicated Collaborative Section**: A separate "Popular with Similar Hikers" section displays:
   - Trails that are collaborative but not in exact/suggestions
   - Badge showing average rating and number of users who completed it
   - Styling with left border accent in collaborative color

3. **View Types**: Trails have a `view_type` property that can include "collaborative" alongside "recommended" or "suggested", allowing trails to appear in multiple categories with appropriate styling.

4. **Map Visualization**: Collaborative trails are marked on maps with:
   - Special marker styling (dashed ring)
   - Collaborative color (#f71e50) for standalone collaborative trails
   - Legend entry explaining collaborative markers

## Accessibility and performance
- Templates use semantic sections and aria labels in the base layout.
- Weather enrichment is limited server-side to reduce API calls.
- Maps are initialized lazily and invalidated on view change.
 
## See also
- Backend routes: `docs/backend.md`
- Recommendation engine: `docs/recommendation_engine.md`
- Functional documentation: `docs/functional.md`
