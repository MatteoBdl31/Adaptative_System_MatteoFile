#!/usr/bin/env python3
"""
Export trails data to JSON reference file for reproducible data generation.

This script exports the trails loaded from the shapefile to a JSON file
that can be used to ensure all developers generate exactly the same trails
with the same characteristics (including elevation data from API).

Usage:
    python data/seed/export_trails_reference.py
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.init_db import seed_trails

def export_trails_reference():
    """Export trails to JSON reference file."""
    print("=" * 70)
    print("EXPORTING TRAILS REFERENCE DATA")
    print("=" * 70)
    print("\nLoading trails from shapefile...")
    
    # Load trails exactly as init_db.py does
    trails = seed_trails(limit=100)
    
    if not trails:
        print("ERROR: No trails loaded. Ensure the shapefile is present.")
        return False
    
    print(f"Loaded {len(trails)} trails")
    
    # Export with all important characteristics
    trails_reference = []
    for trail in trails:
        trails_reference.append({
            "trail_id": trail.get("trail_id"),
            "name": trail.get("name"),
            "description": trail.get("description"),
            "difficulty": trail.get("difficulty"),
            "distance": trail.get("distance"),
            "duration": trail.get("duration"),
            "elevation_gain": trail.get("elevation_gain"),  # Real API value
            "elevation_profile": trail.get("elevation_profile"),  # Full profile
            "trail_type": trail.get("trail_type"),
            "landscapes": trail.get("landscapes"),
            "popularity": trail.get("popularity"),
            "safety_risks": trail.get("safety_risks"),
            "accessibility": trail.get("accessibility"),
            "closed_seasons": trail.get("closed_seasons"),
            "region": trail.get("region"),
            "latitude": trail.get("latitude"),
            "longitude": trail.get("longitude"),
            "coordinates": trail.get("coordinates"),  # GeoJSON
            "source": trail.get("source"),
            "is_real": trail.get("is_real", 1)
        })
    
    # Save to JSON
    output_path = Path(__file__).parent / "trails_reference.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(trails_reference, f, indent=2, ensure_ascii=False)
    
    file_size = output_path.stat().st_size / 1024  # KB
    print(f"\n✓ Exported {len(trails_reference)} trails to:")
    print(f"  {output_path}")
    print(f"  File size: {file_size:.1f} KB")
    print("\nThis file can be versioned in Git and used for reproducible data generation.")
    
    return True

if __name__ == "__main__":
    success = export_trails_reference()
    sys.exit(0 if success else 1)
