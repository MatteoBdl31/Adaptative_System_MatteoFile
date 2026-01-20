# -*- coding: utf-8 -*-
"""
Generate dummy fitness metrics and time-series performance data for users' completed trails.
"""

import sqlite3
import json
import random
import os
from datetime import datetime, timedelta
from backend.db import USERS_DB, get_trail, _ensure_new_tables

_ensure_new_tables()


def generate_heart_rate(base_hr, difficulty, elevation_gain, duration_minutes):
    """
    Generate realistic heart rate based on trail characteristics.
    
    Args:
        base_hr: Base heart rate (resting ~60-80, active ~120-160)
        difficulty: Trail difficulty (0-10)
        elevation_gain: Elevation gain in meters
        duration_minutes: Trail duration in minutes
    
    Returns:
        (avg_hr, max_hr) tuple
    """
    # Base heart rate increases with difficulty and elevation
    difficulty_factor = 1 + (difficulty / 10) * 0.3
    elevation_factor = 1 + min(elevation_gain / 1000, 0.2)  # Up to 20% increase
    
    avg_hr = int(base_hr * difficulty_factor * elevation_factor)
    # Add some variation
    avg_hr += random.randint(-10, 15)
    avg_hr = max(60, min(180, avg_hr))  # Clamp to reasonable range
    
    # Max HR is typically 20-30% higher than avg during peaks
    max_hr = int(avg_hr * (1.2 + random.uniform(0, 0.1)))
    max_hr = min(200, max_hr)  # Cap at 200 bpm
    
    return avg_hr, max_hr


def generate_speed(distance_km, duration_minutes, difficulty):
    """
    Generate realistic speed based on trail characteristics.
    
    Args:
        distance_km: Trail distance in km
        duration_minutes: Trail duration in minutes
        difficulty: Trail difficulty (0-10)
    
    Returns:
        (avg_speed, max_speed) tuple in km/h
    """
    if duration_minutes == 0:
        return 0, 0
    
    # Base speed from distance/duration
    base_speed = (distance_km / duration_minutes) * 60
    
    # Adjust for difficulty (harder trails = slower)
    difficulty_factor = 1 - (difficulty / 10) * 0.2
    avg_speed = base_speed * difficulty_factor
    
    # Add variation
    avg_speed += random.uniform(-0.5, 1.0)
    avg_speed = max(2.0, min(8.0, avg_speed))  # Clamp to 2-8 km/h
    
    # Max speed is typically 30-50% higher
    max_speed = avg_speed * (1.3 + random.uniform(0, 0.2))
    max_speed = min(10.0, max_speed)
    
    return round(avg_speed, 2), round(max_speed, 2)


def generate_calories(distance_km, elevation_gain, duration_minutes, difficulty, weight_kg=70):
    """
    Generate realistic calorie burn.
    
    Args:
        distance_km: Trail distance in km
        elevation_gain: Elevation gain in meters
        duration_minutes: Trail duration in minutes
        difficulty: Trail difficulty (0-10)
        weight_kg: User weight in kg (default 70kg)
    
    Returns:
        Total calories burned
    """
    # Base calories: ~50-100 cal/km depending on difficulty
    base_calories_per_km = 50 + (difficulty * 5)
    distance_calories = distance_km * base_calories_per_km
    
    # Elevation adds significant calories: ~1 cal per meter per kg
    elevation_calories = (elevation_gain / 100) * weight_kg * 0.1
    
    # Time-based: ~5-10 cal/min depending on intensity
    time_calories = duration_minutes * (5 + difficulty * 0.5)
    
    total_calories = int(distance_calories + elevation_calories + time_calories)
    
    # Add variation
    total_calories += random.randint(-50, 100)
    total_calories = max(100, total_calories)  # Minimum 100 calories
    
    return total_calories


