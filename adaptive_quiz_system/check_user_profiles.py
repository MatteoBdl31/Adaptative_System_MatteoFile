#!/usr/bin/env python3
"""
Script to check user profile distribution and variety.

This script analyzes the detected user profiles in the database to verify
that we have good variety across different profile types.
"""
import sys
from pathlib import Path

# Add parent directory to path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.db import get_all_users, get_user_profile
from backend.user_profiling import UserProfiler

def main():
    print("=" * 70)
    print("USER PROFILE DISTRIBUTION ANALYSIS")
    print("=" * 70)
    print()
    
    # Get all users
    users = get_all_users()
    print(f"Total users: {len(users)}\n")
    
    # Count profiles
    profile_counts = {}
    users_with_profiles = 0
    users_without_profiles = 0
    users_with_insufficient_trails = 0
    
    # Profile names for display
    profile_names = {
        "elevation_lover": "Elevation Enthusiast",
        "performance_athlete": "Performance Athlete",
        "contemplative": "Contemplative Hiker",
        "casual": "Casual Hiker",
        "family": "Family / Group Hiker",
        "explorer": "Explorer / Adventurer",
        "photographer": "Photographer / Content Creator"
    }
    
    # Analyze each user
    for user in users:
        user_id = user.get("id")
        detected_profile = user.get("detected_profile")
        completed_trails_count = len(user.get("completed_trails", []))
        
        if detected_profile:
            profile_counts[detected_profile] = profile_counts.get(detected_profile, 0) + 1
            users_with_profiles += 1
        elif completed_trails_count < 3:
            users_without_profiles += 1
            users_with_insufficient_trails += 1
        else:
            users_without_profiles += 1
    
    # Display results
    print("PROFILE DISTRIBUTION:")
    print("-" * 70)
    if profile_counts:
        total_profiles = sum(profile_counts.values())
        for profile_key, count in sorted(profile_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_profiles) * 100
            profile_name = profile_names.get(profile_key, profile_key)
            bar = "█" * int(percentage / 2)
            print(f"{profile_name:30s} {count:2d} users ({percentage:5.1f}%) {bar}")
    else:
        print("No profiles detected yet.")
    
    print()
    print("SUMMARY:")
    print("-" * 70)
    print(f"Users with detected profiles: {users_with_profiles}")
    print(f"Users without profiles: {users_without_profiles}")
    if users_with_insufficient_trails > 0:
        print(f"  - Insufficient trails (< 3): {users_with_insufficient_trails}")
    print()
    
    # Check variety
    unique_profiles = len(profile_counts)
    print(f"Unique profile types detected: {unique_profiles} out of {len(profile_names)} possible")
    print()
    
    if unique_profiles < len(profile_names):
        missing_profiles = set(profile_names.keys()) - set(profile_counts.keys())
        if missing_profiles:
            print("MISSING PROFILES:")
            print("-" * 70)
            for profile_key in sorted(missing_profiles):
                profile_name = profile_names.get(profile_key, profile_key)
                print(f"  - {profile_name}")
            print()
    
    # Show detailed breakdown for each user
    print("DETAILED USER BREAKDOWN:")
    print("-" * 70)
    for user in users:
        user_id = user.get("id")
        name = user.get("name", f"User {user_id}")
        detected_profile = user.get("detected_profile")
        completed_trails_count = len(user.get("completed_trails", []))
        profile_scores = user.get("profile_scores", {})
        
        if detected_profile:
            profile_name = profile_names.get(detected_profile, detected_profile)
            # Get top 3 scores
            sorted_scores = sorted(profile_scores.items(), key=lambda x: x[1], reverse=True)[:3]
            top_scores_str = ", ".join([f"{profile_names.get(k, k)}: {v:.2f}" for k, v in sorted_scores])
            print(f"{name:15s} ({completed_trails_count:2d} trails) -> {profile_name:30s} | Top scores: {top_scores_str}")
        else:
            reason = "Insufficient trails" if completed_trails_count < 3 else "No profile detected"
            print(f"{name:15s} ({completed_trails_count:2d} trails) -> {reason}")
    
    print()
    print("=" * 70)
    
    # Recommendations
    if unique_profiles < len(profile_names):
        print("RECOMMENDATIONS:")
        print("-" * 70)
        print("To increase profile variety:")
        print("1. Ensure users have completed trails from different regions")
        print("2. Diversify trail characteristics (difficulty, distance, elevation, landscapes)")
        print("3. Add more completed trails for users with insufficient data")
        print("4. Review seed data in backend/init_db.py to ensure diversity")
    else:
        print("✓ Good profile variety! All profile types are represented.")
    
    print("=" * 70)

if __name__ == "__main__":
    main()
