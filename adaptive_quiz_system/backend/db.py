# -*- coding: utf-8 -*-

import sqlite3
import json
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(__file__)
USERS_DB = os.path.join(BASE_DIR, "users.db")
RULES_DB = os.path.join(BASE_DIR, "rules.db")
TRAILS_DB = os.path.join(BASE_DIR, "trails.db")


def _normalize_trail_row(row):
    if not row:
        return None
    trail = dict(row)
    for field in ("coordinates", "elevation_profile"):
        value = trail.get(field)
        if value:
            try:
                trail[field] = json.loads(value) if isinstance(value, str) else value
            except (TypeError, json.JSONDecodeError):
                trail[field] = value
        else:
            trail[field] = None
    return trail

# --- Users ---
def get_all_users():
    conn = sqlite3.connect(USERS_DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM users")
    users = [dict(row) for row in cur.fetchall()]
    for user in users:
        cur.execute("SELECT preference FROM preferences WHERE user_id=?", (user["id"],))
        user["preferences"] = [row["preference"] for row in cur.fetchall()]
        cur.execute("SELECT * FROM performance WHERE user_id=?", (user["id"],))
        perf = cur.fetchone()
        user["performance"] = dict(perf) if perf else {}
        # Get completed trails
        cur.execute("SELECT trail_id, completion_date, rating FROM completed_trails WHERE user_id=? ORDER BY completion_date DESC", (user["id"],))
        user["completed_trails"] = [dict(row) for row in cur.fetchall()]
        
        # Get user profile
        profile = get_user_profile(user["id"])
        if profile:
            user["detected_profile"] = profile["primary_profile"]
            user["profile_scores"] = profile["profile_scores"]
        else:
            # Calculate on-the-fly if not stored (but only if user has enough trails)
            if len(user.get("completed_trails", [])) >= 3:
                try:
                    from backend.user_profiling import UserProfiler
                    profiler = UserProfiler()
                    primary_profile, scores = profiler.detect_profile(user["id"])
                    user["detected_profile"] = primary_profile
                    user["profile_scores"] = scores
                except Exception:
                    user["detected_profile"] = None
                    user["profile_scores"] = {}
            else:
                user["detected_profile"] = None
                user["profile_scores"] = {}
    conn.close()
    return users

def get_user(user_id):
    conn = sqlite3.connect(USERS_DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id=?", (user_id,))
    row = cur.fetchone()
    if not row:
        return None
    user = dict(row)
    cur.execute("SELECT preference FROM preferences WHERE user_id=?", (user_id,))
    user["preferences"] = [row["preference"] for row in cur.fetchall()]
    cur.execute("SELECT * FROM performance WHERE user_id=?", (user_id,))
    perf = cur.fetchone()
    user["performance"] = dict(perf) if perf else {}
    # Get completed trails
    cur.execute("SELECT trail_id, completion_date, rating FROM completed_trails WHERE user_id=? ORDER BY completion_date DESC", (user_id,))
    user["completed_trails"] = [dict(row) for row in cur.fetchall()]
    conn.close()
    
    # Get user profile
    profile = get_user_profile(user_id)
    if profile:
        user["detected_profile"] = profile["primary_profile"]
        user["profile_scores"] = profile["profile_scores"]
    else:
        # Calculate on-the-fly if not stored (but only if user has enough trails)
        if len(user.get("completed_trails", [])) >= 3:
            try:
                from backend.user_profiling import UserProfiler
                profiler = UserProfiler()
                primary_profile, scores = profiler.detect_profile(user_id)
                user["detected_profile"] = primary_profile
                user["profile_scores"] = scores
            except Exception:
                user["detected_profile"] = None
                user["profile_scores"] = {}
        else:
            user["detected_profile"] = None
            user["profile_scores"] = {}
    
    return user

def _insert_completed_trail_sql(user_id, trail_id, completion_date, actual_duration, rating, 
                                conn=None, predicted_duration=None, predicted_avg_heart_rate=None,
                                predicted_max_heart_rate=None, predicted_avg_speed=None,
                                predicted_max_speed=None, predicted_calories=None,
                                predicted_profile_category=None):
    """
    Helper function to insert a completed trail into the database.
    This is the shared SQL insertion logic used by both record_trail_completion()
    and seed_users() to avoid code duplication.
    
    Args:
        user_id: User ID
        trail_id: Trail ID
        completion_date: ISO format date string
        actual_duration: Duration in minutes
        rating: Rating (1-5)
        conn: Optional existing database connection. If None, creates and closes a new one.
        predicted_duration: Optional predicted duration in minutes
        predicted_avg_heart_rate: Optional predicted average heart rate
        predicted_max_heart_rate: Optional predicted max heart rate
        predicted_avg_speed: Optional predicted average speed
        predicted_max_speed: Optional predicted max speed
        predicted_calories: Optional predicted calories
        predicted_profile_category: Optional predicted profile category
    
    Returns:
        None
    """
    should_close = False
    if conn is None:
        conn = sqlite3.connect(USERS_DB)
        should_close = True
    
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO completed_trails (user_id, trail_id, completion_date, actual_duration, rating,
                                     predicted_duration, predicted_avg_heart_rate, predicted_max_heart_rate,
                                     predicted_avg_speed, predicted_max_speed, predicted_calories,
                                     predicted_profile_category)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, trail_id, completion_date, actual_duration, rating,
          predicted_duration, predicted_avg_heart_rate, predicted_max_heart_rate,
          predicted_avg_speed, predicted_max_speed, predicted_calories,
          predicted_profile_category))
    
    if should_close:
        conn.commit()
        conn.close()

