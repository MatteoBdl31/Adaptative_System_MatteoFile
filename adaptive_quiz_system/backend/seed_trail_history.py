#!/usr/bin/env python3
"""
Seed trail history (saved and completed trails) for all users based on their profiles.
Matches trails to user profiles and experience levels.
"""
import sys
import random
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import sqlite3
from backend.db import USERS_DB, get_all_users, get_all_trails, get_trail, get_user_profile
from backend.trail_management import save_trail
from backend.db import _insert_completed_trail_sql
from backend.generate_dummy_fitness_data import generate_time_series_data
from backend.trail_analytics import TrailAnalytics


def match_trails_to_profile(trails, profile_type, experience_level):
    """
    Match trails to a user profile.
    
    Args:
        trails: List of all trails
        profile_type: User profile type
        experience_level: User experience (Beginner, Intermediate, Advanced)
    
    Returns:
        List of matching trail IDs
    """
    matched = []
    
    # Determine difficulty range based on experience
    if experience_level == "Beginner":
        min_difficulty, max_difficulty = 0, 4.0
        max_distance = 6.0
        max_elevation = 400
    elif experience_level == "Intermediate":
        min_difficulty, max_difficulty = 3.0, 6.5
        max_distance = 12.0
        max_elevation = 800
    else:  # Advanced
        min_difficulty, max_difficulty = 5.0, 10.0
        max_distance = 999.0  # No limit
        max_elevation = 9999  # No limit
    
    for trail in trails:
        difficulty = trail.get("difficulty", 5.0)
        distance = trail.get("distance", 5.0)
        elevation_gain = trail.get("elevation_gain", 0)
        landscapes = (trail.get("landscapes") or "").lower()
        trail_type = trail.get("trail_type", "one_way")
        popularity = trail.get("popularity", 7.0)
        safety_risks = (trail.get("safety_risks") or "none").lower()
        region = trail.get("region", "")
        
        # Check basic experience constraints
        if difficulty < min_difficulty or difficulty > max_difficulty:
            continue
        if distance > max_distance:
            continue
        if elevation_gain > max_elevation:
            continue
        
        # Profile-specific matching
        matches = False
        
        if profile_type == "elevation_lover":
            # High elevation gain, high difficulty
            if elevation_gain >= 500 and difficulty >= 6.0:
                matches = True
        
        elif profile_type == "performance_athlete":
            # Long distance, long duration, prefer loops
            if distance >= 8.0 and trail.get("duration", 0) >= 90:
                if trail_type == "loop":
                    matches = True
                elif distance >= 10.0:  # Accept long one-way too
                    matches = True
        
        elif profile_type == "contemplative":
            # Scenic landscapes (lake, peaks, glacier), moderate popularity
            scenic_keywords = ["lake", "peaks", "glacier", "mountain"]
            if any(kw in landscapes for kw in scenic_keywords):
                if 6.0 <= popularity <= 8.0:
                    matches = True
        
        elif profile_type == "casual":
            # Short distance, low difficulty
            if distance <= 5.0 and difficulty <= 4.5:
                matches = True
        
        elif profile_type == "family":
            # Low difficulty, high safety
            if difficulty <= 4.0 and "none" in safety_risks:
                matches = True
        
        elif profile_type == "explorer":
            # Different regions, lower popularity, accepts some risks
            if popularity <= 7.5:
                matches = True
        
        elif profile_type == "photographer":
            # Lake/peaks landscapes, one-way trails
            if ("lake" in landscapes or "peaks" in landscapes) and trail_type == "one_way":
                matches = True
        
        else:  # Default/casual
            if difficulty <= 5.0 and distance <= 8.0:
                matches = True
        
        if matches:
            matched.append(trail)
    
    return matched


