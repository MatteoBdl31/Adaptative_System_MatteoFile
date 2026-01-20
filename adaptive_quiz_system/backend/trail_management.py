# -*- coding: utf-8 -*-
"""
Trail management service for handling saved, started, and completed trails.
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from backend.db import USERS_DB, _ensure_new_tables

_ensure_new_tables()


def save_trail(user_id: int, trail_id: str, notes: Optional[str] = None) -> bool:
    """
    Save a trail for a user.
    
    Args:
        user_id: User ID
        trail_id: Trail ID
        notes: Optional notes about the trail
    
    Returns:
        True if saved successfully, False if already saved
    """
    conn = sqlite3.connect(USERS_DB)
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO saved_trails (user_id, trail_id, saved_date, notes)
            VALUES (?, ?, ?, ?)
        """, (user_id, trail_id, datetime.now().isoformat(), notes))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Trail already saved
        return False
    finally:
        conn.close()


def unsave_trail(user_id: int, trail_id: str) -> bool:
    """
    Remove a saved trail for a user.
    
    Args:
        user_id: User ID
        trail_id: Trail ID
    
    Returns:
        True if removed successfully, False if not found
    """
    conn = sqlite3.connect(USERS_DB)
    cur = conn.cursor()
    cur.execute("""
        DELETE FROM saved_trails
        WHERE user_id = ? AND trail_id = ?
    """, (user_id, trail_id))
    deleted = cur.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def start_trail(user_id: int, trail_id: str) -> bool:
    """
    Mark a trail as started for a user.
    
    Args:
        user_id: User ID
        trail_id: Trail ID
    
    Returns:
        True if started successfully, False if already started
    """
    conn = sqlite3.connect(USERS_DB)
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO started_trails (user_id, trail_id, start_date, progress_percentage)
            VALUES (?, ?, ?, 0.0)
        """, (user_id, trail_id, datetime.now().isoformat()))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Check if already started
        cur.execute("SELECT id FROM started_trails WHERE user_id = ? AND trail_id = ?", (user_id, trail_id))
        return cur.fetchone() is not None
    finally:
        conn.close()


def update_trail_progress(
    user_id: int,
    trail_id: str,
    position: Optional[Dict] = None,
    progress_percentage: Optional[float] = None,
    pause_points: Optional[List[Dict]] = None
) -> bool:
    """
    Update progress for a started trail.
    
    Args:
        user_id: User ID
        trail_id: Trail ID
        position: Current position dict with lat, lon, timestamp
        progress_percentage: Progress percentage (0-100)
        pause_points: List of pause point dicts
    
    Returns:
        True if updated successfully, False if trail not started
    """
    conn = sqlite3.connect(USERS_DB)
    cur = conn.cursor()
    
    updates = []
    params = []
    
    if position:
        updates.append("last_position = ?")
        params.append(json.dumps(position))
    
    if progress_percentage is not None:
        updates.append("progress_percentage = ?")
        params.append(progress_percentage)
    
    if pause_points:
        updates.append("pause_points = ?")
        params.append(json.dumps(pause_points))
    
    if not updates:
        conn.close()
        return False
    
    params.extend([user_id, trail_id])
    
    cur.execute(f"""
        UPDATE started_trails
        SET {', '.join(updates)}
        WHERE user_id = ? AND trail_id = ?
    """, params)
    
    updated = cur.rowcount > 0
    conn.commit()
    conn.close()
    return updated


def complete_started_trail(
    user_id: int, 
    trail_id: str, 
    actual_duration: Optional[float] = None,
    rating: Optional[float] = None
) -> Tuple[bool, Optional[int]]:
    """
    Mark a started trail as completed.
    Moves the trail from started_trails to completed_trails.
    
    Args:
        user_id: User ID
        trail_id: Trail ID
        actual_duration: Optional duration in minutes
        rating: Optional rating (1-5)
    
    Returns:
        (success: bool, completed_trail_id: Optional[int])
    """
    from backend.db import _insert_completed_trail_sql
    
    conn = sqlite3.connect(USERS_DB)
    cur = conn.cursor()
    
    try:
        # Get the started trail info
        cur.execute("""
            SELECT start_date, progress_percentage
            FROM started_trails
            WHERE user_id = ? AND trail_id = ?
        """, (user_id, trail_id))
        
        started_trail = cur.fetchone()
        if not started_trail:
            conn.close()
            return (False, None)
        
        # Calculate duration if not provided (estimate based on start date)
        if actual_duration is None:
            start_date = datetime.fromisoformat(started_trail[0])
            time_elapsed = (datetime.now() - start_date).total_seconds() / 60  # minutes
            actual_duration = max(30, time_elapsed)  # Minimum 30 minutes
        
        # Default rating if not provided
        if rating is None:
            rating = 4.0  # Default rating
        
        # Remove from started_trails first
        cur.execute("""
            DELETE FROM started_trails
            WHERE user_id = ? AND trail_id = ?
        """, (user_id, trail_id))
        
        # Record completion (insert into completed_trails)
        completion_date = datetime.now().isoformat()
        cur.execute("""
            INSERT INTO completed_trails (user_id, trail_id, completion_date, actual_duration, rating)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, trail_id, completion_date, actual_duration, rating))
        completed_trail_id = cur.lastrowid
        
        conn.commit()
        conn.close()
        
        # Update user profile
        try:
            from backend.user_profiling import UserProfiler
            from backend.db import update_user_profile
            profiler = UserProfiler()
            primary_profile, scores = profiler.detect_profile(user_id)
            if primary_profile:
                update_user_profile(user_id, primary_profile, scores)
        except Exception as e:
            print(f"Warning: Could not update user profile: {e}")
        
        return (True, completed_trail_id)
        
    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"Error completing trail: {e}")
        return (False, None)


