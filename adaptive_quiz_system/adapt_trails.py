# -*- coding: utf-8 -*-

from backend.db import get_rules, filter_trails, get_all_trails

def evaluate_condition(condition, user, context):
    """Evaluate a condition string against user and context"""
    clauses = condition.split("AND")
    for clause in clauses:
        clause = clause.strip()
        if "=" in clause and "CONTAINS" not in clause:
            key, val = clause.split("=")
            key, val = key.strip(), val.strip()
            # Check user attributes
            if key in user and str(user[key]) != val:
                return False
            # Check context attributes
            elif key in context and str(context[key]) != val:
                return False
            # Check performance attributes
            elif key.startswith("performance."):
                perf_key = key.split(".")[1]
                if user.get("performance", {}).get(perf_key, 0) != float(val):
                    return False
        elif "<=" in clause:
            key, val = clause.split("<=")
            key, val = key.strip(), val.strip()
            # Check context
            if key in context:
                try:
                    if int(context.get(key, 9999)) > int(val):
                        return False
                except (ValueError, TypeError):
                    pass
            # Check performance (without performance. prefix)
            elif key in user.get("performance", {}):
                if user["performance"][key] > float(val):
                    return False
            # Check performance with performance. prefix
            elif key.startswith("performance."):
                perf_key = key.split(".")[1]
                if user.get("performance", {}).get(perf_key, 0) > float(val):
                    return False
        elif ">=" in clause:
            key, val = clause.split(">=")
            key, val = key.strip(), val.strip()
            # Check context
            if key in context and int(context.get(key, 0)) < int(val):
                return False
            # Check performance
            elif key.startswith("performance."):
                perf_key = key.split(".")[1]
                if user.get("performance", {}).get(perf_key, 0) < float(val):
                    return False
        elif "CONTAINS" in clause:
            key, val = clause.split("CONTAINS")
            key, val = key.strip(), val.strip()
            # Check if value is in user preferences
            if key == "landscape_preference":
                if val not in user.get("preferences", []):
                    return False
            elif val not in user.get(key, []):
                return False
    return True

def apply_adaptation(filters, adaptation):
    """Apply adaptation rules to filter dictionary"""
    for rule in adaptation.split(";"):
        if "=" in rule:
            key, val = rule.split("=")
            key, val = key.strip(), val.strip()
            if key == "max_difficulty":
                # Map easy/medium/hard to numeric values
                if val == "easy":
                    filters["max_difficulty"] = 3.0
                elif val == "medium":
                    filters["max_difficulty"] = 6.0
                elif val == "hard":
                    filters["max_difficulty"] = 10.0
                else:
                    filters["max_difficulty"] = float(val)
            elif key == "min_difficulty":
                if val == "easy":
                    filters["min_difficulty"] = 1.0
                elif val == "medium":
                    filters["min_difficulty"] = 4.0
                elif val == "hard":
                    filters["min_difficulty"] = 7.0
                else:
                    filters["min_difficulty"] = float(val)
            elif key in ["max_distance", "min_distance", "max_duration", "max_elevation"]:
                filters[key] = float(val) if "." in val else int(val)
            elif key == "landscape_filter":
                filters["landscape_filter"] = val
            elif key == "prefer_peaks":
                filters["prefer_peaks"] = True
            elif key == "prefer_short":
                filters["prefer_short"] = True
            elif key == "avoid_risky":
                filters["avoid_risky"] = True
            elif key == "avoid_closed":
                filters["avoid_closed"] = True
            elif key == "prefer_safe":
                filters["avoid_risky"] = True  # prefer_safe is same as avoid_risky
            elif key == "display_mode":
                filters["display_mode"] = val
            elif key == "max_trails":
                filters["max_trails"] = int(val)
            elif key == "hide_images":
                filters["hide_images"] = val.lower() == "true"
    return filters

def calculate_relevance_score(trail, filters, user, context, active_rules):
    """Calculate relevance score for a trail based on how many criteria it matches"""
    score = 0
    matched_criteria = []
    total_criteria = 0
    
    # Check difficulty
    if "max_difficulty" in filters:
        total_criteria += 1
        if trail.get("difficulty", 0) <= filters["max_difficulty"]:
            score += 1
            matched_criteria.append("difficulty")
    if "min_difficulty" in filters:
        total_criteria += 1
        if trail.get("difficulty", 0) >= filters["min_difficulty"]:
            score += 1
            matched_criteria.append("difficulty")
    
    # Check distance
    if "max_distance" in filters:
        total_criteria += 1
        if trail.get("distance") and trail["distance"] <= filters["max_distance"]:
            score += 1
            matched_criteria.append("distance")
    if "min_distance" in filters:
        total_criteria += 1
        if trail.get("distance") and trail["distance"] >= filters["min_distance"]:
            score += 1
            matched_criteria.append("distance")
    
    # Check duration
    if "max_duration" in filters:
        total_criteria += 1
        if trail.get("duration") and trail["duration"] <= filters["max_duration"]:
            score += 1
            matched_criteria.append("duration")
    
    # Check elevation
    if "max_elevation" in filters:
        total_criteria += 1
        if trail.get("elevation_gain") and trail["elevation_gain"] <= filters["max_elevation"]:
            score += 1
            matched_criteria.append("elevation")
    
    # Check landscape
    if "landscape_filter" in filters:
        total_criteria += 1
        landscapes = trail.get("landscapes", "").lower()
        if filters["landscape_filter"].lower() in landscapes:
            score += 1
            matched_criteria.append("landscape")
    
    # Check safety (avoid_risky)
    if filters.get("avoid_risky"):
        total_criteria += 1
        safety_risks = trail.get("safety_risks", "").lower()
        if safety_risks in ["none", "low", ""]:
            score += 1
            matched_criteria.append("safety")
    
    # Check season (avoid_closed)
    if filters.get("avoid_closed") and context.get("season"):
        total_criteria += 1
        closed_seasons = trail.get("closed_seasons", "").lower()
        if context["season"].lower() not in closed_seasons:
            score += 1
            matched_criteria.append("season")
    
    # Check fear of heights
    if user.get("fear_of_heights"):
        total_criteria += 1
        safety_risks = trail.get("safety_risks", "").lower()
        if "heights" not in safety_risks:
            score += 1
            matched_criteria.append("safety")
    
    # Check user preferences (landscape preferences)
    user_preferences = user.get("preferences", [])
    if user_preferences:
        total_criteria += 1
        trail_landscapes = [l.strip().lower() for l in trail.get("landscapes", "").split(",") if l.strip()]
        if any(pref.lower() in trail_landscapes for pref in user_preferences):
            score += 1
            matched_criteria.append("preferences")
    
    # Calculate relevance percentage
    # If no criteria exist, set relevance to 50% as a neutral score (will be sorted by popularity)
    if total_criteria == 0:
        relevance = 50.0
    else:
        relevance = (score / total_criteria * 100)
    
    return {
        "score": score,
        "total_criteria": total_criteria,
        "relevance": relevance,
        "matched_criteria": matched_criteria
    }