def generate_time_series_data(
    completed_trail_id,
    duration_minutes,
    avg_hr,
    max_hr,
    avg_speed,
    max_speed,
    elevation_gain,
    total_calories,
    trail_start_elevation=500
):
    """
    Generate time-series performance data points.
    
    Args:
        completed_trail_id: ID of completed trail
        duration_minutes: Total duration
        avg_hr: Average heart rate
        max_hr: Maximum heart rate
        avg_speed: Average speed
        max_speed: Maximum speed
        elevation_gain: Total elevation gain
        total_calories: Total calories
        trail_start_elevation: Starting elevation (default 500m)
    
    Returns:
        List of data point dictionaries
    """
    data_points = []
    
    # Generate points every 30 seconds (or every minute for longer trails)
    interval_seconds = 30 if duration_minutes < 60 else 60
    num_points = (duration_minutes * 60) // interval_seconds
    
    if num_points == 0:
        num_points = 10  # Minimum 10 points
    
    # Simulate trail progression
    for i in range(num_points):
        timestamp = i * interval_seconds
        progress = i / num_points  # 0 to 1
        
        # Heart rate: starts lower, peaks in middle, decreases slightly at end
        hr_progression = progress * (1.2 - progress * 0.4)  # Peak around 60% progress
        current_hr = int(avg_hr * (0.7 + hr_progression * 0.6))
        current_hr = min(max_hr, max(avg_hr - 20, current_hr))
        current_hr += random.randint(-5, 5)
        current_hr = max(60, min(200, current_hr))
        
        # Speed: varies with elevation changes
        speed_variation = 1 + random.uniform(-0.2, 0.2)
        current_speed = avg_speed * speed_variation
        current_speed = max(1.0, min(max_speed, current_speed))
        
        # Elevation: gradual increase, then decrease (for out-and-back) or steady (for loop)
        elevation_progress = progress if progress < 0.5 else (1 - progress)  # Out-and-back pattern
        current_elevation = trail_start_elevation + (elevation_gain * elevation_progress)
        current_elevation += random.uniform(-10, 10)
        
        # Calories: accumulate over time
        calories_at_point = int((total_calories / num_points) * (i + 1))
        
        # Cadence: steps per minute (typically 100-140 for hiking)
        cadence = random.randint(100, 140)
        
        # GPS coordinates (simplified - would be actual trail coordinates in real data)
        # Using approximate values based on progress
        latitude = 45.5 + (progress * 0.1) + random.uniform(-0.01, 0.01)
        longitude = 6.2 + (progress * 0.1) + random.uniform(-0.01, 0.01)
        
        data_points.append({
            "completed_trail_id": completed_trail_id,
            "timestamp": timestamp,
            "heart_rate": current_hr,
            "speed": round(current_speed, 2),
            "elevation": round(current_elevation, 1),
            "latitude": round(latitude, 6),
            "longitude": round(longitude, 6),
            "calories": calories_at_point,
            "cadence": cadence
        })
    
    return data_points


