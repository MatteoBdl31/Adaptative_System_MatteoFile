# -*- coding: utf-8 -*-
"""
Generate dummy smartwatch JSON files for users' started trails.
Creates JSON files with time-series performance data that varies based on user profiles.
"""

import sqlite3
import json
import random
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from backend.db import USERS_DB, get_trail, get_user_profile, get_all_users
from backend.generate_dummy_fitness_data import (
    generate_heart_rate,
    generate_speed,
    generate_calories,
    generate_time_series_data
)
from backend.trail_analytics import TrailAnalytics
from backend.trail_management import get_started_trails, get_saved_trails


def sanitize_filename(name):
    """Sanitize a string for use in filename."""
    # Replace spaces and special characters with underscores
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'[-\s]+', '_', name)
    return name[:100]  # Limit length


def apply_profile_variance(data_points, profile_type, trail_difficulty, elevation_gain):
    """
    Apply profile-specific variance to data points.
    
    Args:
        data_points: List of data point dictionaries
        profile_type: User profile type (elevation_lover, performance_athlete, etc.)
        trail_difficulty: Trail difficulty (0-10)
        elevation_gain: Elevation gain in meters
    
    Returns:
        Modified data_points list
    """
    if not data_points:
        return data_points
    
    profile_multipliers = {
        "elevation_lover": {
            "heart_rate": 1.15,  # Higher HR on elevation
            "speed": 0.85,  # Slower on climbs
            "cadence": 0.95,
            "pauses": False
        },
        "performance_athlete": {
            "heart_rate": 1.10,  # Consistent high HR
            "speed": 1.20,  # Faster speeds
            "cadence": 1.15,  # Higher cadence
            "pauses": False
        },
        "contemplative": {
            "heart_rate": 0.85,  # Lower HR
            "speed": 0.75,  # Slower speeds
            "cadence": 0.90,
            "pauses": True  # More pauses
        },
        "casual": {
            "heart_rate": 0.95,  # Moderate HR
            "speed": 0.90,  # Moderate speed
            "cadence": 0.95,
            "pauses": False
        },
        "family": {
            "heart_rate": 0.90,  # Lower HR
            "speed": 0.80,  # Slower speeds
            "cadence": 0.90,
            "pauses": True  # Frequent pauses
        },
        "explorer": {
            "heart_rate": 1.05,  # Variable, higher on difficult sections
            "speed": 1.00,  # Variable
            "cadence": 1.00,
            "pauses": False
        },
        "photographer": {
            "heart_rate": 0.95,  # Moderate HR
            "speed": 0.85,  # Slower due to stops
            "cadence": 0.90,
            "pauses": True  # Frequent pauses for photos
        }
    }
    
    multipliers = profile_multipliers.get(profile_type, {
        "heart_rate": 1.0,
        "speed": 1.0,
        "cadence": 1.0,
        "pauses": False
    })
    
    modified_points = []
    pause_indices = set()
    
    # Add pauses for profiles that need them
    if multipliers["pauses"] and len(data_points) > 20:
        num_pauses = random.randint(2, 5) if profile_type in ["contemplative", "photographer"] else random.randint(1, 3)
        pause_indices = set(random.sample(range(10, len(data_points) - 10), min(num_pauses, len(data_points) - 20)))
    
    for i, point in enumerate(data_points):
        modified_point = point.copy()
        
        # Apply multipliers
        if point.get("heart_rate"):
            modified_point["heart_rate"] = int(point["heart_rate"] * multipliers["heart_rate"])
            modified_point["heart_rate"] = max(60, min(200, modified_point["heart_rate"]))
        
        if point.get("speed"):
            modified_point["speed"] = round(point["speed"] * multipliers["speed"], 2)
            modified_point["speed"] = max(1.0, min(10.0, modified_point["speed"]))
        
        if point.get("cadence"):
            modified_point["cadence"] = int(point["cadence"] * multipliers["cadence"])
            modified_point["cadence"] = max(80, min(160, modified_point["cadence"]))
        
        # Handle pauses (set speed to 0, reduce HR)
        if i in pause_indices:
            modified_point["speed"] = 0.0
            if modified_point.get("heart_rate"):
                modified_point["heart_rate"] = max(60, modified_point["heart_rate"] - 20)
            modified_point["cadence"] = 0
        
        # Profile-specific adjustments
        if profile_type == "elevation_lover" and elevation_gain > 500:
            # Higher HR on elevation sections
            progress = i / len(data_points)
            if 0.2 < progress < 0.8:  # Middle section (climbing)
                if modified_point.get("heart_rate"):
                    modified_point["heart_rate"] = min(200, int(modified_point["heart_rate"] * 1.1))
        
        if profile_type == "explorer" and trail_difficulty > 7:
            # Higher intensity on difficult sections
            progress = i / len(data_points)
            if 0.3 < progress < 0.7:  # Middle section
                if modified_point.get("heart_rate"):
                    modified_point["heart_rate"] = min(200, int(modified_point["heart_rate"] * 1.15))
                if modified_point.get("speed"):
                    modified_point["speed"] = min(10.0, modified_point["speed"] * 1.1)
        
        modified_points.append(modified_point)
    
    return modified_points


