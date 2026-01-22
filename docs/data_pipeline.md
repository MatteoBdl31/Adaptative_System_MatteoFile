 # Data Pipeline and Seeding
 
 ## Purpose
 The data pipeline ingests French hiking trail shapefiles, builds a curated trail dataset,
 enriches trails with elevation profiles, and seeds SQLite databases for the demo.
 
 ## Inputs
 - Shapefile components placed in `adaptive_quiz_system/data/source/`:
   - `hiking_foot_routes_lineLine.shp`
   - `hiking_foot_routes_lineLine.shx`
   - `hiking_foot_routes_lineLine.dbf`
   - `hiking_foot_routes_lineLine.prj`
 
 ## Outputs
 - `adaptive_quiz_system/backend/trails.db` (curated trails)
 - `adaptive_quiz_system/backend/users.db` (demo users, history, profiles)
 - `adaptive_quiz_system/backend/rules.db` (rule set)
 
 ## Pipeline stages
 1. Load shapefile and filter by region boundaries.
 2. Normalize trail attributes (distance, difficulty, duration).
 3. Fetch elevation samples from Open-Elevation API.
 4. Persist curated trails to `trails.db`.
 5. Seed users, preferences, and completed trail history.
 6. Compute user profiles and generate fitness metrics.
 
 ### Pipeline diagram (Mermaid)
 
 ```mermaid
 flowchart LR
     shapefile[TrailShapefile] --> loader[AlpsTrailsLoader]
     loader --> elevationApi[OpenElevationAPI]
     loader --> trailsDb[(trails.db)]
     initDb[init_db.py] --> trailsDb
     initDb --> usersDb[(users.db)]
     initDb --> rulesDb[(rules.db)]
     initDb --> fitnessGen[generate_dummy_fitness_data]
 ```
 
 ## Primary scripts
 - `data_pipeline/alps_trails_loader.py`
   - Validates shapefile components.
   - Filters trails by geographic regions.
   - Calculates difficulty and duration (Naismith-based estimation).
   - Calls Open-Elevation to build elevation profiles.
 - `backend/init_db.py`
   - Seeds rules, users, and completed trail history.
   - Populates user profiles and performance metrics.
   - Optionally loads from reference JSON if present (checks file existence).
 
 ## Commands
 From repo root:
 - Seed DBs (rules, users, trails):
   - `cd adaptive_quiz_system`
   - `python backend/init_db.py`
 - Load trails only (without full reseed):
   - `python -m data_pipeline.alps_trails_loader --limit 60 --write-db`
 
 ## External dependencies
 - Open-Elevation API: `https://api.open-elevation.com/api/v1/lookup`
 - Requires network access and has throughput limits.
 
 ## Failure modes
 - Missing shapefile components -> loader raises `FileNotFoundError`.
 - Elevation API failures -> trails still saved with fallback elevation gain.
 - Partial data -> difficulty and duration are estimated.
 
## See also
- Operations: `docs/operations.md`
- Backend DB schema: `docs/backend.md`
- Functional documentation: `docs/functional.md`
