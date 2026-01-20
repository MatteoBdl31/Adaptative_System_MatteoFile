# -*- coding: utf-8 -*-
"""
Ranking system for trail recommendations.
Separates exact matches from suggestions and ranks them.
"""

from typing import Dict, List, Tuple, Optional
from backend.weather_service import weather_matches
import logging

logger = logging.getLogger(__name__)


class TrailRanker:
    """Ranks and categorizes trails into exact matches and suggestions."""
    
    def __init__(self, exact_match_threshold: float = 80.0):
        """
        Args:
            exact_match_threshold: Minimum relevance percentage for exact match (0-100)
            Default is 80.0 (80%) for more lenient matching
        """
        self.exact_match_threshold = exact_match_threshold
    
    def rank_trails(
        self, 
        trails: List[Dict], 
        filters: Dict, 
        user: Dict, 
        context: Dict,
        debugger=None
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Rank trails and separate into exact matches and suggestions.
        
        Args:
            trails: List of scored trails
            filters: Active filters
            user: User profile
            context: Context data
            debugger: Optional RecommendationDebugger instance for logging
        
        Returns:
            (exact_matches, suggestions)
        """
        logger.debug(f"Ranking {len(trails)} trails with threshold {self.exact_match_threshold}%")
        
        # Apply hard filters (safety, season, fear of heights)
        filtered_trails = self._apply_hard_filters(trails, filters, user, context, debugger)
        
        # Separate exact matches from suggestions
        exact_matches = []
        suggestions = []
        below_threshold_count = 0
        filter_failed_count = 0
        
        for trail in filtered_trails:
            relevance = trail.get("relevance_percentage", 0.0)
            
            # Check if it's an exact match
            if relevance < self.exact_match_threshold:
                below_threshold_count += 1
                suggestions.append(trail)
            elif self._is_exact_match(trail, filters, user, context, relevance):
                exact_matches.append(trail)
            else:
                filter_failed_count += 1
                suggestions.append(trail)
        
        # Sort exact matches by relevance, then popularity
        exact_matches.sort(
            key=lambda x: (x.get("relevance_percentage", 0), x.get("popularity", 0)),
            reverse=True
        )
        
        # Sort suggestions by relevance, then popularity
        suggestions.sort(
            key=lambda x: (x.get("relevance_percentage", 0), x.get("popularity", 0)),
            reverse=True
        )
        
        logger.debug(f"Ranking results: {len(exact_matches)} exact matches, {len(suggestions)} suggestions "
                     f"(below threshold: {below_threshold_count}, filter failed: {filter_failed_count})")
        
        return exact_matches, suggestions
    
    def _apply_hard_filters(
        self, 
        trails: List[Dict], 
        filters: Dict, 
        user: Dict, 
        context: Dict,
        debugger=None
    ) -> List[Dict]:
        """Apply hard filters that cannot be violated."""
        filtered = []
        filtered_out_count = {
            "season": 0,
            "fear_of_heights": 0,
            "weather": 0
        }
        
        for trail in trails:
            trail_id = trail.get("trail_id", "unknown")
            filtered_out = False
            filter_reason = None
            
            # Season filter
            if filters.get("avoid_closed") and context.get("season"):
                season = context["season"].lower()
                closed_seasons = (trail.get("closed_seasons") or "").lower()
                if season in closed_seasons:
                    filtered_out_count["season"] += 1
                    filtered_out = True
                    filter_reason = f"Closed in {season}"
                    if debugger:
                        debugger.log_trail_filtered_out(trail_id, filter_reason, "season")
                    logger.debug(f"Trail {trail_id} filtered: {filter_reason}")
                    continue
            
            # Fear of heights
            if user.get("fear_of_heights"):
                safety_risks = (trail.get("safety_risks") or "").lower()
                if "heights" in safety_risks:
                    filtered_out_count["fear_of_heights"] += 1
                    filtered_out = True
                    filter_reason = "Contains heights exposure"
                    if debugger:
                        debugger.log_trail_filtered_out(trail_id, filter_reason, "fear_of_heights")
                    logger.debug(f"Trail {trail_id} filtered: {filter_reason}")
                    continue
            
            # Weather filter (if forecast available and doesn't match)
            # Only filter out truly dangerous weather conditions
            hike_date = context.get("hike_start_date") or context.get("hike_date")
            desired_weather = (context.get("weather", "sunny") or "").lower()
            forecast_weather = trail.get("forecast_weather")
            
            if hike_date and desired_weather and forecast_weather:
                forecast_weather = forecast_weather.lower()
                # Only filter out truly dangerous weather (storm_risk)
                # Other mismatches are handled by scoring, allowing flexibility
                if forecast_weather == "storm_risk":
                    # Storm risk is dangerous regardless of desired weather
                    filtered_out_count["weather"] += 1
                    filtered_out = True
                    filter_reason = "Storm risk forecast"
                    if debugger:
                        debugger.log_trail_filtered_out(trail_id, filter_reason, "weather")
                    logger.debug(f"Trail {trail_id} filtered: {filter_reason}")
                    continue
                
                # For other weather conditions, let them through
                # They'll be scored appropriately by WeatherCriterion
                # This allows users to see trails even if weather isn't perfect
            
            filtered.append(trail)
        
        logger.debug(f"Hard filters applied: {len(filtered)}/{len(trails)} trails passed. Filtered out: {filtered_out_count}")
        
        return filtered
    
    def _is_exact_match(
        self, 
        trail: Dict, 
        filters: Dict, 
        user: Dict, 
        context: Dict, 
        relevance: float
    ) -> bool:
        """Determine if a trail is an exact match."""
        # Must meet relevance threshold
        if relevance < self.exact_match_threshold:
            return False
        
        # Check critical criteria
        matched = trail.get("matched_criteria", [])
        unmatched = trail.get("unmatched_criteria", [])
        
        # Extract criterion names from matched/unmatched (handle both dict and string formats)
        matched_names = []
        for m in matched:
            if isinstance(m, dict):
                matched_names.append(m.get("name", ""))
            else:
                matched_names.append(str(m))
        
        unmatched_names = []
        for u in unmatched:
            if isinstance(u, dict):
                unmatched_names.append(u.get("name", ""))
            else:
                unmatched_names.append(str(u))
        
        # Critical criteria that must match (only if they were evaluated)
        critical_criteria = ["safety", "duration"]
        for crit in critical_criteria:
            if crit not in matched_names:
                # Only fail if it was explicitly unmatched
                if crit in unmatched_names:
                    return False
                # If not evaluated, that's okay (criterion might not apply)
        
        # Check if all filters are satisfied
        # Duration filter
        if "max_duration" in filters:
            trail_duration = trail.get("duration")
            if trail_duration and trail_duration > filters["max_duration"]:
                return False
        
        # Difficulty filter
        if "max_difficulty" in filters:
            trail_difficulty = trail.get("difficulty", 0)
            if trail_difficulty > filters["max_difficulty"]:
                return False
        
        # Distance filter - Note: max_distance should already be removed for multi-day trips by FilterBuilder
        # This check is a safety net in case max_distance somehow still exists
        if "max_distance" in filters:
            trail_distance = trail.get("distance")
            trail_duration = trail.get("duration", 0)
            time_available = context.get("time_available", 0)
            
            if trail_distance:
                # For multi-day hikes, be lenient (though max_distance should be removed by FilterBuilder)
                is_multi_day = (trail_duration >= 1440) or (time_available >= 1440)
                if is_multi_day:
                    # Allow up to 3x the limit for multi-day (safety net)
                    max_allowed = filters["max_distance"] * 3
                    if trail_distance > max_allowed:
                        return False
                else:
                    # Single-day hikes: strict limit
                    if trail_distance > filters["max_distance"]:
                        return False
        
        # Elevation filter
        if "max_elevation" in filters:
            trail_elevation = trail.get("elevation_gain")
            if trail_elevation and trail_elevation > filters["max_elevation"]:
                return False
        
        # Landscape filter
        if "landscape_filter" in filters:
            landscapes = (trail.get("landscapes") or "").lower()
            if filters["landscape_filter"].lower() not in landscapes:
                return False
        
        return True