def record_trail_completion(user_id, trail_id, actual_duration, rating, 
                           predicted_duration=None, predicted_avg_heart_rate=None,
                           predicted_max_heart_rate=None, predicted_avg_speed=None,
                           predicted_max_speed=None, predicted_calories=None,
                           predicted_profile_category=None):
    """
    Record when a user completes a trail and update profile.
    
    Args:
        user_id: User ID
        trail_id: Trail ID
        actual_duration: Duration in minutes
        rating: Rating (1-5)
        predicted_duration: Optional predicted duration in minutes
        predicted_avg_heart_rate: Optional predicted average heart rate
        predicted_max_heart_rate: Optional predicted max heart rate
        predicted_avg_speed: Optional predicted average speed
        predicted_max_speed: Optional predicted max speed
        predicted_calories: Optional predicted calories
        predicted_profile_category: Optional predicted profile category
    """
    # Use shared SQL insertion function
    _insert_completed_trail_sql(
        user_id, 
        trail_id, 
        datetime.now().isoformat(), 
        actual_duration, 
        rating,
        predicted_duration=predicted_duration,
        predicted_avg_heart_rate=predicted_avg_heart_rate,
        predicted_max_heart_rate=predicted_max_heart_rate,
        predicted_avg_speed=predicted_avg_speed,
        predicted_max_speed=predicted_max_speed,
        predicted_calories=predicted_calories,
        predicted_profile_category=predicted_profile_category
    )
    
    # Recalculate user profile
    try:
        from backend.user_profiling import UserProfiler
        profiler = UserProfiler()
        primary_profile, scores = profiler.detect_profile(user_id)
        if primary_profile:
            update_user_profile(user_id, primary_profile, scores)
    except Exception as e:
        # Don't fail if profiling fails
        print(f"Warning: Could not update user profile for user {user_id}: {e}")

