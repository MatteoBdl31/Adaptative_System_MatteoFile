## Adaptive Quiz System

This repository contains the source code for the Adaptive Quiz System coursework project.  
Follow the steps below to set up your local environment and obtain the required offline
assets.

### 1. Install dependencies

1. Create and activate a Python 3.9+ virtual environment (recommended).
2. Install requirements:

```
pip install -r requirements.txt
```

### 2. Retrieve large GIS data

The application relies on a GIS shapefile that is too large to store in Git:

```
adaptive_quiz_system/hiking_foot_routes_lineLine.shp
```

Along with this main `.shp` file, make sure the accompanying `.shx`, `.dbf`, and `.prj` files
from the same dataset sit in the `adaptive_quiz_system/` directory.

**How to get it**

- Download the archive from the shared drive link (to be provided).
- Extract the shapefile components into `adaptive_quiz_system/`.

The structure should look like:

```
adaptive_quiz_system/
  …
  hiking_foot_routes_lineLine.dbf
  hiking_foot_routes_lineLine.prj
  hiking_foot_routes_lineLine.shp
  hiking_foot_routes_lineLine.shx
```

If you already cloned the repo before these files were ignored, run
`git rm --cached adaptive_quiz_system/hiking_foot_routes_lineLine.*` and re-commit so the
large files are fully removed from your local Git history.

### 3. Run the app

From the project root:

```
cd adaptive_quiz_system
python app.py
```

The Flask server starts on the default port; open the printed URL in your browser.

