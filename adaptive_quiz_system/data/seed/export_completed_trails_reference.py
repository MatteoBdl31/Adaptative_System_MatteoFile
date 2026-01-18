#!/usr/bin/env python3
"""
Export completed trails assignments to JSON reference file.

This script exports the exact trail assignments (which user completed which trail)
to ensure reproducible user profile generation.

Usage:
    python data/seed/export_completed_trails_reference.py
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

def export_completed_trails_reference():
    """Export completed trails assignments to JSON."""
    print("=" * 70)
    print("EXPORTING COMPLETED TRAILS REFERENCE DATA")
    print("=" * 70)
    
    # Check if trails_reference.json exists
    trails_ref_path = Path(__file__).parent / "trails_reference.json"
    
    if trails_ref_path.exists():
        print("\nLoading trails from reference JSON...")
        with open(trails_ref_path, "r", encoding="utf-8") as f:
            trails = json.load(f)
    else:
        print("\nLoading trails from shapefile (trails_reference.json not found)...")
        from backend.init_db import seed_trails
        trails = seed_trails(limit=100)
    
    if not trails:
        print("ERROR: No trails available.")
        return False
    
    print(f"Loaded {len(trails)} trails")
    
    # Generate completed trails assignments
    print("\nGenerating completed trails assignments...")
    from backend.diversify_profiles import create_diverse_completed_trails
    
    completed_trails = create_diverse_completed_trails(trails)
    
    if not completed_trails:
        print("ERROR: No completed trails generated.")
        return False
    
    # Export to JSON
    completed_trails_reference = [
        {
            "user_id": user_id,
            "trail_id": trail_id,
            "completion_date": date,
            "actual_duration": duration,
            "rating": rating
        }
        for user_id, trail_id, date, duration, rating in completed_trails
    ]
    
    # Save to JSON
    output_path = Path(__file__).parent / "completed_trails_reference.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(completed_trails_reference, f, indent=2, ensure_ascii=False)
    
    file_size = output_path.stat().st_size / 1024  # KB
    
    # Count by user
    user_counts = {}
    for ct in completed_trails_reference:
        user_id = ct["user_id"]
        user_counts[user_id] = user_counts.get(user_id, 0) + 1
    
    print(f"\n✓ Exported {len(completed_trails_reference)} completed trail assignments to:")
    print(f"  {output_path}")
    print(f"  File size: {file_size:.1f} KB")
    print(f"  Assigned to {len(user_counts)} users")
    print("\nThis file ensures reproducible user profile generation.")
    
    return True

if __name__ == "__main__":
    success = export_completed_trails_reference()
    sys.exit(0 if success else 1)
