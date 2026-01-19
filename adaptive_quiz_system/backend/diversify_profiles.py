#!/usr/bin/env python3
"""
Helper script to select diverse trails for users to trigger different profiles.

This script helps create a more balanced distribution of user profiles by
selecting trails with specific characteristics for each user.
"""
from typing import List, Dict, Optional

def pick_trail_by_criteria(trails: List[dict], criteria: Dict) -> Optional[str]:
    """
    Pick a trail that matches specific criteria.
    
    Args:
        trails: List of all available trails
        criteria: Dictionary with criteria like:
            - min_elevation, max_elevation
            - min_difficulty, max_difficulty
            - min_distance, max_distance
            - min_popularity, max_popularity
            - landscapes (list of required landscapes)
            - trail_type (loop or one_way)
            - safety_risks (none, low, etc.)
    
    Returns:
        trail_id or None if no match found
    """
    for trail in trails:
        # Elevation check
        elevation = trail.get("elevation_gain", 0)
        if criteria.get("min_elevation") and elevation < criteria["min_elevation"]:
            continue
        if criteria.get("max_elevation") and elevation > criteria["max_elevation"]:
            continue
        
        # Difficulty check
        difficulty = trail.get("difficulty", 0)
        if criteria.get("min_difficulty") and difficulty < criteria["min_difficulty"]:
            continue
        if criteria.get("max_difficulty") and difficulty > criteria["max_difficulty"]:
            continue
        
        # Distance check
        distance = trail.get("distance", 0)
        if criteria.get("min_distance") and distance < criteria["min_distance"]:
            continue
        if criteria.get("max_distance") and distance > criteria["max_distance"]:
            continue
        
        # Popularity check
        popularity = trail.get("popularity", 0)
        if criteria.get("min_popularity") and popularity < criteria["min_popularity"]:
            continue
        if criteria.get("max_popularity") and popularity > criteria["max_popularity"]:
            continue
        
        # Landscape check
        if criteria.get("landscapes"):
            trail_landscapes = (trail.get("landscapes") or "").lower()
            required_landscapes = [l.lower() for l in criteria["landscapes"]]
            if not any(l in trail_landscapes for l in required_landscapes):
                continue
        
        # Trail type check
        if criteria.get("trail_type"):
            if trail.get("trail_type") != criteria["trail_type"]:
                continue
        
        # Safety check
        if criteria.get("safety_risks"):
            trail_safety = (trail.get("safety_risks") or "none").lower()
            if criteria["safety_risks"].lower() not in trail_safety:
                continue
        
        return trail.get("trail_id")
    
    return None

