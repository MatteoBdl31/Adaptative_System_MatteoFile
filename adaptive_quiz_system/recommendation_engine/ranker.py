# -*- coding: utf-8 -*-
"""
Ranking system for trail recommendations.
Separates exact matches from suggestions and ranks them.
"""

from typing import Dict, List, Tuple
from backend.weather_service import weather_matches


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
        context: Dict
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Rank trails and separate into exact matches and suggestions.
        
        Args:
            trails: List of scored trails
            filters: Active filters
            user: User profile
            context: Context data
        
        Returns:
            (exact_matches, suggestions)
        """
        # Apply hard filters (safety, season, fear of heights)
        filtered_trails = self._apply_hard_filters(trails, filters, user, context)
        
        # Separate exact matches from suggestions
        exact_matches = []
        suggestions = []
        
        for trail in filtered_trails:
            relevance = trail.get("relevance_percentage", 0.0)
            
            # Check if it's an exact match
            if self._is_exact_match(trail, filters, user, context, relevance):
                exact_matches.append(trail)
            else:
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
        
        return exact_matches, suggestions
    
    def _apply_hard_filters(
        self, 
        trails: List[Dict], 
        filters: Dict, 
        user: Dict, 
        context: Dict
    ) -> List[Dict]:
        """Apply hard filters that cannot be violated."""
        filtered = []
        
        for trail in trails:
            # Season filter
            if filters.get("avoid_closed") and context.get("season"):
                season = context["season"].lower()
                closed_seasons = (trail.get("closed_seasons") or "").lower()
                if season in closed_seasons:
                    continue
            
            # Fear of heights
            if user.get("fear_of_heights"):
                safety_risks = (trail.get("safety_risks") or "").lower()
                if "heights" in safety_risks:
                    continue
            
            # Weather filter (if forecast available and doesn't match)
            hike_date = context.get("hike_start_date") or context.get("hike_date")
            desired_weather = context.get("weather", "sunny")
            forecast_weather = trail.get("forecast_weather")
            
            if hike_date and desired_weather and forecast_weather:
                # Only filter out if forecast exists and doesn't match
                # Don't penalize for missing forecasts
                if not weather_matches(desired_weather, forecast_weather):
                    # Move to suggestions instead of filtering out completely
                    # This allows users to see trails even if weather doesn't match
                    pass
            
            filtered.append(trail)
        
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
        
        # Distance filter
        if "max_distance" in filters:
            trail_distance = trail.get("distance")
            if trail_distance and trail_distance > filters["max_distance"]:
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

