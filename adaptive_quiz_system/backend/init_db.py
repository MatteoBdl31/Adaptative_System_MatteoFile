# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Import moved to seed_trails() to use load_french_trails for multi-region support

BASE_DIR = Path(__file__).resolve().parent
USERS_DB = BASE_DIR / "users.db"
RULES_DB = BASE_DIR / "rules.db"
TRAILS_DB = BASE_DIR / "trails.db"
DEFAULT_TRAIL_LIMIT = int(os.getenv("TRAIL_LIMIT", "100"))


def seed_rules() -> None:
    conn = sqlite3.connect(RULES_DB)
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS rules")
    cur.execute(
        """
        CREATE TABLE rules (
            rule_id INTEGER PRIMARY KEY,
            condition TEXT NOT NULL,
            adaptation TEXT NOT NULL,
            description TEXT
        )
        """
    )

    rules = [
        (
            "experience=Beginner AND time_available<=60",
            "max_difficulty=easy;max_distance=5;max_elevation=200",
            "Beginner with limited time: easy, short trails",
        ),
        (
            "experience=Beginner AND weather=rainy",
            "max_difficulty=easy;landscape_preference=forest;avoid_risky=true",
            "Beginner in bad weather: safe forest trails",
        ),
        (
            "experience=Advanced AND weather=sunny AND time_available>=120",
            "min_difficulty=hard;min_distance=10;prefer_peaks=true",
            "Advanced hiker, great weather: challenging peaks",
        ),
        (
            "device=mobile",
            "display_mode=compact;max_trails=5",
            "Mobile device: compact display, fewer trails",
        ),
        (
            "connection=weak",
            "display_mode=text_only;hide_images=true",
            "Weak connection: text-only layout",
        ),
        (
            "persistence_score<=0.5 AND time_available<1440",
            "max_difficulty=medium;prefer_short=true;max_distance=8",
            "Low persistence: shorter, easier trails (only for short trips)",
        ),
        (
            "landscape_preference CONTAINS lake",
            "landscape_filter=lake",
            "User prefers lakes: filter for lake trails",
        ),
        (
            "time_available<=45 AND time_available>0",
            "max_duration=45;max_distance=6",
            "Limited time: short trails under 45 min",
        ),
        (
            "weather=storm_risk",
            "avoid_risky=true;max_elevation=500",
            "Storm risk: avoid dangerous high-elevation trails",
        ),
        (
            "season=winter",
            "avoid_closed=true;prefer_safe=true",
            "Winter: avoid closed trails, prefer safe routes",
        ),
    ]
    cur.executemany("INSERT INTO rules (condition, adaptation, description) VALUES (?, ?, ?)", rules)
    conn.commit()
    conn.close()
    print("rules.db initialized with adaptive ruleset")


