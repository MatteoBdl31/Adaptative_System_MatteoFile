 # Adaptive Trail Recommender - Overview
 
 ## Purpose
 Adaptive Trail Recommender is a Flask-based demo application that recommends hiking trails based on
 user profile, context (time, device, weather, season, connection), and a rules engine. It uses real
 French hiking trail data (from a shapefile) and enriches results with weather and AI explanations.
 
## Key capabilities
- Context-aware trail recommendations with progressive fallback.
- Profile detection from user trail history.
- Collaborative recommendations based on similar users' preferences and ratings.
- Trail detail views with map, elevation profile, and performance analytics.
- Demo mode with side-by-side comparisons.
- Upload and ingestion of smartwatch performance data.
 
 ## Entry points
 - App runtime: `adaptive_quiz_system/run.py`
 - Flask app factory: `adaptive_quiz_system/app/__init__.py`
 - DB seeding: `adaptive_quiz_system/backend/init_db.py`
 - Trail ingestion: `adaptive_quiz_system/data_pipeline/alps_trails_loader.py`
 
## High-level flow
1. User hits a page route (demo, trail detail, profile).
2. Flask resolves user and context, then calls `adapt_trails()`.
3. The recommendation engine builds filters, scores trails, enriches weather, ranks, and explains.
4. Templates render data and load JS for interactive maps and dashboards.
 
 ## Data stores
 - `adaptive_quiz_system/backend/users.db` (user profiles, performance, uploads)
 - `adaptive_quiz_system/backend/trails.db` (trail data and geometry)
 - `adaptive_quiz_system/backend/rules.db` (rule-based adaptation conditions)
 
 ## External services
 - Open-Meteo API: weather forecasts (no API key required).
 - Open-Elevation API: elevation profiles for trails.
 - OpenAI/OpenRouter: AI explanation generation (optional; requires API key).
 
## Runtime URLs (examples)
- `/demo` - interactive demo mode with multi-user comparisons and trail recommendations.
- `/trail/<user_id>/<trail_id>` - trail detail view with elevation.
- `/profile/<user_id>` - user dashboard and trail management.
 
 ## Repository layout (core)
 - `adaptive_quiz_system/app/` Flask routes and templates binding.
 - `adaptive_quiz_system/backend/` persistence and service layer.
 - `adaptive_quiz_system/recommendation_engine/` filtering, scoring, ranking, explanations.
 - `adaptive_quiz_system/data_pipeline/` trail ingestion utilities.
 - `adaptive_quiz_system/templates/` Jinja pages.
 - `adaptive_quiz_system/static/` JS and CSS for UI.
 
## Glossary
- **Exact match**: a trail above a configured relevance threshold and passing hard filters.
- **Suggestion**: a relevant trail below the exact-match threshold or failing strict criteria.
- **Collaborative recommendation**: a trail recommended based on what similar users (same profile) have completed and rated highly.
- **Context**: request-driven inputs (time available, device, weather, season, connection).
- **Profile**: a behavioral label inferred from past completions.
 
## See also
- Architecture: `docs/architecture.md`
- Backend details: `docs/backend.md`
- Recommendation engine: `docs/recommendation_engine.md`
- Data pipeline: `docs/data_pipeline.md`
- Frontend details: `docs/frontend.md`
- Operations: `docs/operations.md`
- Functional documentation: `docs/functional.md`