def _ensure_user_profiles_table():
    """Ensure user_profiles table exists (for migration compatibility)."""
    conn = sqlite3.connect(USERS_DB)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_profiles (
            user_id INTEGER PRIMARY KEY,
            primary_profile TEXT,
            profile_scores TEXT,
            last_updated TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()

def update_user_profile(user_id: int, primary_profile: str, profile_scores: dict):
    """Update user profile in database."""
    _ensure_user_profiles_table()
    conn = sqlite3.connect(USERS_DB)
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO user_profiles 
        (user_id, primary_profile, profile_scores, last_updated)
        VALUES (?, ?, ?, ?)
    """, (user_id, primary_profile, json.dumps(profile_scores), 
          datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_user_profile(user_id: int):
    """Get user profile from database."""
    _ensure_user_profiles_table()
    conn = sqlite3.connect(USERS_DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM user_profiles WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        profile = dict(row)
        profile["profile_scores"] = json.loads(profile["profile_scores"])
        return profile
    return None

def _ensure_new_tables():
    """Ensure new tables exist (for migration compatibility)."""
    conn = sqlite3.connect(USERS_DB)
    cur = conn.cursor()
    
    # Check and extend completed_trails if needed
    cur.execute("PRAGMA table_info(completed_trails)")
    columns = [row[1] for row in cur.fetchall()]
    if "avg_heart_rate" not in columns:
        cur.execute("ALTER TABLE completed_trails ADD COLUMN avg_heart_rate INTEGER")
    if "max_heart_rate" not in columns:
        cur.execute("ALTER TABLE completed_trails ADD COLUMN max_heart_rate INTEGER")
    if "avg_speed" not in columns:
        cur.execute("ALTER TABLE completed_trails ADD COLUMN avg_speed REAL")
    if "max_speed" not in columns:
        cur.execute("ALTER TABLE completed_trails ADD COLUMN max_speed REAL")
    if "total_calories" not in columns:
        cur.execute("ALTER TABLE completed_trails ADD COLUMN total_calories INTEGER")
    if "uploaded_data_id" not in columns:
        cur.execute("ALTER TABLE completed_trails ADD COLUMN uploaded_data_id INTEGER")
    if "difficulty_rating" not in columns:
        cur.execute("ALTER TABLE completed_trails ADD COLUMN difficulty_rating INTEGER")
    # Add predicted metrics columns for future profile comparison
    if "predicted_duration" not in columns:
        cur.execute("ALTER TABLE completed_trails ADD COLUMN predicted_duration INTEGER")
    if "predicted_avg_heart_rate" not in columns:
        cur.execute("ALTER TABLE completed_trails ADD COLUMN predicted_avg_heart_rate INTEGER")
    if "predicted_max_heart_rate" not in columns:
        cur.execute("ALTER TABLE completed_trails ADD COLUMN predicted_max_heart_rate INTEGER")
    if "predicted_avg_speed" not in columns:
        cur.execute("ALTER TABLE completed_trails ADD COLUMN predicted_avg_speed REAL")
    if "predicted_max_speed" not in columns:
        cur.execute("ALTER TABLE completed_trails ADD COLUMN predicted_max_speed REAL")
    if "predicted_calories" not in columns:
        cur.execute("ALTER TABLE completed_trails ADD COLUMN predicted_calories INTEGER")
    if "predicted_profile_category" not in columns:
        cur.execute("ALTER TABLE completed_trails ADD COLUMN predicted_profile_category TEXT")
    
    # Create saved_trails table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS saved_trails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            trail_id TEXT,
            saved_date TEXT,
            notes TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id),
            UNIQUE(user_id, trail_id)
        )
    """)
    
    # Create started_trails table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS started_trails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            trail_id TEXT,
            start_date TEXT,
            last_position TEXT,
            progress_percentage REAL,
            pause_points TEXT,
            estimated_completion_date TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    
    # Create trail_performance_data table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS trail_performance_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            completed_trail_id INTEGER,
            timestamp INTEGER,
            heart_rate INTEGER,
            speed REAL,
            elevation REAL,
            latitude REAL,
            longitude REAL,
            calories INTEGER,
            cadence INTEGER,
            FOREIGN KEY(completed_trail_id) REFERENCES completed_trails(id)
        )
    """)
    
    # Create indexes for trail_performance_data for better query performance
    try:
        cur.execute("CREATE INDEX IF NOT EXISTS idx_trail_perf_completed_trail_id ON trail_performance_data(completed_trail_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_trail_perf_timestamp ON trail_performance_data(completed_trail_id, timestamp)")
    except sqlite3.OperationalError:
        # Indexes might already exist, ignore
        pass
    
    # Create uploaded_trail_data table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS uploaded_trail_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            trail_id TEXT,
            upload_date TEXT,
            original_filename TEXT,
            data_format TEXT,
            raw_data TEXT,
            parsed_data TEXT,
            status TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    
    # Create trail_photos table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS trail_photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            completed_trail_id INTEGER,
            photo_path TEXT,
            upload_date TEXT,
            caption TEXT,
            FOREIGN KEY(completed_trail_id) REFERENCES completed_trails(id)
        )
    """)
    
    # Extend user_profiles table if needed
    cur.execute("PRAGMA table_info(user_profiles)")
    profile_columns = [row[1] for row in cur.fetchall()]
    if "pinned_dashboard" not in profile_columns:
        cur.execute("ALTER TABLE user_profiles ADD COLUMN pinned_dashboard TEXT")
    
    conn.commit()
    conn.close()

