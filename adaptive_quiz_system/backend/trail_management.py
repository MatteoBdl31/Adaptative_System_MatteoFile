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
    Allows multiple starts - does not remove from saved_trails.
    
    Args:
        user_id: User ID
        trail_id: Trail ID
    
    Returns:
        True if started successfully
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
    except Exception as e:
        print(f"Error starting trail: {e}")
        return False
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
    rating: Optional[float] = None,
    difficulty_rating: Optional[int] = None,
    photos: Optional[List[str]] = None,
    uploaded_file_id: Optional[int] = None,
    predicted_duration: Optional[int] = None,
    predicted_avg_heart_rate: Optional[int] = None,
    predicted_max_heart_rate: Optional[int] = None,
    predicted_avg_speed: Optional[float] = None,
    predicted_max_speed: Optional[float] = None,
    predicted_calories: Optional[int] = None,
    predicted_profile_category: Optional[str] = None
) -> Tuple[bool, Optional[int]]:
    """
    Mark a started trail as completed.
    Does NOT remove from started_trails - trail can be completed multiple times.
    
    Args:
        user_id: User ID
        trail_id: Trail ID
        actual_duration: Optional duration in minutes
        rating: Optional rating (1-5)
        difficulty_rating: Optional difficulty rating (1-10)
        photos: Optional list of photo paths
        uploaded_file_id: Optional ID of uploaded file (smartwatch data)
        predicted_duration: Optional predicted duration in minutes
        predicted_avg_heart_rate: Optional predicted average heart rate
        predicted_max_heart_rate: Optional predicted max heart rate
        predicted_avg_speed: Optional predicted average speed
        predicted_max_speed: Optional predicted max speed
        predicted_calories: Optional predicted calories
        predicted_profile_category: Optional predicted profile category
    
    Returns:
        (success: bool, completed_trail_id: Optional[int])
    """
    conn = sqlite3.connect(USERS_DB)
    cur = conn.cursor()
    
    try:
        # Get the started trail info (use the most recent one)
        cur.execute("""
            SELECT start_date, progress_percentage
            FROM started_trails
            WHERE user_id = ? AND trail_id = ?
            ORDER BY start_date DESC
            LIMIT 1
        """, (user_id, trail_id))
        
        started_trail = cur.fetchone()
        
        # Calculate duration if not provided (estimate based on start date)
        if actual_duration is None:
            if started_trail:
                start_date = datetime.fromisoformat(started_trail[0])
                time_elapsed = (datetime.now() - start_date).total_seconds() / 60  # minutes
                actual_duration = max(30, time_elapsed)  # Minimum 30 minutes
            else:
                actual_duration = 60  # Default 1 hour
        
        # Default rating if not provided
        if rating is None:
            rating = 4.0  # Default rating
        
        # Record completion (insert into completed_trails)
        completion_date = datetime.now().isoformat()
        cur.execute("""
            INSERT INTO completed_trails (user_id, trail_id, completion_date, actual_duration, rating, 
                                         difficulty_rating, uploaded_data_id,
                                         predicted_duration, predicted_avg_heart_rate, predicted_max_heart_rate,
                                         predicted_avg_speed, predicted_max_speed, predicted_calories,
                                         predicted_profile_category)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, trail_id, completion_date, actual_duration, rating, difficulty_rating, uploaded_file_id,
              predicted_duration, predicted_avg_heart_rate, predicted_max_heart_rate,
              predicted_avg_speed, predicted_max_speed, predicted_calories,
              predicted_profile_category))
        completed_trail_id = cur.lastrowid
        
        # Remove the specific started_trail record that was completed (most recent one)
        # This allows multiple starts - only the completed one is removed
        if started_trail:
            cur.execute("""
                DELETE FROM started_trails
                WHERE user_id = ? AND trail_id = ? AND start_date = ?
            """, (user_id, trail_id, started_trail[0]))
        
        # Store photos if provided
        if photos:
            for photo_path in photos:
                cur.execute("""
                    INSERT INTO trail_photos (completed_trail_id, photo_path, upload_date)
                    VALUES (?, ?, ?)
                """, (completed_trail_id, photo_path, completion_date))
        
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


def get_trail_statistics(user_id: int, trail_id: str) -> Dict[str, int]:
    """
    Get statistics for a trail (how many times started and completed).
    
    Args:
        user_id: User ID
        trail_id: Trail ID
    
    Returns:
        {
            "start_count": int,
            "completion_count": int
        }
    """
    conn = sqlite3.connect(USERS_DB)
    cur = conn.cursor()
    
    # Count starts
    cur.execute("""
        SELECT COUNT(*) FROM started_trails
        WHERE user_id = ? AND trail_id = ?
    """, (user_id, trail_id))
    start_count = cur.fetchone()[0]
    
    # Count completions
    cur.execute("""
        SELECT COUNT(*) FROM completed_trails
        WHERE user_id = ? AND trail_id = ?
    """, (user_id, trail_id))
    completion_count = cur.fetchone()[0]
    
    conn.close()
    
    return {
        "start_count": start_count,
        "completion_count": completion_count
    }


def get_user_trails(user_id: int) -> Dict[str, List[Dict]]:
    """
    Get all trails for a user (saved, started, completed).
    Includes statistics for saved trails.
    
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
    
    # Get saved trails with statistics
    cur.execute("""
        SELECT trail_id, saved_date, notes
        FROM saved_trails
        WHERE user_id = ?
        ORDER BY saved_date DESC
    """, (user_id,))
    saved = []
    for row in cur.fetchall():
        trail = dict(row)
        # Add statistics
        stats = get_trail_statistics(user_id, trail["trail_id"])
        trail["start_count"] = stats["start_count"]
        trail["completion_count"] = stats["completion_count"]
        saved.append(trail)
    
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
    
    # Get completed trails with photos
    cur.execute("""
        SELECT id, trail_id, completion_date, actual_duration, rating,
               avg_heart_rate, max_heart_rate, avg_speed, max_speed,
               total_calories, uploaded_data_id, difficulty_rating
        FROM completed_trails
        WHERE user_id = ?
        ORDER BY completion_date DESC
    """, (user_id,))
    completed = []
    for row in cur.fetchall():
        trail = dict(row)
        # Ensure rating and difficulty_rating are numbers, not strings
        if trail.get("rating") is not None:
            try:
                trail["rating"] = float(trail["rating"])
            except (ValueError, TypeError):
                trail["rating"] = None
        if trail.get("difficulty_rating") is not None:
            try:
                trail["difficulty_rating"] = int(trail["difficulty_rating"])
            except (ValueError, TypeError):
                trail["difficulty_rating"] = None
        # Get photos for this completion
        cur.execute("""
            SELECT photo_path, caption FROM trail_photos
            WHERE completed_trail_id = ?
            ORDER BY upload_date ASC
        """, (trail["id"],))
        photos = [{"path": p[0], "caption": p[1]} for p in cur.fetchall()]
        trail["photos"] = photos
        completed.append(trail)
    
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