def create_diverse_completed_trails(trails: List[dict]) -> List[tuple]:
    """
    Create a diverse set of completed trails that will trigger different profiles.
    
    To ensure reproducibility, trails are sorted by trail_id before processing.
    
    Returns:
        List of (user_id, trail_id, completion_date, actual_duration, rating) tuples
    """
    # Sort trails deterministically by trail_id to ensure reproducible selection
    trails_sorted = sorted(trails, key=lambda t: t.get("trail_id", ""))
    
    completed = []
    used_trails = set()  # Track used trails to avoid duplicates
    
    # Helper to pick unused trail with fallback
    def pick_unused(criteria: Dict, fallback_criteria: Dict = None, require_match: bool = False) -> Optional[str]:
        # Try strict criteria first - search through all available trails (sorted for reproducibility)
        all_matching = [t for t in trails_sorted if t.get("trail_id") not in used_trails]
        for trail in all_matching:
            trail_id = pick_trail_by_criteria([trail], criteria)  # Check if this single trail matches
            if trail_id:
                used_trails.add(trail_id)
                return trail_id
        
        # Try fallback criteria - search through all available trails
        if fallback_criteria:
            for trail in all_matching:
                trail_id = pick_trail_by_criteria([trail], fallback_criteria)
                if trail_id:
                    used_trails.add(trail_id)
                    return trail_id
        
        # Last resort: pick any unused trail (only if not required to match)
        if not require_match:
            for trail in all_matching:
                trail_id = trail.get("trail_id")
                if trail_id:
                    used_trails.add(trail_id)
                    return trail_id
        
        return None
    
    # IMPORTANT: Process specialized profiles first to ensure they get the best matching trails
    # This prevents other users from consuming the limited trails that match these strict criteria
    
    # User 102 (Bob) - Beginner, Medium fitness -> Casual Hiker (PRIORITY 1)
    # Need: Very short distance (<4km), low difficulty (<3.8), safe
    # Require match: don't use last resort for specialized profiles
    for i, date in enumerate(["2024-01-10", "2024-01-25", "2024-02-05"]):
        trail_id = pick_unused(
            {"max_distance": 4.0, "max_difficulty": 3.8, "safety_risks": "none"},
            fallback_criteria={"max_distance": 4.5, "max_difficulty": 4.0, "safety_risks": "none"},
            require_match=True
        )
        if trail_id:
            completed.append((102, trail_id, date, 40 + i*5, 4))
    
    # User 107 (Grace) - Beginner, Low fitness -> Casual Hiker (PRIORITY 2)
    # Need: Very short (<3.5km), very easy (<3.5), very safe
    for i, date in enumerate(["2024-01-09", "2024-01-24", "2024-02-09"]):
        trail_id = pick_unused(
            {"max_distance": 3.5, "max_difficulty": 3.5, "safety_risks": "none"},
            fallback_criteria={"max_distance": 4.0, "max_difficulty": 3.8, "safety_risks": "none"},
            require_match=True
        )
        if trail_id:
            completed.append((107, trail_id, date, 30 + i*2, 3 + (i % 2)))
    
    # User 110 (Jack) - Beginner, High fitness -> Casual Hiker (PRIORITY 3)
    # Need: Short (<4km), easy (<3.8), safe
    for i, date in enumerate(["2024-01-14", "2024-01-29", "2024-02-17"]):
        trail_id = pick_unused(
            {"max_distance": 4.0, "max_difficulty": 3.8, "safety_risks": "none"},
            fallback_criteria={"max_distance": 4.5, "max_difficulty": 4.0, "safety_risks": "none"},
            require_match=True
        )
        if trail_id:
            completed.append((110, trail_id, date, 38 + i*2, 4))
    
    # User 104 (David) - Beginner, Low fitness -> Family Hiker (PRIORITY 4)
    # Need: Very low difficulty (<3.8), very safe (none), short distance (<7km)
    for i, date in enumerate(["2024-01-08", "2024-01-22", "2024-02-08"]):
        trail_id = pick_unused(
            {"max_difficulty": 3.8, "safety_risks": "none", "max_distance": 7.0},
            fallback_criteria={"max_difficulty": 4.0, "safety_risks": "none", "max_distance": 8.0},
            require_match=True
        )
        if trail_id:
            completed.append((104, trail_id, date, 25 + i*3, 3 + (i % 2)))
    
    # User 109 (Iris) - Intermediate, Low fitness -> Family Hiker (PRIORITY 5)
    # Need: Very easy (<3.8), very safe (none), short distance (<7km)
    for i, date in enumerate(["2024-01-13", "2024-01-30", "2024-02-16"]):
        trail_id = pick_unused(
            {"max_difficulty": 3.8, "safety_risks": "none", "max_distance": 7.0},
            fallback_criteria={"max_difficulty": 4.0, "safety_risks": "none", "max_distance": 8.0},
            require_match=True
        )
        if trail_id:
            completed.append((109, trail_id, date, 45 + i*3, 3 + (i % 2)))
    
    # User 113 (Mia) - Beginner, Medium fitness -> Family Hiker (PRIORITY 6)
    # Need: Very easy (<3.8), very safe (none), short (<6km)
    for i, date in enumerate(["2024-01-07", "2024-01-23", "2024-02-11"]):
        trail_id = pick_unused(
            {"max_difficulty": 3.8, "max_distance": 6.0, "safety_risks": "none"},
            fallback_criteria={"max_difficulty": 4.0, "max_distance": 7.0, "safety_risks": "none"},
            require_match=True
        )
        if trail_id:
            completed.append((113, trail_id, date, 28 + i*2, 3))
    
    # User 103 (Carol) - Intermediate, High fitness -> Contemplative Hiker (PRIORITY 7)
    # Need: Lakes/peaks landscapes, moderate popularity (6.5-7.5), scenic
    # Since only 3 trails match exactly, use a wider range but ensure peaks
    for i, date in enumerate(["2024-01-12", "2024-01-28", "2024-02-15"]):
        trail_id = pick_unused(
            {"landscapes": ["peaks"], "min_popularity": 6.5, "max_popularity": 7.5},
            fallback_criteria={"landscapes": ["peaks"], "min_popularity": 6.5, "max_popularity": 8.0},
            require_match=True
        )
        if trail_id:
            completed.append((103, trail_id, date, 90 + i*5, 4 + (i % 2)))
    
    # User 112 (Liam) - Intermediate, Medium fitness -> Contemplative (PRIORITY 8)
    # Need: Lakes/peaks, moderate popularity (6.5-7.5), scenic views
    # Ensure we get contemplative trails (peaks with moderate popularity)
    # Use wider fallback since only 3 trails match exactly
    for i, date in enumerate(["2024-01-17", "2024-02-03", "2024-02-20"]):
        trail_id = pick_unused(
            {"landscapes": ["peaks"], "min_popularity": 6.5, "max_popularity": 7.5},
            fallback_criteria={"landscapes": ["peaks"], "min_popularity": 6.5, "max_popularity": 8.0},
            require_match=True
        )
        if trail_id:
            completed.append((112, trail_id, date, 85 + i*4, 4 + (i % 2)))
    
    # User 101 (Alice) - Advanced, High fitness -> Elevation Enthusiast
    # Need: High elevation gain (>700m), moderate to high difficulty, can be any distance
    for i, date in enumerate(["2024-01-15", "2024-01-20", "2024-02-10", "2024-02-25"]):
        trail_id = pick_unused(
            {"min_elevation": 700, "min_difficulty": 6.0},
            fallback_criteria={"min_elevation": 600, "min_difficulty": 5.5}
        )
        if trail_id:
            completed.append((101, trail_id, date, 110 + i*20, 5))
    
    # User 105 (Emma) - Advanced, High fitness -> Performance Athlete
    # Need: Long distance (>10km), loops preferred, consistent difficulty
    for i, date in enumerate(["2024-01-25", "2024-01-18", "2024-02-12", "2024-02-28", "2024-03-10"]):
        trail_id = pick_unused(
            {"min_distance": 10.0, "trail_type": "loop"},
            fallback_criteria={"min_distance": 10.0}
        )
        if trail_id:
            completed.append((105, trail_id, date, 140 + i*10, 5))
    
    # User 106 (Frank) - Intermediate, Medium fitness -> Explorer
    # Need: Lower popularity (<8.5), diverse trails
    for i, date in enumerate(["2024-01-11", "2024-01-27", "2024-02-14"]):
        trail_id = pick_unused(
            {"max_popularity": 8.0},
            fallback_criteria={"max_popularity": 8.5}
        )
        if trail_id:
            completed.append((106, trail_id, date, 70 + i*3, 4 + (i % 2)))
    
    # User 108 (Henry) - Advanced, Medium fitness -> Elevation Enthusiast
    # Need: Very high elevation (>800m), challenging, moderate to high difficulty
    for i, date in enumerate(["2024-01-16", "2024-02-01", "2024-02-18", "2024-03-05"]):
        trail_id = pick_unused(
            {"min_elevation": 800, "min_difficulty": 6.5},
            fallback_criteria={"min_elevation": 700, "min_difficulty": 6.0}
        )
        if trail_id:
            completed.append((108, trail_id, date, 105 + i*5, 4 + (i % 2)))
    
    # User 111 (Kate) - Advanced, High fitness -> Photographer
    # Need: Lakes/peaks, one-way trails preferred, moderate duration (60-240 min)
    for i, date in enumerate(["2024-01-22", "2024-02-08", "2024-02-24", "2024-03-12"]):
        trail_id = pick_unused(
            {"landscapes": ["peaks"], "trail_type": "one_way"},
            fallback_criteria={"trail_type": "one_way", "min_difficulty": 4.0}
        )
        if trail_id:
            # Find the trail to get its duration
            trail_obj = next((t for t in trails if t.get("trail_id") == trail_id), None)
            if trail_obj:
                duration = trail_obj.get("duration", 120)
                if 60 <= duration <= 240:
                    completed.append((111, trail_id, date, duration + i*5, 5))
                else:
                    completed.append((111, trail_id, date, 140 + i*5, 5))
            else:
                completed.append((111, trail_id, date, 140 + i*5, 5))
    
    # User 114 (Noah) - Advanced, High fitness -> Performance Athlete
    # Need: Very long distance (>12km), loops preferred, consistent
    for i, date in enumerate(["2024-01-24", "2024-02-09", "2024-02-26", "2024-03-14", "2024-03-28", "2024-04-10"]):
        trail_id = pick_unused(
            {"min_distance": 12.0, "trail_type": "loop"},
            fallback_criteria={"min_distance": 12.0}
        )
        if trail_id:
            completed.append((114, trail_id, date, 155 + i*3, 5))
    
    # User 115 (Olivia) - Intermediate, High fitness -> Explorer
    # Need: Lower popularity, diverse trails
    for i, date in enumerate(["2024-01-19", "2024-02-06", "2024-02-22"]):
        trail_id = pick_unused(
            {"max_popularity": 8.0},
            fallback_criteria={}  # Any trail
        )
        if trail_id:
            completed.append((115, trail_id, date, 90 + i*3, 4 + (i % 2)))
    
    return completed