def adapt_trails(user, context):
    """Main adaptation function for trail recommendations"""
    filters = {}
    display_settings = {"display_mode": "full", "max_trails": 10, "hide_images": False}
    
    rules = get_rules()
    active_rules = []
    
    for rule in rules:
        if evaluate_condition(rule["condition"], user, context):
            filters = apply_adaptation(filters, rule["adaptation"])
            active_rules.append(rule)
    
    # Apply display settings from filters
    if "display_mode" in filters:
        display_settings["display_mode"] = filters.pop("display_mode")
    if "max_trails" in filters:
        display_settings["max_trails"] = filters.pop("max_trails")
    if "hide_images" in filters:
        display_settings["hide_images"] = filters.pop("hide_images")
    
    # Get all trails for relevance calculation
    all_trails = get_all_trails()
    
    # Post-filter for season-based closures
    avoid_closed = filters.get("avoid_closed", False)
    if avoid_closed and context.get("season"):
        season = context["season"]
        all_trails = [t for t in all_trails if not t.get("closed_seasons") or season not in t.get("closed_seasons", "")]
    
    # Filter out trails with heights if user has fear of heights
    if user.get("fear_of_heights"):
        all_trails = [t for t in all_trails if "heights" not in t.get("safety_risks", "")]
    
    # Calculate relevance for all trails
    trails_with_relevance = []
    for trail in all_trails:
        relevance_info = calculate_relevance_score(trail, filters, user, context, active_rules)
        trail["relevance_score"] = relevance_info["score"]
        trail["relevance_total"] = relevance_info["total_criteria"]
        trail["relevance_percentage"] = relevance_info["relevance"]
        trail["matched_criteria"] = relevance_info["matched_criteria"]
        trails_with_relevance.append(trail)
    
    # Separate exact matches (recommendations) from suggestions
    exact_matches = []
    suggestions = []
    
    # Get filtered trails (exact matches)
    filters_copy = filters.copy()
    if filters_copy:
        exact_matches = filter_trails(filters_copy)
        # Post-filter exact matches for season and fear of heights
        if avoid_closed and context.get("season"):
            season = context["season"]
            exact_matches = [t for t in exact_matches if not t.get("closed_seasons") or season not in t.get("closed_seasons", "")]
        if user.get("fear_of_heights"):
            exact_matches = [t for t in exact_matches if "heights" not in t.get("safety_risks", "")]
    
    # Get exact match IDs to exclude from suggestions
    exact_match_ids = {t["trail_id"] for t in exact_matches}
    
    # Get suggestions (trails not in exact matches, sorted by relevance)
    # If no filters exist, all trails become suggestions sorted by popularity
    suggestions = [t for t in trails_with_relevance if t["trail_id"] not in exact_match_ids]
    if filters:
        # Sort by relevance when filters exist
        suggestions.sort(key=lambda x: (x["relevance_percentage"], x.get("popularity", 0)), reverse=True)
    else:
        # Sort by popularity when no filters exist
        suggestions.sort(key=lambda x: x.get("popularity", 0), reverse=True)
    
    # Add recommendation reasons to exact matches
    for trail in exact_matches:
        trail["recommendation_reasons"] = []
        for rule in active_rules:
            if rule.get("description"):
                trail["recommendation_reasons"].append(rule["description"])
        # Add relevance info
        relevance_info = calculate_relevance_score(trail, filters, user, context, active_rules)
        trail["relevance_score"] = relevance_info["score"]
        trail["relevance_total"] = relevance_info["total_criteria"]
        trail["relevance_percentage"] = relevance_info["relevance"]
        trail["matched_criteria"] = relevance_info["matched_criteria"]
    
    # Limit number of trails
    max_trails = display_settings.get("max_trails", 10)
    exact_matches = exact_matches[:max_trails]
    suggestions = suggestions[:max_trails]
    
    return exact_matches, suggestions, display_settings, active_rules