def seed_trail_history():
    """Seed trail history for all users based on their profiles."""
    print("Seeding trail history for all users...")
    print("=" * 60)
    
    # Clear existing history
    conn = sqlite3.connect(USERS_DB)
    cur = conn.cursor()
    cur.execute("DELETE FROM saved_trails")
    cur.execute("DELETE FROM started_trails")
    cur.execute("DELETE FROM trail_performance_data")
    cur.execute("DELETE FROM completed_trails")
    conn.commit()
    conn.close()
    print("Cleared existing trail history")
    print()
    
    # Get all users and trails
    users = get_all_users()
    all_trails = get_all_trails()
    
    print(f"Found {len(users)} users")
    print(f"Found {len(all_trails)} trails")
    print()
    
    total_saved = 0
    total_completed = 0
    
    # Group trails by region for explorers
    trails_by_region = defaultdict(list)
    for trail in all_trails:
        region = trail.get("region", "unknown")
        trails_by_region[region].append(trail)
    
    for user in users:
        user_id = user["id"]
        user_name = user.get("name", f"user_{user_id}")
        experience = user.get("experience", "Intermediate")
        
        # Get user profile
        profile = get_user_profile(user_id)
        profile_type = profile.get("primary_profile") if profile else "casual"
        
        # Determine number of trails based on experience
        if experience == "Beginner":
            num_saved = random.randint(2, 4)
            num_completed = random.randint(1, 2)
        elif experience == "Intermediate":
            num_saved = random.randint(4, 6)
            num_completed = random.randint(2, 3)
        else:  # Advanced
            num_saved = random.randint(6, 8)
            num_completed = random.randint(3, 5)
        
        # Match trails to profile
        matched_trails = match_trails_to_profile(all_trails, profile_type, experience)
        
        # If not enough matches, fall back to more lenient matching
        if len(matched_trails) < num_saved + num_completed:
            # Try with more lenient profile matching
            if profile_type == "contemplative":
                # Accept any scenic trail
                matched_trails = [t for t in all_trails 
                                if any(kw in (t.get("landscapes") or "").lower() 
                                      for kw in ["lake", "peaks", "glacier", "mountain"])
                                and t.get("difficulty", 5.0) <= (6.5 if experience == "Advanced" else 5.0)]
            elif profile_type == "elevation_lover":
                # Accept any trail with elevation
                matched_trails = [t for t in all_trails 
                                if t.get("elevation_gain", 0) >= 300
                                and t.get("difficulty", 5.0) >= 5.0]
            elif profile_type == "performance_athlete":
                # Accept any long trail
                matched_trails = [t for t in all_trails 
                                if t.get("distance", 0) >= 6.0
                                and t.get("duration", 0) >= 60]
            else:
                # Generic fallback: trails matching experience level
                difficulty_range = {
                    "Beginner": (0, 4.0),
                    "Intermediate": (3.0, 6.5),
                    "Advanced": (5.0, 10.0)
                }
                min_d, max_d = difficulty_range.get(experience, (0, 10.0))
                matched_trails = [t for t in all_trails 
                                if min_d <= t.get("difficulty", 5.0) <= max_d]
        
        # For explorers, ensure diversity across regions
        if profile_type == "explorer" and len(matched_trails) > num_saved + num_completed:
            # Select trails from different regions
            selected_trails = []
            used_regions = set()
            for trail in matched_trails:
                region = trail.get("region", "unknown")
                if region not in used_regions or len(selected_trails) < num_saved + num_completed:
                    selected_trails.append(trail)
                    used_regions.add(region)
                if len(selected_trails) >= num_saved + num_completed:
                    break
            matched_trails = selected_trails[:num_saved + num_completed]
        
        # Shuffle and select
        random.shuffle(matched_trails)
        needed = num_saved + num_completed
        selected = matched_trails[:needed] if len(matched_trails) >= needed else matched_trails
        
        if not selected:
            print(f"User {user_name} (ID: {user_id}): No matching trails found - skipping")
            continue
        
        # Ensure we have at least 1 completed trail
        if len(selected) < num_completed:
            num_completed = max(1, len(selected) - num_saved)
            if num_completed < 1:
                num_completed = 1
                num_saved = max(0, len(selected) - 1)
        
        # Split into saved and completed
        saved_trails = selected[:num_saved] if num_saved > 0 else []
        completed_trails = selected[num_saved:num_saved + num_completed] if num_completed > 0 else []
        
        print(f"User {user_name} (ID: {user_id}, {experience}, {profile_type}):")
        print(f"  Saving {len(saved_trails)} trail(s)")
        print(f"  Completing {len(completed_trails)} trail(s)")
        
        # Save trails
        for trail in saved_trails:
            trail_id = trail.get("trail_id")
            save_trail(user_id, trail_id, f"Saved trail matching {profile_type} profile")
            total_saved += 1
        
        # Complete trails with dummy data
        for trail in completed_trails:
            trail_id = trail.get("trail_id")
            distance = trail.get("distance", 5.0)
            difficulty = trail.get("difficulty", 5.0)
            elevation_gain = trail.get("elevation_gain", 300)
            estimated_duration = trail.get("duration", 120)
            
            # Generate completion date (spread over last 6 months)
            days_ago = random.randint(0, 180)
            completion_date = (datetime.now() - timedelta(days=days_ago)).isoformat()
            
            # Calculate actual duration with variation
            duration_variation = random.uniform(0.90, 1.10)
            actual_duration = int(estimated_duration * duration_variation)
            
            # Generate rating (4-5 for most, occasional 3)
            rating = random.choices([3, 4, 5], weights=[10, 30, 60])[0]
            
            # Calculate predicted metrics (simplified, without needing analytics)
            fitness_level = user.get("fitness_level", "Medium")
            base_hr = {"High": 120, "Medium": 140, "Low": 160}.get(fitness_level, 140)
            
            # Simple predictions based on trail characteristics
            predicted_duration = estimated_duration
            predicted_avg_hr = int(base_hr * (1 + difficulty / 20))
            predicted_max_hr = int(predicted_avg_hr * 1.2)
            predicted_speed = (distance / actual_duration) * 60 if actual_duration > 0 else 4.0
            predicted_max_speed = predicted_speed * 1.3
            predicted_calories = int(distance * 60 + elevation_gain * 0.5)
            
            # Generate actual metrics with variation
            hr_variation = random.uniform(0.95, 1.05)
            avg_hr = int(predicted_avg_hr * hr_variation)
            avg_hr = max(60, min(180, avg_hr))
            max_hr = int(predicted_max_hr * hr_variation)
            max_hr = min(200, max(avg_hr + 10, max_hr))
            
            speed_variation = random.uniform(0.95, 1.05)
            avg_speed = round(predicted_speed * speed_variation, 2)
            avg_speed = max(2.0, min(8.0, avg_speed))
            max_speed = round(avg_speed * 1.3, 2)
            max_speed = min(10.0, max_speed)
            
            calories_variation = random.uniform(0.95, 1.05)
            total_calories = int(predicted_calories * calories_variation)
            total_calories = max(100, total_calories)
            
            # Open connection for this trail
            conn = sqlite3.connect(USERS_DB)
            cur = conn.cursor()
            
            # Insert completed trail
            _insert_completed_trail_sql(
                user_id, trail_id, completion_date, actual_duration, rating,
                conn=conn,
                predicted_duration=predicted_duration,
                predicted_avg_heart_rate=predicted_avg_hr,
                predicted_max_heart_rate=predicted_max_hr,
                predicted_avg_speed=predicted_speed,
                predicted_max_speed=predicted_max_speed,
                predicted_calories=predicted_calories,
                predicted_profile_category=profile_type
            )
            
            # Get the completed_trail_id
            cur.execute("""
                SELECT id FROM completed_trails
                WHERE user_id = ? AND trail_id = ? AND completion_date = ?
                ORDER BY id DESC LIMIT 1
            """, (user_id, trail_id, completion_date))
            row = cur.fetchone()
            completed_trail_id = row[0] if row else None
            
            if completed_trail_id:
                # Update with actual metrics
                cur.execute("""
                    UPDATE completed_trails
                    SET avg_heart_rate = ?, max_heart_rate = ?,
                        avg_speed = ?, max_speed = ?, total_calories = ?
                    WHERE id = ?
                """, (avg_hr, max_hr, avg_speed, max_speed, total_calories, completed_trail_id))
                
                # Generate time-series data
                trail_start_elevation = trail.get("latitude", 45.5) * 100
                time_series_data = generate_time_series_data(
                    completed_trail_id,
                    actual_duration,
                    avg_hr,
                    max_hr,
                    avg_speed,
                    max_speed,
                    elevation_gain,
                    total_calories,
                    trail_start_elevation
                )
                
                # Insert time-series data
                for point in time_series_data:
                    cur.execute("""
                        INSERT INTO trail_performance_data
                        (completed_trail_id, timestamp, heart_rate, speed, elevation,
                         latitude, longitude, calories, cadence)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        point["completed_trail_id"],
                        point["timestamp"],
                        point["heart_rate"],
                        point["speed"],
                        point["elevation"],
                        point["latitude"],
                        point["longitude"],
                        point["calories"],
                        point["cadence"]
                    ))
                
                total_completed += 1
            
            conn.commit()
            conn.close()
        print()
    
    print("=" * 60)
    print(f"Seeding complete!")
    print(f"  Total saved trails: {total_saved}")
    print(f"  Total completed trails: {total_completed}")
    print()
    print("Recalculating user profiles...")
    
    # Recalculate profiles
    from backend.user_profiling import UserProfiler
    from backend.db import update_user_profile
    
    profiler = UserProfiler()
    for user in users:
        user_id = user["id"]
        try:
            primary_profile, scores = profiler.detect_profile(user_id)
            if primary_profile:
                update_user_profile(user_id, primary_profile, scores)
        except Exception as e:
            print(f"Warning: Could not update profile for user {user_id}: {e}")


if __name__ == "__main__":
    seed_trail_history()