def get_user_trails(user_id: int) -> Dict[str, List[Dict]]:
    """
    Get all trails for a user (saved, started, completed).
    
    Args:
        user_id: User ID
    
    Returns:
        {
            "saved": List[Dict],
            "started": List[Dict],
            "completed": List[Dict]
        }
    """
    conn = sqlite3.connect(USERS_DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Get saved trails
    cur.execute("""
        SELECT trail_id, saved_date, notes
        FROM saved_trails
        WHERE user_id = ?
        ORDER BY saved_date DESC
    """, (user_id,))
    saved = [dict(row) for row in cur.fetchall()]
    
    # Get started trails
    cur.execute("""
        SELECT trail_id, start_date, last_position, progress_percentage, 
               pause_points, estimated_completion_date
        FROM started_trails
        WHERE user_id = ?
        ORDER BY start_date DESC
    """, (user_id,))
    started = []
    for row in cur.fetchall():
        trail = dict(row)
        if trail.get("last_position"):
            try:
                trail["last_position"] = json.loads(trail["last_position"])
            except:
                trail["last_position"] = None
        if trail.get("pause_points"):
            try:
                trail["pause_points"] = json.loads(trail["pause_points"])
            except:
                trail["pause_points"] = []
        started.append(trail)
    
    # Get completed trails
    cur.execute("""
        SELECT id, trail_id, completion_date, actual_duration, rating,
               avg_heart_rate, max_heart_rate, avg_speed, max_speed,
               total_calories, uploaded_data_id
        FROM completed_trails
        WHERE user_id = ?
        ORDER BY completion_date DESC
    """, (user_id,))
    completed = [dict(row) for row in cur.fetchall()]
    
    conn.close()
    
    return {
        "saved": saved,
        "started": started,
        "completed": completed
    }


def get_saved_trails(user_id: int) -> List[Dict]:
    """Get saved trails for a user."""
    trails = get_user_trails(user_id)
    return trails["saved"]


def get_started_trails(user_id: int) -> List[Dict]:
    """Get started trails for a user."""
    trails = get_user_trails(user_id)
    return trails["started"]


def is_trail_saved(user_id: int, trail_id: str) -> bool:
    """Check if a trail is saved by a user."""
    conn = sqlite3.connect(USERS_DB)
    cur = conn.cursor()
    cur.execute("""
        SELECT id FROM saved_trails
        WHERE user_id = ? AND trail_id = ?
    """, (user_id, trail_id))
    result = cur.fetchone() is not None
    conn.close()
    return result


def is_trail_started(user_id: int, trail_id: str) -> bool:
    """Check if a trail is started by a user."""
    conn = sqlite3.connect(USERS_DB)
    cur = conn.cursor()
    cur.execute("""
        SELECT id FROM started_trails
        WHERE user_id = ? AND trail_id = ?
    """, (user_id, trail_id))
    result = cur.fetchone() is not None
    conn.close()
    return result
