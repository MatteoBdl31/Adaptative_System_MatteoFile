# -*- coding: utf-8 -*-
from __future__ import annotations

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

from data_pipeline.alps_trails_loader import load_french_alps_trails  # noqa: E402

BASE_DIR = Path(__file__).resolve().parent
USERS_DB = BASE_DIR / "users.db"
RULES_DB = BASE_DIR / "rules.db"
TRAILS_DB = BASE_DIR / "trails.db"
DEFAULT_TRAIL_LIMIT = int(os.getenv("TRAIL_LIMIT", "45"))


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


def seed_users(example_trails: List[dict]) -> None:
    conn = sqlite3.connect(USERS_DB)
    cur = conn.cursor()
    for table in ["users", "preferences", "performance", "completed_trails", "trail_history", "user_profiles"]:
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
        CREATE TABLE trail_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            trail_id TEXT,
            viewed_at TEXT,
            abandoned INTEGER,
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

    available_ids = [trail["trail_id"] for trail in example_trails] or ["placeholder_id"]

    def pick(offset: int) -> str:
        return available_ids[offset % len(available_ids)]

    completed_trails = [
        # User 101 (Alice) - Advanced, High fitness - 4 trails
        (101, pick(0), "2024-01-15", 110, 5),
        (101, pick(1), "2024-01-20", 180, 5),
        (101, pick(2), "2024-02-10", 165, 5),
        (101, pick(3), "2024-02-25", 200, 4),
        # User 102 (Bob) - Beginner, Medium fitness - 3 trails
        (102, pick(4), "2024-01-10", 40, 4),
        (102, pick(5), "2024-01-25", 45, 4),
        (102, pick(6), "2024-02-05", 50, 3),
        # User 103 (Carol) - Intermediate, High fitness - 3 trails
        (103, pick(7), "2024-01-12", 95, 4),
        (103, pick(8), "2024-01-28", 100, 5),
        (103, pick(9), "2024-02-15", 90, 4),
        # User 104 (David) - Beginner, Low fitness - 3 trails
        (104, pick(10), "2024-01-08", 25, 3),
        (104, pick(11), "2024-01-22", 30, 3),
        (104, pick(12), "2024-02-08", 28, 4),
        # User 105 (Emma) - Advanced, High fitness - 5 trails
        (105, pick(13), "2024-01-25", 150, 5),
        (105, pick(14), "2024-01-18", 140, 5),
        (105, pick(15), "2024-02-12", 160, 5),
        (105, pick(16), "2024-02-28", 175, 5),
        (105, pick(0), "2024-03-10", 155, 4),
        # User 106 (Frank) - Intermediate, Medium fitness - 3 trails
        (106, pick(1), "2024-01-11", 70, 4),
        (106, pick(2), "2024-01-27", 75, 4),
        (106, pick(3), "2024-02-14", 68, 5),
        # User 107 (Grace) - Beginner, Low fitness - 3 trails
        (107, pick(4), "2024-01-09", 32, 4),
        (107, pick(5), "2024-01-24", 35, 4),
        (107, pick(6), "2024-02-09", 30, 3),
        # User 108 (Henry) - Advanced, Medium fitness - 4 trails
        (108, pick(7), "2024-01-16", 105, 4),
        (108, pick(8), "2024-02-01", 110, 4),
        (108, pick(9), "2024-02-18", 115, 5),
        (108, pick(10), "2024-03-05", 108, 4),
        # User 109 (Iris) - Intermediate, Low fitness - 3 trails
        (109, pick(11), "2024-01-13", 48, 4),
        (109, pick(12), "2024-01-30", 50, 4),
        (109, pick(13), "2024-02-16", 45, 3),
        # User 110 (Jack) - Beginner, High fitness - 3 trails
        (110, pick(14), "2024-01-14", 38, 4),
        (110, pick(15), "2024-01-29", 42, 4),
        (110, pick(16), "2024-02-17", 40, 5),
        # User 111 (Kate) - Advanced, High fitness - 4 trails
        (111, pick(0), "2024-01-22", 145, 5),
        (111, pick(1), "2024-02-08", 150, 5),
        (111, pick(2), "2024-02-24", 140, 5),
        (111, pick(3), "2024-03-12", 155, 4),
        # User 112 (Liam) - Intermediate, Medium fitness - 3 trails
        (112, pick(4), "2024-01-17", 88, 4),
        (112, pick(5), "2024-02-03", 92, 4),
        (112, pick(6), "2024-02-20", 85, 5),
        # User 113 (Mia) - Beginner, Medium fitness - 3 trails
        (113, pick(7), "2024-01-07", 28, 3),
        (113, pick(8), "2024-01-23", 30, 3),
        (113, pick(9), "2024-02-11", 32, 4),
        # User 114 (Noah) - Advanced, High fitness - 6 trails
        (114, pick(10), "2024-01-24", 155, 5),
        (114, pick(11), "2024-02-09", 160, 5),
        (114, pick(12), "2024-02-26", 165, 5),
        (114, pick(13), "2024-03-14", 170, 5),
        (114, pick(14), "2024-03-28", 158, 4),
        (114, pick(15), "2024-04-10", 162, 5),
        # User 115 (Olivia) - Intermediate, High fitness - 3 trails
        (115, pick(16), "2024-01-19", 92, 4),
        (115, pick(0), "2024-02-06", 95, 5),
        (115, pick(1), "2024-02-22", 90, 4),
    ]
    cur.executemany(
        "INSERT INTO completed_trails (user_id, trail_id, completion_date, actual_duration, rating) "
        "VALUES (?, ?, ?, ?, ?)",
        completed_trails,
    )

    conn.commit()
    conn.close()
    print("users.db initialized with demo hikers and contextual history")


def seed_trails(limit: int = DEFAULT_TRAIL_LIMIT) -> List[dict]:
    trails = load_french_alps_trails(limit=limit)
    if not trails:
        raise RuntimeError("No trails extracted from shapefile. Ensure the dataset is present locally.")

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
                trail.get("trail_id"),
                trail.get("name"),
                trail.get("description"),
                trail.get("difficulty"),
                trail.get("distance"),
                trail.get("duration"),
                trail.get("elevation_gain"),
                trail.get("trail_type"),
                trail.get("landscapes"),
                trail.get("popularity"),
                trail.get("safety_risks"),
                trail.get("accessibility"),
                trail.get("closed_seasons"),
                trail.get("latitude"),
                trail.get("longitude"),
                trail.get("coordinates"),
                trail.get("region"),
                trail.get("source"),
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
    print("Initializing adaptive hiking datasets...")
    trail_records = seed_trails()
    seed_rules()
    seed_users(trail_records)
    print("Initialization complete.")


if __name__ == "__main__":
    main()