def generate_fitness_data_for_user(user_id, fitness_level="Medium", user_profile=None):
    """
    Generate fitness data for all completed trails of a user.
    Uses predicted metrics as baseline and adds realistic variations.
    
    Args:
        user_id: User ID
        fitness_level: User fitness level ("High", "Medium", "Low")
        user_profile: Optional user profile dictionary
    """
    from backend.trail_analytics import TrailAnalytics
    from backend.db import get_user
    
    conn = sqlite3.connect(USERS_DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Get user info if not provided
    if not user_profile:
        user_profile = get_user(user_id)
        if not user_profile:
            print(f"User {user_id} not found")
            conn.close()
            return
    
    # Get user's completed trails
    cur.execute("""
        SELECT ct.id, ct.trail_id, ct.actual_duration, ct.completion_date, ct.rating
        FROM completed_trails ct
        WHERE ct.user_id = ?
        ORDER BY ct.completion_date DESC
    """, (user_id,))
    
    completed_trails = [dict(row) for row in cur.fetchall()]
    
    if not completed_trails:
        print(f"No completed trails found for user {user_id}")
        conn.close()
        return
    
    # Base heart rate based on fitness level
    base_heart_rates = {
        "High": random.randint(110, 130),
        "Medium": random.randint(130, 150),
        "Low": random.randint(150, 170)
    }
    base_hr = base_heart_rates.get(fitness_level, 140)
    
    analytics = TrailAnalytics()
    
    print(f"Generating fitness data for user {user_id} ({len(completed_trails)} trails)...")
    
    for ct in completed_trails:
        trail_id = ct["trail_id"]
        completed_trail_id = ct["id"]
        actual_duration = ct.get("actual_duration") or 120
        
        # Get trail details
        trail = get_trail(trail_id)
        if not trail:
            continue
        
        distance = trail.get("distance", 5.0)
        difficulty = trail.get("difficulty", 5.0)
        elevation_gain = trail.get("elevation_gain", 300)
        estimated_duration = trail.get("duration", 120)
        
        # Use actual duration if available, otherwise estimated
        duration_minutes = actual_duration if actual_duration else estimated_duration
        
        # PREDICT metrics first (what was expected/planned)
        predicted = analytics.predict_metrics(trail, user_profile)
        predicted_duration = predicted.get("predicted_duration", duration_minutes)
        predicted_hr = predicted.get("predicted_heart_rate", {})
        predicted_avg_hr = predicted_hr.get("avg", base_hr)
        predicted_max_hr = predicted_hr.get("max", int(predicted_avg_hr * 1.2))
        predicted_speed = predicted.get("predicted_speed", (distance / duration_minutes) * 60)
        predicted_calories = predicted.get("predicted_calories", 300)
        
        # Generate ACTUAL metrics with realistic variations from predicted
        # Duration: actual can be ±10-20% different from predicted
        duration_variation = random.uniform(0.85, 1.15)  # ±15% variation
        actual_duration_final = int(predicted_duration * duration_variation)
        actual_duration_final = max(int(predicted_duration * 0.8), min(int(predicted_duration * 1.2), actual_duration_final))
        
        # Heart rate: actual can be ±5-10% different (due to conditions, fitness on the day)
        hr_variation = random.uniform(0.92, 1.08)  # ±8% variation
        avg_hr = int(predicted_avg_hr * hr_variation)
        avg_hr = max(60, min(180, avg_hr))
        max_hr = int(predicted_max_hr * hr_variation)
        max_hr = min(200, max(avg_hr + 10, max_hr))
        
        # Speed: actual can be ±10-15% different (terrain, weather, pace)
        speed_variation = random.uniform(0.88, 1.12)  # ±12% variation
        avg_speed = round(predicted_speed * speed_variation, 2)
        avg_speed = max(2.0, min(8.0, avg_speed))
        max_speed = round(avg_speed * (1.3 + random.uniform(0, 0.2)), 2)
        max_speed = min(10.0, max_speed)
        
        # Calories: actual can be ±10-20% different (metabolism, effort level)
        calories_variation = random.uniform(0.85, 1.15)  # ±15% variation
        total_calories = int(predicted_calories * calories_variation)
        total_calories = max(100, total_calories)
        
        # Update completed_trail record with aggregated metrics
        # Also update actual_duration if it differs significantly from predicted
        cur.execute("""
            UPDATE completed_trails
            SET actual_duration = ?,
                avg_heart_rate = ?,
                max_heart_rate = ?,
                avg_speed = ?,
                max_speed = ?,
                total_calories = ?
            WHERE id = ?
        """, (actual_duration_final, avg_hr, max_hr, avg_speed, max_speed, total_calories, completed_trail_id))
        
        # Log the variation for debugging
        duration_diff = actual_duration_final - predicted_duration
        duration_diff_pct = (duration_diff / predicted_duration * 100) if predicted_duration > 0 else 0
        hr_diff_pct = ((avg_hr - predicted_avg_hr) / predicted_avg_hr * 100) if predicted_avg_hr > 0 else 0
        speed_diff_pct = ((avg_speed - predicted_speed) / predicted_speed * 100) if predicted_speed > 0 else 0
        
        print(f"    Trail {trail_id}:")
        print(f"      Duration: {predicted_duration}min → {actual_duration_final}min ({duration_diff_pct:+.1f}%)")
        print(f"      HR: {predicted_avg_hr}bpm → {avg_hr}bpm ({hr_diff_pct:+.1f}%)")
        print(f"      Speed: {predicted_speed}km/h → {avg_speed}km/h ({speed_diff_pct:+.1f}%)")
        
        # Generate time-series data using ACTUAL duration and metrics
        time_series_data = generate_time_series_data(
            completed_trail_id,
            actual_duration_final,  # Use actual duration, not predicted
            avg_hr,
            max_hr,
            avg_speed,
            max_speed,
            elevation_gain,
            total_calories
        )
        
        # Delete existing data for this trail (if any)
        cur.execute("DELETE FROM trail_performance_data WHERE completed_trail_id = ?", (completed_trail_id,))
        
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
        
        print(f"    ✓ Generated {len(time_series_data)} time-series data points")
    
    conn.commit()
    conn.close()
    print(f"✓ Completed generating fitness data for user {user_id}")


def generate_fitness_data_for_all_users():
    """Generate fitness data for all users."""
    from backend.db import get_user
    
    conn = sqlite3.connect(USERS_DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Get all users with their fitness levels
    cur.execute("SELECT id, fitness_level FROM users")
    user_rows = [dict(row) for row in cur.fetchall()]
    
    conn.close()
    
    print(f"Generating fitness data for {len(user_rows)} users...")
    print("=" * 60)
    
    for user_row in user_rows:
        user_id = user_row["id"]
        user = get_user(user_id)  # Get full user profile
        generate_fitness_data_for_user(
            user_id, 
            user.get("fitness_level", "Medium"),
            user  # Pass full user profile for predictions
        )
        print()
    
    print("=" * 60)
    print("Fitness data generation complete!")
    print("\nNote: Actual metrics may differ from predicted values by 5-20%")
    print("This simulates real-world variations in performance.")


if __name__ == "__main__":
    _ensure_new_tables()
    generate_fitness_data_for_all_users()
