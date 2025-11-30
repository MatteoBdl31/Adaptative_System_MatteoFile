# -*- coding: utf-8 -*-

from backend.db import get_rules, filter_trails, get_all_trails
from backend.weather_service import get_weather_for_trail, weather_matches


def _prepare_trail_metadata(trail):
    if not trail:
        return {}
    profile = trail.get("elevation_profile") or []
    if profile:
        elevations = [point.get("elevation_m", 0) for point in profile]
        if elevations:
            trail["max_elevation"] = max(elevations)
            trail["min_elevation"] = min(elevations)
        trail["elevation_samples"] = len(profile)
    trail["region_label"] = trail.get("region", "french_alps").replace("_", " ").title()
    return trail


def _is_low_risk(trail):
    safety = (trail.get("safety_risks") or "").lower()
    return safety in ("", "none", "low")


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
            # Special handling for weather: check forecasted weather, not desired
            elif key == "weather":
                # For weather conditions in rules, use forecasted weather if available
                # This allows rules like "weather=rainy" to trigger based on forecast
                hike_start_date = context.get("hike_start_date") or context.get("hike_date")
                if hike_start_date:
                    # We need to get forecast for a representative trail location
                    # For rule evaluation, we'll use the desired weather as fallback
                    # The actual forecast will be checked per-trail in calculate_relevance_score
                    # For now, use context weather (rules will be evaluated per-trail later)
                    effective_weather = context.get("weather", "sunny")
                    if effective_weather != val:
                        return False
                elif context.get("weather") != val:
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
    unmatched_criteria = []
    total_criteria = 0
    
    # Helper to format criteria messages
    def format_criteria_message(criteria_name, trail_value, filter_value, comparison=""):
        """Format a human-readable message about why a criterion didn't match"""
        if criteria_name == "difficulty":
            if "max" in criteria_name.lower() or "max_difficulty" in str(filter_value):
                return f"Difficulty too high ({trail_value:.1f} > {filter_value:.1f})"
            else:
                return f"Difficulty too low ({trail_value:.1f} < {filter_value:.1f})"
        elif criteria_name == "distance":
            if "max" in criteria_name.lower() or "max_distance" in str(filter_value):
                return f"Too long ({trail_value:.1f} km > {filter_value:.1f} km)"
            else:
                return f"Too short ({trail_value:.1f} km < {filter_value:.1f} km)"
        elif criteria_name == "duration":
            return f"Too long ({trail_value} min > {filter_value} min)"
        elif criteria_name == "elevation":
            return f"Elevation too high ({trail_value} m > {filter_value} m)"
        elif criteria_name == "landscape":
            return f"Missing landscape: {filter_value}"
        elif criteria_name == "safety":
            return "Safety concerns present"
        elif criteria_name == "season":
            return f"Closed in {context.get('season', 'this season')}"
        elif criteria_name == "fitness":
            if user.get("fitness_level", "").lower() == "low":
                return f"Too challenging (elevation: {trail_value} m)"
            else:
                return f"Not challenging enough (elevation: {trail_value} m)"
        elif criteria_name == "preferences":
            return f"Doesn't match preferences: {', '.join(user.get('preferences', []))}"
        elif criteria_name == "weather":
            return "Not suitable for current weather"
        else:
            return f"Doesn't match {criteria_name}"
    
    # Check difficulty
    if "max_difficulty" in filters:
        total_criteria += 1
        trail_difficulty = trail.get("difficulty", 0)
        if trail_difficulty <= filters["max_difficulty"]:
            score += 1
            matched_criteria.append("difficulty")
        else:
            unmatched_criteria.append(format_criteria_message("difficulty", trail_difficulty, filters["max_difficulty"]))
    if "min_difficulty" in filters:
        total_criteria += 1
        trail_difficulty = trail.get("difficulty", 0)
        min_required = filters["min_difficulty"]
        if trail_difficulty >= min_required:
            score += 1
            matched_criteria.append("difficulty")
        else:
            unmatched_criteria.append(f"Difficulty too low ({trail_difficulty:.1f} < {min_required:.1f})")
    
    # Check distance
    if "max_distance" in filters:
        total_criteria += 1
        trail_distance = trail.get("distance")
        if trail_distance and trail_distance <= filters["max_distance"]:
            score += 1
            matched_criteria.append("distance")
        elif trail_distance:
            unmatched_criteria.append(format_criteria_message("distance", trail_distance, filters["max_distance"]))
    if "min_distance" in filters:
        # Only check min_distance if max_duration allows for longer trails
        # If max_duration is very restrictive (< 60 min), skip min_distance check to avoid contradictions
        max_duration = filters.get("max_duration", float('inf'))
        if max_duration >= 60:  # Only enforce min_distance if we have reasonable time
            total_criteria += 1
            trail_distance = trail.get("distance")
            if trail_distance and trail_distance >= filters["min_distance"]:
                score += 1
                matched_criteria.append("distance")
            elif trail_distance:
                unmatched_criteria.append(format_criteria_message("distance", trail_distance, filters["min_distance"]))
    
    # Check duration
    if "max_duration" in filters:
        total_criteria += 1
        trail_duration = trail.get("duration")
        if trail_duration and trail_duration <= filters["max_duration"]:
            score += 1
            matched_criteria.append("duration")
        elif trail_duration:
            unmatched_criteria.append(f"Too long ({trail_duration} min > {filters['max_duration']} min)")
    
    # Check elevation
    if "max_elevation" in filters:
        total_criteria += 1
        trail_elevation = trail.get("elevation_gain")
        if trail_elevation and trail_elevation <= filters["max_elevation"]:
            score += 1
            matched_criteria.append("elevation")
        elif trail_elevation:
            unmatched_criteria.append(f"Elevation too high ({trail_elevation} m > {filters['max_elevation']} m)")
    
    # Check landscape
    if "landscape_filter" in filters:
        total_criteria += 1
        landscapes = trail.get("landscapes", "").lower()
        if filters["landscape_filter"].lower() in landscapes:
            score += 1
            matched_criteria.append("landscape")
        else:
            unmatched_criteria.append(f"Missing landscape: {filters['landscape_filter']}")
    
    # Check safety (avoid_risky)
    if filters.get("avoid_risky"):
        total_criteria += 1
        if _is_low_risk(trail):
            score += 1
            matched_criteria.append("safety")
        else:
            unmatched_criteria.append("Safety concerns present")
    
    # Check season (avoid_closed)
    if filters.get("avoid_closed") and context.get("season"):
        total_criteria += 1
        closed_seasons = trail.get("closed_seasons", "").lower()
        if context["season"].lower() not in closed_seasons:
            score += 1
            matched_criteria.append("season")
        else:
            unmatched_criteria.append(f"Closed in {context['season']}")
    
    # Check fear of heights
    if user.get("fear_of_heights"):
        total_criteria += 1
        safety_risks = trail.get("safety_risks", "").lower()
        if "heights" not in safety_risks:
            score += 1
            matched_criteria.append("safety")
        else:
            unmatched_criteria.append("Contains heights exposure")

    # Weather-aware safety boost (based on FORECASTED weather if available, otherwise desired weather)
    # For filtered trails, forecast_weather will be available; for others, use desired weather
    hike_start_date = context.get("hike_start_date") or context.get("hike_date")
    desired_weather = context.get("weather", "sunny")
    
    # Use forecasted weather if available (for filtered trails), otherwise use desired weather
    forecast_weather = trail.get("forecast_weather")
    effective_weather = forecast_weather if forecast_weather else desired_weather
    
    if effective_weather:
        # Bad weather conditions require safer trails
        if effective_weather in {"rainy", "snowy", "storm_risk"}:
            total_criteria += 1
            if _is_low_risk(trail):
                score += 1
                matched_criteria.append("weather_safety")
            else:
                unmatched_criteria.append(f"Not suitable for {effective_weather} weather conditions")
    
    # Weather preference matching (compare desired weather with forecast)
    if hike_start_date and desired_weather and forecast_weather:
        total_criteria += 1
        if weather_matches(desired_weather, forecast_weather):
            score += 1
            matched_criteria.append("weather_preference")
        else:
            unmatched_criteria.append(f"Weather forecast ({forecast_weather}) doesn't match desired ({desired_weather})")

    # Time alignment - use max_duration from filters if available (which includes smart buffer),
    # otherwise calculate based on time_available with smart buffer logic
    # This ensures consistency with the filtering logic
    if context.get("time_available") and trail.get("duration"):
        total_criteria += 1
        trail_duration = trail["duration"]
        time_available = context["time_available"]
        
        # Use max_duration from filters if set, otherwise calculate
        if "max_duration" in filters:
            max_allowed = filters["max_duration"]
        else:
            # No buffer for single day hikes (user removed hours input)
            if time_available < 1440:  # Less than 1 day
                max_allowed = time_available  # NO buffer
            else:
                # For multi-day, round up to next day boundary
                days = (time_available // 1440) + 1
                max_allowed = days * 1440
        
        if trail_duration <= max_allowed:
            score += 1
            matched_criteria.append("duration")
        else:
            # Format the message nicely
            if time_available < 1440:
                time_str = f"{time_available} min"
                max_str = f"{max_allowed} min"
            else:
                avail_days = time_available // 1440
                max_days = max_allowed // 1440
                time_str = f"{avail_days} day{'s' if avail_days != 1 else ''}"
                max_str = f"{max_days} day{'s' if max_days != 1 else ''}"
            unmatched_criteria.append(f"Too long ({trail_duration} min > {max_str} available)")

    # Fitness vs elevation gain
    fitness = (user.get("fitness_level") or "").lower()
    elevation_gain = trail.get("elevation_gain") or 0
    if fitness == "low":
        total_criteria += 1
        if elevation_gain <= 400:
            score += 1
            matched_criteria.append("fitness")
        else:
            unmatched_criteria.append(f"Too challenging for fitness level (elevation: {elevation_gain} m)")
    elif fitness == "high":
        total_criteria += 1
        if elevation_gain >= 400:
            score += 1
            matched_criteria.append("fitness")
        else:
            unmatched_criteria.append(f"Not challenging enough (elevation: {elevation_gain} m)")
    
    # Check user preferences (landscape preferences)
    user_preferences = user.get("preferences", [])
    if user_preferences:
        total_criteria += 1
        trail_landscapes = [l.strip().lower() for l in trail.get("landscapes", "").split(",") if l.strip()]
        if any(pref.lower() in trail_landscapes for pref in user_preferences):
            score += 1
            matched_criteria.append("preferences")
        else:
            unmatched_criteria.append(f"Doesn't match preferences: {', '.join(user_preferences)}")
    
    # Calculate relevance percentage
    # If no criteria exist, set relevance to 50% as a neutral score (will be sorted by popularity)
    if total_criteria == 0:
        relevance = 50.0
    elif score == total_criteria:
        # Explicitly set to 100.0 for perfect matches to avoid floating point issues
        relevance = 100.0
    else:
        relevance = (score / total_criteria * 100)
    
    return {
        "score": score,
        "total_criteria": total_criteria,
        "relevance": relevance,
        "matched_criteria": matched_criteria,
        "unmatched_criteria": unmatched_criteria
    }

def adapt_trails(user, context):
    """Main adaptation function for trail recommendations"""
    filters = {"region": "french_alps", "is_real": True}
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
    
    # Automatically set max_duration from time_available if not already set by rules
    # Apply smart buffer logic:
    # - For trails < 1 day: NO buffer (user requested no minutes/hours input)
    # - For trails >= 1 day: match day counts (no buffer, round to nearest day)
    # IMPORTANT: If rules set max_duration for short trips, but user has multi-day context,
    # override the rule to respect the multi-day intent
    time_available = context.get("time_available")
    if time_available:
        # If user has multi-day availability (>= 1 day) but a rule set a very short max_duration (< 1 day), override it
        # This prevents rules like "Limited time" or "Low persistence" from overriding multi-day trip intent
        if time_available >= 1440 and filters.get("max_duration") and filters["max_duration"] < 1440:
            # User wants multi-day trip, but rule set short duration - override
            days = (time_available // 1440) + 1
            filters["max_duration"] = days * 1440
            # Also remove restrictive distance filters for multi-day trips (rules often set max_distance < 10km)
            if filters.get("max_distance") and filters["max_distance"] < 15:
                # Multi-day trips typically need more distance, remove restrictive distance filter
                filters.pop("max_distance", None)
            # Remove prefer_short flag for multi-day trips
            if filters.get("prefer_short"):
                filters.pop("prefer_short", None)
        elif "max_duration" not in filters:
            # No rule set max_duration, calculate from time_available
            if time_available < 1440:  # Less than 24 hours (1 day)
                # NO buffer for single day hikes (user removed hours input)
                # But ensure minimum of 1 hour (60 min) to avoid overly restrictive filters
                filters["max_duration"] = max(60, time_available) if time_available > 0 else 480  # Default to 8 hours if 0
            else:
                # For multi-day trails, round up to the next day boundary
                # This allows flexibility within the same day count
                days = (time_available // 1440) + 1  # Round up to next day
                filters["max_duration"] = days * 1440  # Exact day boundary
        
        # Fix contradictory filters: if max_duration is very restrictive (< 60 min), remove min_distance
        # because short time windows can't accommodate long distance requirements
        # Also ensure max_duration is never 0 or too small
        if filters.get("max_duration"):
            if filters["max_duration"] < 60:
                # If max_duration is too restrictive, set minimum to 60 minutes
                filters["max_duration"] = 60
                if filters.get("min_distance"):
                    filters.pop("min_distance", None)
                if filters.get("min_difficulty"):
                    filters.pop("min_difficulty", None)
    
    # Get all trails for relevance calculation
    all_trails = [_prepare_trail_metadata(trail) for trail in get_all_trails()]
    
    # Post-filter for season-based closures
    avoid_closed = filters.get("avoid_closed", False)
    if avoid_closed and context.get("season"):
        season = context["season"]
        all_trails = [t for t in all_trails if not t.get("closed_seasons") or season not in t.get("closed_seasons", "")]
    
    # Filter out trails with heights if user has fear of heights
    if user.get("fear_of_heights"):
        all_trails = [t for t in all_trails if "heights" not in t.get("safety_risks", "")]
    
    # Optional: Pre-filter trails by weather forecast if desired weather is specified
    # This can be enabled to strictly filter out trails with mismatched weather
    # For now, we'll use it in scoring only (not filtering) to show all trails but rank by weather match
    # Uncomment below to enable strict weather filtering:
    # hike_date = context.get("hike_date")
    # desired_weather = context.get("weather")
    # if hike_date and desired_weather:
    #     all_trails = [t for t in all_trails if weather_matches(desired_weather, get_weather_for_trail(t, hike_date))]
    
    # Calculate relevance for all trails (without fetching weather - that's expensive!)
    trails_with_relevance = []
    for trail in all_trails:
        relevance_info = calculate_relevance_score(trail, filters, user, context, active_rules)
        trail["relevance_score"] = relevance_info["score"]
        trail["relevance_total"] = relevance_info["total_criteria"]
        trail["relevance_percentage"] = relevance_info["relevance"]
        trail["matched_criteria"] = relevance_info["matched_criteria"]
        trail["unmatched_criteria"] = relevance_info["unmatched_criteria"]
        # Don't fetch weather here - only fetch for trails that will be displayed
        trail["forecast_weather"] = None
        trails_with_relevance.append(trail)
    
    # Separate exact matches (recommendations) from suggestions
    exact_matches = []
    suggestions = []
    
    # Step 1: Filter trails with all criteria EXCEPT weather (to minimize API calls)
    filters_copy = filters.copy()
    # Remove any weather-related filters for initial filtering (we'll apply weather after fetching)
    # Note: Weather filters aren't typically in filters dict, but we ensure clean filtering
    
    if filters_copy:
        exact_matches = [_prepare_trail_metadata(trail) for trail in filter_trails(filters_copy)]
        # Post-filter exact matches for season and fear of heights
        if avoid_closed and context.get("season"):
            season = context["season"]
            exact_matches = [t for t in exact_matches if not t.get("closed_seasons") or season not in t.get("closed_seasons", "")]
        if user.get("fear_of_heights"):
            exact_matches = [t for t in exact_matches if "heights" not in t.get("safety_risks", "")]
    else:
        exact_matches = []
    
    # Step 2: Fetch weather for filtered trails
    hike_start_date = context.get("hike_start_date") or context.get("hike_date")
    desired_weather = context.get("weather", "sunny")
    
    if hike_start_date:
        for trail in exact_matches:
            trail["forecast_weather"] = None
            try:
                forecast_weather = get_weather_for_trail(trail, hike_start_date)
                trail["forecast_weather"] = forecast_weather
            except Exception as e:
                trail["forecast_weather"] = None
                print(f"Warning: Could not retrieve weather for trail {trail.get('trail_id')}: {e}")
    
    # Step 3: Re-filter/recalculate with weather conditions included
    if hike_start_date and desired_weather:
        # Filter out trails with mismatched weather (if forecast is available)
        weather_filtered_matches = []
        for trail in exact_matches:
            forecast_weather = trail.get("forecast_weather")
            # Only filter out if we have a forecast AND it doesn't match
            # If no forecast available, keep the trail (don't penalize for API failures)
            if forecast_weather is None or weather_matches(desired_weather, forecast_weather):
                weather_filtered_matches.append(trail)
            # If forecast exists and doesn't match, exclude from exact matches
            # (but we could add them to suggestions later)
        
        exact_matches = weather_filtered_matches
    
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
    
    # Step 4: Recalculate relevance with weather included for exact matches
    for trail in exact_matches:
        trail["recommendation_reasons"] = []
        for rule in active_rules:
            if rule.get("description"):
                trail["recommendation_reasons"].append(rule["description"])
        
        # Recalculate relevance with weather conditions now included
        # (weather forecast is already fetched and stored in trail["forecast_weather"])
        relevance_info = calculate_relevance_score(trail, filters, user, context, active_rules)
        trail["relevance_score"] = relevance_info["score"]
        trail["relevance_total"] = relevance_info["total_criteria"]
        
        # Recalculate relevance percentage
        if relevance_info["total_criteria"] > 0:
            trail["relevance_percentage"] = (relevance_info["score"] / relevance_info["total_criteria"] * 100)
        else:
            trail["relevance_percentage"] = 100.0
        
        trail["matched_criteria"] = relevance_info["matched_criteria"]
        trail["unmatched_criteria"] = relevance_info["unmatched_criteria"]
    
    # Limit number of trails
    max_trails = display_settings.get("max_trails", 10)
    exact_matches = exact_matches[:max_trails]
    suggestions = suggestions[:max_trails]
    
    # Only fetch weather for suggestions that will actually be displayed (limited to max_trails)
    if hike_start_date:
        desired_weather = context.get("weather", "sunny")
        # Fetch weather for suggestions that will be displayed
        for trail in suggestions:
            trail["forecast_weather"] = None
            try:
                forecast_weather = get_weather_for_trail(trail, hike_start_date)
                trail["forecast_weather"] = forecast_weather
                # Add weather preference matching for displayed trails
                if forecast_weather and desired_weather and weather_matches(desired_weather, forecast_weather):
                    if "weather_preference" not in trail.get("matched_criteria", []):
                        trail["matched_criteria"].append("weather_preference")
            except Exception as e:
                trail["forecast_weather"] = None
                print(f"Warning: Could not retrieve weather for trail {trail.get('trail_id')}: {e}")
    
    return exact_matches, suggestions, display_settings, active_rules

