# -*- coding: utf-8 -*-

import sqlite3
import json
import os
from datetime import datetime

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

def record_trail_view(user_id, trail_id, abandoned=False):
    """Record when a user views a trail"""
    conn = sqlite3.connect(USERS_DB)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO trail_history (user_id, trail_id, viewed_at, abandoned)
        VALUES (?, ?, ?, ?)
    """, (user_id, trail_id, datetime.now().isoformat(), 1 if abandoned else 0))
    conn.commit()
    conn.close()

def record_trail_completion(user_id, trail_id, actual_duration, rating):
    """Record when a user completes a trail and update profile"""
    conn = sqlite3.connect(USERS_DB)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO completed_trails (user_id, trail_id, completion_date, actual_duration, rating)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, trail_id, datetime.now().isoformat(), actual_duration, rating))
    conn.commit()
    conn.close()
    
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
    
    cur.execute(query, params)
    trails = [_normalize_trail_row(row) for row in cur.fetchall()]
    conn.close()
    return trails
