## Adaptive Trail Recommender

The legacy quiz artefacts have been replaced with a geo-aware adaptive trail demo fed by real
French Alps data. Follow the steps below to hydrate the dataset, rebuild the SQLite stores, and
run the personalised experience.

### 1. Install dependencies

```
python -m venv .venv
.venv\Scripts\activate  # or `source .venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
```

### 2. Retrieve the hiking shapefile

Place the `hiking_foot_routes_lineLine.*` files (shp/shx/dbf/prj) inside `adaptive_quiz_system/data/source/`.
Those files are sourced from the French data.gouv “Itinéraires de randonnée” dataset and are too
large for Git.

Folder excerpt:

```
adaptive_quiz_system/
  data/
    source/
      hiking_foot_routes_lineLine.dbf
      hiking_foot_routes_lineLine.prj
      hiking_foot_routes_lineLine.shp
      hiking_foot_routes_lineLine.shx
```

### 3. Generate real trails + seed the databases

The script will parse the shapefile, call the Open Elevation API (limited sample per run), and
recreate `users.db`, `rules.db`, and `trails.db` with the curated data.

```
cd adaptive_quiz_system
python backend/init_db.py
```

To regenerate trails without touching users/rules you can also run the loader directly:

```
python -m data_pipeline.alps_trails_loader --limit 60 --write-db
```

### 4. Run the Flask app

The Flask entry point now lives in `run.py` (the application itself is inside the `app/`
package):

```
cd adaptive_quiz_system
python run.py
```

The demo exposes:

- `/demo` – trail recommendations with map/list/card views and side-by-side user comparison
- `/trail/<user_id>/<trail_id>` – detailed view with interactive map + elevation profile

All pages automatically reuse the personalised filters stored in SQLite so the UI is ready for
presentations without extra configuration.

