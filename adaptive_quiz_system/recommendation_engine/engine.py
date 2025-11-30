# -*- coding: utf-8 -*-
"""
Main recommendation engine.
Orchestrates filtering, scoring, ranking, and enrichment.
"""

from typing import Dict, List, Tuple
from backend.db import get_all_trails, filter_trails
from .filters import FilterBuilder
from .scorer import TrailScorer
from .ranker import TrailRanker
from .weather import WeatherEnricher


class RecommendationEngine:
    """Main recommendation engine for adaptive trail recommendations."""
    
    def __init__(self):
        self.filter_builder = FilterBuilder()
        self.scorer = TrailScorer()
        self.ranker = TrailRanker()
        self.weather_enricher = WeatherEnricher()
    
    def recommend(
        self, 
        user: Dict, 
        context: Dict,
        max_trails: int = 10
    ) -> Dict:
        """
        Generate trail recommendations.
        
        Args:
            user: User profile dictionary
            context: Context dictionary (time, weather, device, etc.)
            max_trails: Maximum number of trails to return per category
        
        Returns:
            {
                "exact_matches": List[Dict],
                "suggestions": List[Dict],
                "active_rules": List[Dict],
                "display_settings": Dict,
                "metadata": Dict
            }
        """
        # Step 1: Build filters from rules and context
        filters, active_rules = self.filter_builder.build_filters(user, context)
        
        # Extract display settings
        display_settings = self._extract_display_settings(filters)
        if "max_trails" in display_settings:
            max_trails = display_settings["max_trails"]
        
        # Step 2: Get candidate trails
        candidate_trails = self._get_candidate_trails(filters)
        
        # Step 3: Score all trails
        scored_trails = self.scorer.score_trails(candidate_trails, user, context)
        
        # Step 4: Rank first (without weather) to identify top trails
        # This way we only fetch weather for trails that will actually be shown
        exact_matches_prelim, suggestions_prelim = self.ranker.rank_trails(
            scored_trails, 
            filters, 
            user, 
            context
        )
        
        # Step 5: Fetch weather only for final results (much faster!)
        hike_date = context.get("hike_start_date") or context.get("hike_date")
        
        # Only fetch weather for trails that will be displayed (exact matches + top suggestions)
        trails_to_enrich = (exact_matches_prelim[:max_trails] + 
                           suggestions_prelim[:max_trails])
        
        # Fetch weather in parallel (only for trails we'll actually show)
        enriched_trails_list = self.weather_enricher.enrich_trails(
            trails_to_enrich, 
            hike_date
        )
        
        # Create a mapping of trail_id to enriched trail
        enriched_map = {t["trail_id"]: t for t in enriched_trails_list}
        
        # Update scored_trails with weather data where available
        for trail in scored_trails:
            trail_id = trail.get("trail_id")
            if trail_id in enriched_map:
                trail["forecast_weather"] = enriched_map[trail_id].get("forecast_weather")
        
        # Re-score with weather data (only affects weather criterion)
        scored_trails = self.scorer.score_trails(scored_trails, user, context)
        
        # Step 6: Final ranking with weather data included
        exact_matches, suggestions = self.ranker.rank_trails(
            scored_trails, 
            filters, 
            user, 
            context
        )
        
        # Step 7: Limit results
        exact_matches = exact_matches[:max_trails]
        suggestions = suggestions[:max_trails]
        
        # Step 8: Add metadata and recommendation reasons
        for trail in exact_matches:
            trail["view_type"] = "recommended"
            trail["recommendation_reasons"] = [
                rule.get("description", rule.get("condition"))
                for rule in active_rules
            ]
        
        for trail in suggestions:
            trail["view_type"] = "suggested"
        
        # Build metadata
        metadata = {
            "total_candidates": len(candidate_trails),
            "scored_count": len(scored_trails),
            "exact_matches_count": len(exact_matches),
            "suggestions_count": len(suggestions),
            "active_rules_count": len(active_rules),
            "weather_fetched": len(trails_to_enrich) if hike_date else 0
        }
        
        return {
            "exact_matches": exact_matches,
            "suggestions": suggestions,
            "active_rules": active_rules,
            "display_settings": display_settings,
            "metadata": metadata
        }
    
    def _get_candidate_trails(self, filters: Dict) -> List[Dict]:
        """Get candidate trails based on filters."""
        # Remove non-filter keys
        filter_copy = {k: v for k, v in filters.items() 
                      if k not in ["display_mode", "max_trails", "hide_images"]}
        
        if filter_copy:
            # Use database filtering for efficiency
            trails = filter_trails(filter_copy)
        else:
            # No filters, get all trails
            trails = get_all_trails()
        
        return trails
    
    def _extract_display_settings(self, filters: Dict) -> Dict:
        """Extract display settings from filters."""
        settings = {
            "display_mode": filters.pop("display_mode", "full"),
            "max_trails": filters.pop("max_trails", 10),
            "hide_images": filters.pop("hide_images", False)
        }
        return settings