# --- Rules ---
def get_rules():
    conn = sqlite3.connect(RULES_DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM rules")
    rules = [dict(row) for row in cur.fetchall()]
    conn.close()
    return rules

# --- Trails ---
def get_all_trails():
    conn = sqlite3.connect(TRAILS_DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM trails")
    trails = [_normalize_trail_row(row) for row in cur.fetchall()]
    conn.close()
    return trails

def get_trail(trail_id):
    conn = sqlite3.connect(TRAILS_DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM trails WHERE trail_id=?", (trail_id,))
    row = cur.fetchone()
    conn.close()
    return _normalize_trail_row(row)

def filter_trails(filters):
    """Filter trails based on criteria"""
    logger.debug(f"Filtering trails with filters: {filters}")
    
    try:
        conn = sqlite3.connect(TRAILS_DB)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        query = "SELECT * FROM trails WHERE 1=1"
        params = []
        
        if filters.get("max_difficulty"):
            query += " AND difficulty <= ?"
            params.append(float(filters["max_difficulty"]))
        if filters.get("min_difficulty"):
            query += " AND difficulty >= ?"
            params.append(float(filters["min_difficulty"]))
        if filters.get("max_distance"):
            query += " AND distance <= ?"
            params.append(float(filters["max_distance"]))
        if filters.get("min_distance"):
            query += " AND distance >= ?"
            params.append(float(filters["min_distance"]))
        if filters.get("max_duration"):
            query += " AND duration <= ?"
            params.append(int(filters["max_duration"]))
        if filters.get("min_duration"):
            query += " AND duration >= ?"
            params.append(int(filters["min_duration"]))
        if filters.get("max_elevation"):
            query += " AND elevation_gain <= ?"
            params.append(int(filters["max_elevation"]))
        if filters.get("landscape_filter"):
            query += " AND landscapes LIKE ?"
            params.append(f"%{filters['landscape_filter']}%")
        if filters.get("avoid_risky"):
            query += " AND (safety_risks = 'none' OR safety_risks = 'low')"
        if filters.get("region"):
            query += " AND region = ?"
            params.append(filters["region"])
        if filters.get("is_real") is not None:
            query += " AND is_real = ?"
            params.append(1 if filters["is_real"] else 0)
        if filters.get("avoid_closed"):
            # This would need season context - for now just filter out trails with closed_seasons
            # In a real implementation, you'd check if current season matches closed_seasons
            pass
        if filters.get("prefer_short"):
            query += " ORDER BY distance ASC"
        elif filters.get("prefer_peaks"):
            query += " AND landscapes LIKE '%peaks%' ORDER BY difficulty DESC"
        else:
            query += " ORDER BY popularity DESC"
        
        logger.debug(f"Executing query: {query[:200]}... with {len(params)} parameters")
        cur.execute(query, params)
        trails = [_normalize_trail_row(row) for row in cur.fetchall()]
        conn.close()
        
        logger.debug(f"Query returned {len(trails)} trails")
        return trails
        
    except Exception as e:
        logger.error(f"Error filtering trails: {e}")
        logger.error(f"Filters were: {filters}")
        # Return empty list on error rather than crashing
        return []