def generate_smartwatch_file(user_id, trail_id, output_dir):
    """
    Generate a smartwatch JSON file for a user-trail combination.
    
    Args:
        user_id: User ID
        trail_id: Trail ID
        output_dir: Output directory for JSON files
    
    Returns:
        Path to generated file or None if generation failed
    """
    from backend.db import get_user
    
    # Get user info
    user = get_user(user_id)
    if not user:
        return None
    
    # Get user profile
    profile = get_user_profile(user_id)
    profile_type = profile.get("primary_profile") if profile else None
    if not profile_type:
        profile_type = "casual"  # Default
    
    # Get trail details
    trail = get_trail(trail_id)
    if not trail:
        return None
    
    trail_name = trail.get("name", "Unknown Trail")
    distance = trail.get("distance", 5.0)
    difficulty = trail.get("difficulty", 5.0)
    elevation_gain = trail.get("elevation_gain", 300)
    estimated_duration = trail.get("duration", 120)
    
    # Use estimated duration as baseline
    duration_minutes = estimated_duration
    
    # Get fitness level
    fitness_level = user.get("fitness_level", "Medium")
    base_heart_rates = {
        "High": random.randint(110, 130),
        "Medium": random.randint(130, 150),
        "Low": random.randint(150, 170)
    }
    base_hr = base_heart_rates.get(fitness_level, 140)
    
    # Predict metrics using TrailAnalytics
    analytics = TrailAnalytics()
    predicted = analytics.predict_metrics(trail, user)
    
    predicted_avg_hr = predicted.get("predicted_heart_rate", {}).get("avg", base_hr)
    predicted_max_hr = predicted.get("predicted_heart_rate", {}).get("max", int(predicted_avg_hr * 1.2))
    predicted_speed = predicted.get("predicted_speed", (distance / duration_minutes) * 60)
    predicted_max_speed = predicted_speed * 1.3 if predicted_speed else None
    predicted_calories = predicted.get("predicted_calories", 300)
    
    # Generate actual metrics with variation
    duration_variation = random.uniform(0.90, 1.10)  # ±10% variation
    actual_duration = int(duration_minutes * duration_variation)
    
    hr_variation = random.uniform(0.95, 1.05)  # ±5% variation
    avg_hr = int(predicted_avg_hr * hr_variation)
    avg_hr = max(60, min(180, avg_hr))
    max_hr = int(predicted_max_hr * hr_variation)
    max_hr = min(200, max(avg_hr + 10, max_hr))
    
    speed_variation = random.uniform(0.95, 1.05)  # ±5% variation
    avg_speed = round(predicted_speed * speed_variation, 2)
    avg_speed = max(2.0, min(8.0, avg_speed))
    max_speed = round(avg_speed * (1.3 + random.uniform(0, 0.2)), 2)
    max_speed = min(10.0, max_speed)
    
    calories_variation = random.uniform(0.95, 1.05)  # ±5% variation
    total_calories = int(predicted_calories * calories_variation)
    total_calories = max(100, total_calories)
    
    # Generate time-series data (using a dummy completed_trail_id)
    trail_start_elevation = trail.get("latitude", 45.5) * 100  # Approximate
    time_series_data = generate_time_series_data(
        completed_trail_id=0,  # Dummy ID, not used in file
        duration_minutes=actual_duration,
        avg_hr=avg_hr,
        max_hr=max_hr,
        avg_speed=avg_speed,
        max_speed=max_speed,
        elevation_gain=elevation_gain,
        total_calories=total_calories,
        trail_start_elevation=trail_start_elevation
    )
    
    # Remove completed_trail_id from data points (not needed in JSON file)
    for point in time_series_data:
        point.pop("completed_trail_id", None)
    
    # Apply profile-based variance
    time_series_data = apply_profile_variance(
        time_series_data,
        profile_type,
        difficulty,
        elevation_gain
    )
    
    # Calculate start and end times
    start_time = datetime.now() - timedelta(minutes=actual_duration)
    end_time = datetime.now()
    
    # Create JSON structure
    smartwatch_data = {
        "trail_id": trail_id,
        "trail_name": trail_name,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "data_points": time_series_data
    }
    
    # Generate filename
    user_name = sanitize_filename(user.get("name", f"user_{user_id}"))
    profile_name = sanitize_filename(profile_type)
    trail_name_safe = sanitize_filename(trail_name)
    
    filename = f"{user_name}_{profile_name}_{trail_name_safe}.json"
    filepath = os.path.join(output_dir, filename)
    
    # Save JSON file
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(smartwatch_data, f, indent=2, ensure_ascii=False)
        return filepath
    except Exception as e:
        print(f"Error saving file {filepath}: {e}")
        return None


def generate_all_smartwatch_files():
    """Generate smartwatch JSON files for all users' saved trails."""
    # Create output directory
    base_dir = Path(__file__).parent.parent
    output_dir = base_dir / "data" / "dummy_smartwatch"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating smartwatch data files in: {output_dir}")
    print("=" * 60)
    
    # Get all users
    users = get_all_users()
    
    total_files = 0
    total_errors = 0
    
    for user in users:
        user_id = user["id"]
        user_name = user.get("name", f"user_{user_id}")
        
        # Get saved trails for this user
        saved_trails = get_saved_trails(user_id)
        
        if not saved_trails:
            print(f"User {user_name} (ID: {user_id}): No saved trails")
            continue
        
        print(f"\nUser {user_name} (ID: {user_id}): {len(saved_trails)} saved trail(s)")
        
        for saved_trail in saved_trails:
            trail_id = saved_trail.get("trail_id")
            
            filepath = generate_smartwatch_file(user_id, trail_id, str(output_dir))
            
            if filepath:
                print(f"  [OK] Generated: {os.path.basename(filepath)}")
                total_files += 1
            else:
                print(f"  [ERROR] Failed to generate file for trail {trail_id}")
                total_errors += 1
    
    print("\n" + "=" * 60)
    print(f"Generation complete!")
    print(f"  Total files generated: {total_files}")
    print(f"  Errors: {total_errors}")
    print(f"  Output directory: {output_dir}")


if __name__ == "__main__":
    generate_all_smartwatch_files()
