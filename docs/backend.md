 # Backend
 
 ## Flask app entry point
 - Routes live in `adaptive_quiz_system/app/__init__.py`.
 - `run.py` starts the Flask app for local development.
 
## Page routes
| Method | Route | Purpose | Template |
| --- | --- | --- | --- |
| GET/POST | `/` | Redirects to demo | (redirect only) |
| GET | `/demo` | Demo mode with multi-user comparison and trail recommendations | `demo.html` |
| GET | `/trail/<user_id>/<trail_id>` | Trail detail view | `trail_detail.html` |
 | POST | `/trail/<user_id>/<trail_id>/complete` | Record completion | (redirect) |
 | GET | `/profile/<user_id>` | Profile dashboard | `profile.html` |
 | GET | `/profile/<user_id>/trail/<trail_id>` | Profile trail detail | `profile_trail_detail.html` |
 | GET | `/dashboard/<user_id>` | Legacy dashboard view | `dashboard.html` |
 | GET | `/admin/rules` | Rules inspection | `admin_rules.html` |
 | GET | `/trails` | All trails map/list | `all_trails.html` |
 
 ## API routes
 | Method | Route | Purpose |
 | --- | --- | --- |
 | GET | `/api/trails` | All trails as JSON |
 | GET | `/api/trail/<trail_id>` | Single trail detail JSON |
 | GET | `/api/weather/batch` | Batch weather forecasts for trails |
 | GET | `/api/trail/<trail_id>/weather/weekly` | 7-day forecast for a trail |
 | GET | `/api/demo/results` | Demo results JSON |
 | GET | `/api/explanations/general/<user_identifier>` | AI general explanation |
 | GET | `/api/explanations/trail/<user_identifier>/<trail_id>` | AI trail explanation |
 | POST | `/api/profile/<user_id>/trails/save` | Save trail |
 | DELETE | `/api/profile/<user_id>/trails/<trail_id>/unsave` | Unsave trail |
 | POST | `/api/profile/<user_id>/trails/start` | Start trail |
 | POST | `/api/profile/<user_id>/trails/<trail_id>/progress` | Update progress |
 | POST | `/api/profile/<user_id>/trails/<trail_id>/complete` | Complete started trail |
 | GET | `/api/profile/<user_id>/trails` | Get saved/started/completed |
 | POST | `/api/profile/<user_id>/trails/<trail_id>/photos` | Upload photos |
 | GET | `/api/profile/<user_id>/dashboard/<dashboard_type>` | Dashboard metrics |
 | GET | `/api/profile/<user_id>/dashboard/metrics` | All dashboard metrics |
 | GET | `/api/profile/<user_id>/trail/<trail_id>/analytics` | Trail analytics |
 | GET | `/api/profile/<user_id>/trail/<trail_id>/predictions` | Predict metrics |
 | GET | `/api/profile/<user_id>/trail/<trail_id>/recommendations` | AI recommendations |
 | GET | `/api/profile/<user_id>/trail/<trail_id>/completions` | All completions |
 | GET | `/api/profile/<user_id>/trail/<trail_id>/performance` | Performance time-series |
 | POST | `/api/profile/<user_id>/upload` | Upload performance file |
 | POST | `/api/profile/<user_id>/upload/<upload_id>/associate` | Associate upload |
 | GET | `/api/profile/<user_id>/uploads` | List uploads |
 | GET | `/api/dashboard/<user_id>/heart-rate-trends` | Legacy dashboard data |
 | GET | `/api/dashboard/<user_id>/gps-aggregates` | Legacy dashboard data |
 | GET | `/api/dashboard/<user_id>/performance-improvements` | Legacy dashboard data |
 
 ## Service modules and responsibilities
 - `backend/db.py`: SQLite access, rule retrieval, trail/user reads, profile updates.
 - `backend/trail_management.py`: save/start/complete trails and progress tracking.
 - `backend/upload_service.py`: parse/validate/match uploads and store time-series data.
 - `backend/trail_analytics.py`: analyze performance and predict metrics.
 - `backend/dashboard_service.py`: compute profile dashboards (fitness, elevation, etc).
 - `backend/weather_service.py`: Open-Meteo forecasts and weather matching.
 - `backend/trail_recommendation_service.py`: AI recommendations for trail detail page with similar-profile hiker context.
 - `backend/explanation_service.py`: OpenAI/OpenRouter explanation generation.
 - `backend/user_profiling.py`: profile detection based on completed trails.
 
 ## Data model (high level)
 SQLite databases are created by `backend/init_db.py`. Key tables include:
 - `users`, `preferences`, `performance`
 - `completed_trails`, `saved_trails`, `started_trails`
 - `trail_performance_data`, `uploaded_trail_data`, `trail_photos`
 - `user_profiles`
 - `rules` (rules.db) and trail data in `trails.db`
 
 ## Error handling and fallbacks
 - Weather calls time out and return `None` on errors.
 - Explanation service falls back to rule-based explanations when API fails.
 - Recommendation engine uses progressive fallback for low candidate counts.
 
## See also
- Recommendation engine: `docs/recommendation_engine.md`
- Data pipeline: `docs/data_pipeline.md`
- Functional documentation: `docs/functional.md`
