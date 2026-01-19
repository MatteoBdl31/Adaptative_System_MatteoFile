# Reference Data for Reproducible Database Generation

This directory contains reference data files that ensure all developers can generate exactly the same database content, including trails, user assignments, and calculated profiles.

## Files

- **`trails_reference.json`**: Complete trail data with all characteristics (including elevation profiles from API)
- **`completed_trails_reference.json`**: Exact assignments of which users completed which trails
- **`export_trails_reference.py`**: Script to export trails to JSON reference file
- **`export_completed_trails_reference.py`**: Script to export completed trails assignments to JSON

## Quick Start

### For Developers (Using Reference Data)

To generate the database with exact reference data:

```bash
# Activate virtual environment
source .venv/bin/activate

# Initialize database using reference data
cd adaptive_quiz_system
python backend/init_db.py --use-reference
```

This will:
1. Load trails from `trails_reference.json` (no API calls needed)
2. Load completed trail assignments from `completed_trails_reference.json`
3. Generate the same user profiles as the reference

### For Maintainers (Updating Reference Data)

To update the reference data files:

```bash
# 1. Ensure shapefile is downloaded
python download_trails_shapefile.py

# 2. Export trails reference (this will call the elevation API)
python data/seed/export_trails_reference.py

# 3. Export completed trails assignments
python data/seed/export_completed_trails_reference.py

# 4. Commit the updated JSON files to Git
git add data/seed/*.json
git commit -m "Update reference data for reproducible generation"
```

## Why Reference Data?

### Problem Without Reference Data

1. **API Non-Determinism**: The Open Elevation API may return slightly different values
2. **Order Dependency**: Trail selection depends on processing order
3. **Different Results**: Each developer gets slightly different data

### Solution With Reference Data

1. **Exact Reproducibility**: All developers get identical trails and assignments
2. **No API Calls**: Reference data includes elevation profiles (faster initialization)
3. **Versioned**: JSON files are versioned in Git (small, text-based, diffable)
4. **Flexible**: Can still generate fresh data without `--use-reference` flag

## File Formats

### trails_reference.json

```json
[
  {
    "trail_id": "french_alps_20014199",
    "name": "Col de la Croix",
    "difficulty": 6.5,
    "distance": 12.3,
    "duration": 180,
    "elevation_gain": 850,
    "elevation_profile": [...],
    "trail_type": "loop",
    "landscapes": "peaks,alpine",
    "popularity": 7.8,
    "region": "french_alps",
    ...
  }
]
```

### completed_trails_reference.json

```json
[
  {
    "user_id": 101,
    "trail_id": "french_alps_20014199",
    "completion_date": "2024-01-15",
    "actual_duration": 110,
    "rating": 5
  }
]
```

## Workflow

### Initial Setup (First Time)

```bash
# 1. Download shapefile
python download_trails_shapefile.py

# 2. Generate reference data (one-time, by maintainer)
python data/seed/export_trails_reference.py
python data/seed/export_completed_trails_reference.py

# 3. Commit reference files
git add data/seed/*.json
git commit -m "Add reference data for reproducible generation"
```

### Daily Development

```bash
# Option 1: Use reference data (fast, reproducible)
python backend/init_db.py --use-reference

# Option 2: Generate fresh data (slower, may vary slightly)
python backend/init_db.py
```

## Updating Reference Data

Reference data should be updated when:
- New regions are added
- Trail selection criteria change significantly
- User profile assignments need adjustment

**Process:**
1. Run export scripts to generate new reference files
2. Test that `--use-reference` produces expected results
3. Commit updated JSON files
4. Notify team of the update

## Troubleshooting

### "trails_reference.json not found"

- Run `export_trails_reference.py` first, or
- Use `python backend/init_db.py` without `--use-reference` flag

### "Different profiles detected"

- Ensure you're using `--use-reference` flag
- Check that reference JSON files are up to date
- Verify you're using the same version of the code

### "API errors during export"

- Check internet connection
- Open Elevation API may be temporarily unavailable
- Retry the export script
