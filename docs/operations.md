 # Operations
 
 ## Requirements
 - Python 3.x
 - Dependencies from:
   - `requirements.txt`
   - `adaptive_quiz_system/requirements.txt`
 
 ## Setup
 From repo root:
 1. Create and activate a virtual environment.
 2. Install dependencies:
    - `pip install -r requirements.txt`
    - `pip install -r adaptive_quiz_system/requirements.txt`
 3. Place shapefile components in `adaptive_quiz_system/data/source/`.
 4. Seed databases:
    - `cd adaptive_quiz_system`
    - `python backend/init_db.py`
 5. Run the app:
    - `python run.py`
 
 ## Environment variables
 - Recommendation config:
   - `REC_EXACT_MATCH_THRESHOLD`
   - `REC_MIN_CANDIDATES`
   - `REC_MAX_FALLBACK_LEVELS`
   - `REC_DEBUG`
   - `REC_SOFT_FILTER`
   - `REC_ALWAYS_RETURN`
   - `REC_MIN_RESULTS`
   - `REC_MAX_TRAILS`
 - Data pipeline:
   - `TRAIL_LIMIT` (used by `init_db.py`)
 - AI explanations:
   - `OPENROUTER_API_KEY` (preferred if set)
   - `OPENAI_API_KEY`
 
 The app loads environment variables via `python-dotenv` (`.env` file supported).
 
 ## External services
 - Open-Meteo (weather): no API key required, forecasts up to 16 days ahead.
 - Open-Elevation (elevation profiles): free, best-effort.
 - OpenAI/OpenRouter (explanations): optional, requires API key.
 
 ## Troubleshooting
 - Missing shapefile: `FileNotFoundError` from `alps_trails_loader.py`.
 - Weather data missing: request outside Open-Meteo forecast range (older or >16 days).
 - AI explanations empty: API key not set or API error; fallback used automatically.
 - Map not rendering: check Leaflet script include in the page template.
 
 ## Operational notes
 - SQLite DB files are created under `adaptive_quiz_system/backend/`.
 - Re-running `init_db.py` resets users/rules and may overwrite data.
 - Weather enrichment is limited to top-scored trails for performance.
 
## See also
- Data pipeline: `docs/data_pipeline.md`
- Backend routes: `docs/backend.md`
- Functional documentation: `docs/functional.md`
