# -*- coding: utf-8 -*-

import sqlite3
import json
import os
<<<<<<< HEAD
from datetime import datetime
=======
>>>>>>> d04b8f65898e6e31c37e1228d779449922fdd635

BASE_DIR = os.path.dirname(__file__)
USERS_DB = os.path.join(BASE_DIR, "users.db")
RULES_DB = os.path.join(BASE_DIR, "rules.db")
<<<<<<< HEAD
TRAILS_DB = os.path.join(BASE_DIR, "trails.db")
=======
QUIZZES_DIR = os.path.join(BASE_DIR, "quizzes")
>>>>>>> d04b8f65898e6e31c37e1228d779449922fdd635

# --- Users ---
def get_all_users():
    conn = sqlite3.connect(USERS_DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM users")
    users = [dict(row) for row in cur.fetchall()]
<<<<<<< HEAD
=======
    # ajouter préférences et performance
>>>>>>> d04b8f65898e6e31c37e1228d779449922fdd635
    for user in users:
        cur.execute("SELECT preference FROM preferences WHERE user_id=?", (user["id"],))
        user["preferences"] = [row["preference"] for row in cur.fetchall()]
        cur.execute("SELECT * FROM performance WHERE user_id=?", (user["id"],))
        perf = cur.fetchone()
        user["performance"] = dict(perf) if perf else {}
<<<<<<< HEAD
        # Get completed trails
        cur.execute("SELECT trail_id, completion_date, rating FROM completed_trails WHERE user_id=? ORDER BY completion_date DESC", (user["id"],))
        user["completed_trails"] = [dict(row) for row in cur.fetchall()]
=======
>>>>>>> d04b8f65898e6e31c37e1228d779449922fdd635
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
<<<<<<< HEAD
    # Get completed trails
    cur.execute("SELECT trail_id, completion_date, rating FROM completed_trails WHERE user_id=? ORDER BY completion_date DESC", (user_id,))
    user["completed_trails"] = [dict(row) for row in cur.fetchall()]
    conn.close()
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
    """Record when a user completes a trail"""
    conn = sqlite3.connect(USERS_DB)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO completed_trails (user_id, trail_id, completion_date, actual_duration, rating)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, trail_id, datetime.now().isoformat(), actual_duration, rating))
    conn.commit()
    conn.close()

=======
    conn.close()
    return user

>>>>>>> d04b8f65898e6e31c37e1228d779449922fdd635
# --- Rules ---
def get_rules():
    conn = sqlite3.connect(RULES_DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM rules")
    rules = [dict(row) for row in cur.fetchall()]
    conn.close()
    return rules

<<<<<<< HEAD
# --- Trails ---
def get_all_trails():
    conn = sqlite3.connect(TRAILS_DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM trails")
    trails = [dict(row) for row in cur.fetchall()]
    conn.close()
    return trails

def get_trail(trail_id):
    conn = sqlite3.connect(TRAILS_DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM trails WHERE trail_id=?", (trail_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

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
    trails = [dict(row) for row in cur.fetchall()]
    conn.close()
    return trails
=======
# --- Quiz files ---
def get_all_quizzes():
    return [f for f in os.listdir(QUIZZES_DIR) if f.endswith(".json")]

def load_quiz(quiz_file):
    path = os.path.join(QUIZZES_DIR, quiz_file)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
>>>>>>> d04b8f65898e6e31c37e1228d779449922fdd635