def seed_users(example_trails: List[dict], use_reference: bool = False) -> None:
    conn = sqlite3.connect(USERS_DB)
    cur = conn.cursor()
    for table in ["users", "preferences", "performance", "completed_trails", "user_profiles"]:
        cur.execute(f"DROP TABLE IF EXISTS {table}")

    cur.execute(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT,
            experience TEXT,
            fitness_level TEXT,
            fear_of_heights INTEGER,
            health_constraints TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            preference TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE performance (
            user_id INTEGER PRIMARY KEY,
            trails_completed INTEGER,
            avg_difficulty_completed REAL,
            persistence_score REAL,
            exploration_level REAL,
            avg_completion_time REAL,
            activity_frequency INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE completed_trails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            trail_id TEXT,
            completion_date TEXT,
            actual_duration INTEGER,
            rating INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE user_profiles (
            user_id INTEGER PRIMARY KEY,
            primary_profile TEXT,
            profile_scores TEXT,
            last_updated TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )

    users = [
        (101, "Alice", "Advanced", "High", 0, None),
        (102, "Bob", "Beginner", "Medium", 1, None),
        (103, "Carol", "Intermediate", "High", 0, "Knee issues"),
        (104, "David", "Beginner", "Low", 1, "Back pain"),
        (105, "Emma", "Advanced", "High", 0, None),
        (106, "Frank", "Intermediate", "Medium", 0, "Asthma"),
        (107, "Grace", "Beginner", "Low", 0, None),
        (108, "Henry", "Advanced", "Medium", 1, None),
        (109, "Iris", "Intermediate", "Low", 0, "Knee issues"),
        (110, "Jack", "Beginner", "High", 1, None),
        (111, "Kate", "Advanced", "High", 0, None),
        (112, "Liam", "Intermediate", "Medium", 0, None),
        (113, "Mia", "Beginner", "Medium", 0, "Heart condition"),
        (114, "Noah", "Advanced", "High", 0, None),
        (115, "Olivia", "Intermediate", "High", 1, None),
    ]
    cur.executemany(
        "INSERT INTO users (id, name, experience, fitness_level, fear_of_heights, health_constraints) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        users,
    )

    preferences = [
        (101, "lake"),
        (101, "peaks"),
        (102, "forest"),
        (102, "river"),
        (103, "lake"),
        (103, "mountain"),
        (104, "forest"),
        (104, "urban"),
        (105, "peaks"),
        (105, "alpine"),
        (105, "mountain"),
        (106, "lake"),
        (106, "forest"),
        (107, "river"),
        (107, "forest"),
        (108, "peaks"),
        (108, "mountain"),
        (109, "lake"),
        (109, "meadow"),
        (110, "forest"),
        (110, "river"),
        (111, "peaks"),
        (111, "alpine"),
        (111, "glacier"),
        (112, "lake"),
        (112, "mountain"),
        (113, "urban"),
        (113, "forest"),
        (114, "peaks"),
        (114, "alpine"),
        (114, "mountain"),
        (115, "lake"),
        (115, "peaks"),
    ]
    cur.executemany("INSERT INTO preferences (user_id, preference) VALUES (?, ?)", preferences)

    performance = [
        (101, 15, 7.5, 0.9, 0.8, 120, 8),
        (102, 3, 3.0, 0.4, 0.6, 45, 2),
        (103, 8, 5.5, 0.7, 0.7, 90, 5),
        (104, 2, 2.0, 0.3, 0.4, 30, 1),
        (105, 20, 8.5, 0.95, 0.9, 150, 10),
        (106, 6, 4.5, 0.6, 0.65, 75, 4),
        (107, 1, 2.5, 0.35, 0.5, 35, 1),
        (108, 12, 7.0, 0.85, 0.75, 110, 7),
        (109, 4, 3.5, 0.45, 0.55, 50, 3),
        (110, 2, 3.5, 0.5, 0.6, 40, 2),
        (111, 18, 8.0, 0.92, 0.85, 140, 9),
        (112, 7, 5.0, 0.65, 0.7, 85, 5),
        (113, 1, 2.0, 0.3, 0.45, 25, 1),
        (114, 22, 9.0, 0.98, 0.95, 160, 12),
        (115, 9, 6.0, 0.75, 0.75, 95, 6),
    ]
    cur.executemany(
        "INSERT INTO performance (user_id, trails_completed, avg_difficulty_completed, persistence_score, "
        "exploration_level, avg_completion_time, activity_frequency) VALUES (?, ?, ?, ?, ?, ?, ?)",
        performance,
    )

    # Use diverse trail selection to trigger different user profiles
    from backend.diversify_profiles import create_diverse_completed_trails
    from backend.db import _insert_completed_trail_sql
    
    # Check for reference JSON file
    completed_trails_ref_path = BASE_DIR.parent / "data" / "seed" / "completed_trails_reference.json"
    
    if use_reference and completed_trails_ref_path.exists():
        # Load from reference JSON for reproducibility
        print("Loading completed trails from reference JSON for reproducibility...")
        with open(completed_trails_ref_path, "r", encoding="utf-8") as f:
            completed_trails_data = json.load(f)
        # Convert to tuples for compatibility
        completed_trails = [
            (ct["user_id"], ct["trail_id"], ct["completion_date"], 
             ct["actual_duration"], ct["rating"])
            for ct in completed_trails_data
        ]
    else:
        # Generate dynamically (current behavior)
        completed_trails = create_diverse_completed_trails(example_trails)
    
    # Insert completed trails using shared function to avoid code duplication
    # Pass existing connection for efficiency (single commit at the end)
    for user_id, trail_id, completion_date, actual_duration, rating in completed_trails:
        _insert_completed_trail_sql(user_id, trail_id, completion_date, actual_duration, rating, conn=conn)

    conn.commit()
    conn.close()
    
    # Recalculate profiles for all users after seeding trails
    # This is done once at the end for efficiency (instead of per-trail)
    print("Calculating user profiles...")
    from backend.user_profiling import UserProfiler
    from backend.db import update_user_profile, get_all_users
    
    profiler = UserProfiler()
    # Get all users (already includes user IDs)
    users = get_all_users()
    user_ids = [user["id"] for user in users]
    
    for user_id in user_ids:
        try:
            primary_profile, scores = profiler.detect_profile(user_id)
            if primary_profile:
                update_user_profile(user_id, primary_profile, scores)
        except Exception as e:
            # Don't fail if profiling fails for one user
            print(f"Warning: Could not calculate profile for user {user_id}: {e}")
    
    print("users.db initialized with demo hikers and contextual history")


def seed_trails(limit: int = DEFAULT_TRAIL_LIMIT, use_reference: bool = False) -> List[dict]:
    """
    Load trails from shapefile or reference JSON.
    
    Args:
        limit: Maximum number of trails to load (ignored if use_reference=True)
        use_reference: If True, load from trails_reference.json instead of shapefile
    
    Returns:
        List of trail dictionaries
    """
    # Check for reference JSON file
    reference_path = BASE_DIR.parent / "data" / "seed" / "trails_reference.json"
    
    if use_reference and reference_path.exists():
        # Load from reference JSON for reproducibility
        print("Loading trails from reference JSON for reproducibility...")
        with open(reference_path, "r", encoding="utf-8") as f:
            trails = json.load(f)
        print(f"Loaded {len(trails)} trails from reference")
        return trails
    
    # Load trails from multiple regions for variety
    # This ensures diverse trail types for better user profile detection
    from data_pipeline.alps_trails_loader import load_french_trails
    
    # Load trails from multiple regions, distributing the limit across them
    # Focus on regions that offer different characteristics:
    # - Mountains: french_alps, pyrenees, jura, vosges
    # - Diverse landscapes: provence, massif_central
    selected_regions = [
        "french_alps",  # High mountains, peaks, glaciers
        "pyrenees",     # Mountain range, diverse
        "massif_central",  # Volcanic, plateaus
        "jura",         # Forested mountains
        "provence",     # Mediterranean landscapes
    ]
    
    # Load all selected regions together, with a limit per region to ensure diversity
    # Increase limit per region to get more variety
    limit_per_region = max(15, limit // len(selected_regions))
    
    trails = load_french_trails(
        regions=selected_regions,
        limit_per_region=limit_per_region,
        total_limit=limit
    )
    
    if not trails:
        raise RuntimeError("No trails extracted from shapefile. Ensure the dataset is present locally.")
    
    # Print summary
    region_counts = {}
    for trail in trails:
        region = trail.get("region", "unknown")
        region_counts[region] = region_counts.get(region, 0) + 1
    print(f"Loaded {len(trails)} trails from {len(region_counts)} regions:")
    for region, count in sorted(region_counts.items()):
        print(f"  {region}: {count} trails")

    conn = sqlite3.connect(TRAILS_DB)
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS trails")
    cur.execute(
        """
        CREATE TABLE trails (
            trail_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            difficulty REAL,
            distance REAL,
            duration INTEGER,
            elevation_gain INTEGER,
            trail_type TEXT,
            landscapes TEXT,
            popularity REAL,
            safety_risks TEXT,
            accessibility TEXT,
            closed_seasons TEXT,
            latitude REAL,
            longitude REAL,
            coordinates TEXT,
            region TEXT,
            source TEXT,
            is_real INTEGER DEFAULT 1,
            elevation_profile TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        """
    )

    now = datetime.now(timezone.utc).isoformat()
    for trail in trails:
        # Ensure all fields are non-null with defaults
        cur.execute(
            """
            INSERT INTO trails (
                trail_id, name, description, difficulty, distance, duration, elevation_gain,
                trail_type, landscapes, popularity, safety_risks, accessibility, closed_seasons,
                latitude, longitude, coordinates, region, source, is_real, elevation_profile,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                trail.get("trail_id") or f"trail_{len(trails)}",
                trail.get("name") or "Unnamed Trail",
                trail.get("description") or "Hiking trail",
                float(trail.get("difficulty", 5.0)),
                float(trail.get("distance", 5.0)),
                int(trail.get("duration", 120)),
                int(trail.get("elevation_gain", 0)),
                trail.get("trail_type") or "one_way",
                trail.get("landscapes") or "alpine",
                float(trail.get("popularity", 6.0)),
                trail.get("safety_risks") or "none",
                trail.get("accessibility") or "",
                trail.get("closed_seasons") or "",
                float(trail.get("latitude", 0.0)),
                float(trail.get("longitude", 0.0)),
                trail.get("coordinates") or json.dumps({"type": "LineString", "coordinates": []}),
                trail.get("region") or "unknown",
                trail.get("source") or "french_osm_shapefile",
                trail.get("is_real", 1),
                json.dumps(trail.get("elevation_profile", [])),
                now,
                now,
            ),
        )

    conn.commit()
    conn.close()
    print(f"trails.db initialized with {len(trails)} real French Alps itineraries")
    return trails


def main() -> None:
    """Main function to initialize databases."""
    parser = argparse.ArgumentParser(description="Initialize hiking trail databases")
    parser.add_argument(
        "--use-reference",
        action="store_true",
        help="Use reference JSON files for reproducible data generation"
    )
    args = parser.parse_args()
    
    print("Initializing adaptive hiking datasets...")
    if args.use_reference:
        print("Mode: Using reference data for reproducibility")
    else:
        print("Mode: Generating fresh data from shapefile")
    
    trail_records = seed_trails(use_reference=args.use_reference)
    seed_rules()
    seed_users(trail_records, use_reference=args.use_reference)
    print("Initialization complete.")


if __name__ == "__main__":
    main()
