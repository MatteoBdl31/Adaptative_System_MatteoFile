# -*- coding: utf-8 -*-
"""
Main recommendation engine.
Orchestrates filtering, scoring, ranking, and enrichment.
"""

from typing import Dict, List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor
from backend.db import get_all_trails, filter_trails
from .filters import FilterBuilder
from .scorer import TrailScorer
from .ranker import TrailRanker
from .weather import WeatherEnricher
from .explanation import ExplanationEnricher
from .debug import RecommendationDebugger
from .config import (
    DEBUG_ENABLED, ALWAYS_RETURN_RESULTS, MIN_RESULTS_TO_RETURN,
    THRESHOLD_LEVELS, MAX_FILTER_RELAXATION_LEVELS
)


class RecommendationEngine:
    """Main recommendation engine for adaptive trail recommendations."""
    
    def __init__(self, debug_enabled: bool = None):
        """
        Args:
            debug_enabled: Whether to enable debugging (defaults to config)
        """
        self.filter_builder = FilterBuilder()
        self.scorer = TrailScorer()
        self.ranker = TrailRanker()
        self.weather_enricher = WeatherEnricher()
        self.explanation_enricher = ExplanationEnricher()
        self.debugger = RecommendationDebugger(enabled=debug_enabled if debug_enabled is not None else DEBUG_ENABLED)
    
    def recommend(
        self, 
        user: Dict, 
        context: Dict,
        max_trails: int = 10
    ) -> Dict:
        """
        Generate trail recommendations with progressive fallback and debugging.
        
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
                "metadata": Dict (includes debug_info if enabled)
            }
        """
        try:
            self.debugger.clear()
            self.debugger.start_stage("initialization", {"user_id": user.get("id"), "max_trails": max_trails})
            
            # Step 1: Build filters from rules and context
            try:
                self.debugger.start_stage("filter_building")
                filters, active_rules = self.filter_builder.build_filters(user, context, self.debugger)
                self.debugger.end_stage({"filters": filters, "active_rules_count": len(active_rules)})
            except Exception as e:
                self.debugger.add_error("Filter building failed", e)
                # Fallback to minimal filters
                filters = {"is_real": True}
                active_rules = []
            
            # Extract display settings
            display_settings = self._extract_display_settings(filters)
            if "max_trails" in display_settings:
                max_trails = display_settings["max_trails"]
            
            # Progressive fallback system
            candidate_trails, fallback_level = self._get_candidates_with_fallback(filters, context)
            
            if not candidate_trails:
                self.debugger.add_warning("No candidate trails found after all fallback levels")
                # Last resort: get all trails
                try:
                    candidate_trails = get_all_trails()
                    self.debugger.log_fallback_triggered(7, "No candidates after all fallbacks", filters, {"is_real": True})
                except Exception as e:
                    self.debugger.add_error("Failed to get all trails", e)
                    candidate_trails = []
            
            # Step 3: Score all trails (without weather - faster)
            try:
                self.debugger.start_stage("scoring")
                scored_trails = self.scorer.score_trails(candidate_trails, user, context)
                self.debugger.log_scoring_stats(scored_trails)
                self.debugger.end_stage({"scored_count": len(scored_trails)})
            except Exception as e:
                self.debugger.add_error("Scoring failed", e)
                # Use trails without scores
                scored_trails = candidate_trails
                for trail in scored_trails:
                    trail["relevance_percentage"] = 50.0
                    trail["score"] = 0.5
            
            # Step 4: Fetch weather ONLY for top-scored trails (performance optimization)
            # Weather is only used to filter out storm_risk, so we fetch for top 50 scored trails
            # This reduces API calls from potentially 200+ to 50, significantly improving performance
            try:
                self.debugger.start_stage("weather_enrichment")
                hike_date = context.get("hike_start_date") or context.get("hike_date")
                
                if hike_date and scored_trails:
                    # Sort by score to get top trails
                    scored_trails_sorted = sorted(
                        scored_trails,
                        key=lambda x: (x.get("relevance_percentage", 0), x.get("popularity", 0)),
                        reverse=True
                    )
                    # Fetch weather for top 50 scored trails (enough for ranking to filter storm_risk)
                    top_scored_trails = scored_trails_sorted[:50]
                    
                    enriched_trails_list = self.weather_enricher.enrich_trails(top_scored_trails, hike_date, max_trails=50)
                    enriched_map = {t["trail_id"]: t for t in enriched_trails_list}
                    
                    # Update weather in all scored trails (only top 50 will have it)
                    for trail in scored_trails:
                        trail_id = trail.get("trail_id")
                        if trail_id in enriched_map:
                            trail["forecast_weather"] = enriched_map[trail_id].get("forecast_weather")
                    
                    self.debugger.end_stage({"weather_fetched": len(enriched_trails_list)})
                else:
                    self.debugger.end_stage({"weather_fetched": 0, "reason": "no_hike_date" if not hike_date else "no_trails"})
            except Exception as e:
                self.debugger.add_error("Weather enrichment failed", e)
                # Continue without weather data
            
            # Step 5: Rank trails with progressive threshold adjustment (now with weather for top trails)
            exact_matches, suggestions = self._rank_with_fallback(
                scored_trails, filters, user, context, fallback_level, self.debugger
            )
            
            # Step 6: Ensure we always have some results (but respect min_duration for multi-day trips)
            time_available = context.get("time_available", 0)
            is_multi_day_trip = time_available >= 1440
            min_duration_required = filters.get("min_duration") if is_multi_day_trip else None
            
            if ALWAYS_RETURN_RESULTS and not exact_matches and not suggestions:
                self.debugger.add_warning("No results after ranking, using fallback to top scored trails")
                scored_trails.sort(
                    key=lambda x: (x.get("relevance_percentage", 0), x.get("popularity", 0)),
                    reverse=True
                )
                # For multi-day trips, only include trails that meet min_duration requirement
                if min_duration_required:
                    filtered_trails = [t for t in scored_trails if t.get("duration", 0) >= min_duration_required]
                    suggestions = filtered_trails[:max_trails] if filtered_trails else []
                else:
                    suggestions = scored_trails[:max_trails]
            
            # Step 7: Final safety check - ensure multi-day trips only show multi-day trails
            if is_multi_day_trip:
                days = time_available // 1440
                # Minimum duration thresholds based on trip length
                min_duration_thresholds = {
                    1: 900,   # 15 hours minimum
                    2: 1800,  # 1.25 days minimum
                    3: 2520,  # 1.75 days minimum
                }
                min_duration_threshold = min_duration_thresholds.get(days, 3240)  # 2.25 days for 4+ days
                
                # Filter out trails that don't meet minimum duration
                exact_matches = [t for t in exact_matches if t.get("duration", 0) >= min_duration_threshold]
                suggestions = [t for t in suggestions if t.get("duration", 0) >= min_duration_threshold]
                
                if len(exact_matches) == 0 and len(suggestions) == 0:
                    self.debugger.add_warning(f"All trails filtered out by min_duration ({min_duration_threshold} min) for {days}-day trip")
            
            # Step 8: Limit results
            exact_matches = exact_matches[:max_trails]
            suggestions = suggestions[:max_trails]
            
            # Ensure minimum results - but respect min_duration for multi-day trips
            if ALWAYS_RETURN_RESULTS and len(exact_matches) + len(suggestions) < MIN_RESULTS_TO_RETURN:
                all_trails = exact_matches + suggestions
                if len(all_trails) < MIN_RESULTS_TO_RETURN:
                    # Add more from scored trails
                    scored_trails.sort(
                        key=lambda x: (x.get("relevance_percentage", 0), x.get("popularity", 0)),
                        reverse=True
                    )
                    for trail in scored_trails:
                        # For multi-day trips, only add trails that meet min_duration
                        if min_duration_required and trail.get("duration", 0) < min_duration_required:
                            continue
                        if trail not in all_trails and len(suggestions) < max_trails * 2:
                            suggestions.append(trail)
                            if len(exact_matches) + len(suggestions) >= MIN_RESULTS_TO_RETURN:
                                break
            
            # Step 9: Add metadata and recommendation reasons
            for trail in exact_matches:
                trail["view_type"] = "recommended"
                trail["recommendation_reasons"] = [
                    rule.get("description", rule.get("condition"))
                    for rule in active_rules
                ]
            
            for trail in suggestions:
                trail["view_type"] = "suggested"
            
            # Build metadata with debug info
            hike_date = context.get("hike_start_date") or context.get("hike_date")
            metadata = {
                "total_candidates": len(candidate_trails),
                "scored_count": len(scored_trails),
                "exact_matches_count": len(exact_matches),
                "suggestions_count": len(suggestions),
                "active_rules_count": len(active_rules),
                "weather_fetched": min(50, len(scored_trails)) if hike_date and scored_trails else 0,
                "fallback_level": fallback_level
            }
            
            # Add debug information if enabled
            if self.debugger.enabled:
                metadata["debug_info"] = self.debugger.get_debug_info()
            
            # Step 9: Explanations are generated on-demand only (not here)
            # This avoids unnecessary API calls and credit usage
            # Explanations are fetched via API endpoints when user requests them
            
            self.debugger.end_stage({"final_results": len(exact_matches) + len(suggestions)})
            
            return {
                "exact_matches": exact_matches,
                "suggestions": suggestions,
                "active_rules": active_rules,
                "display_settings": display_settings,
                "metadata": metadata
            }
            
        except Exception as e:
            self.debugger.add_error("Critical error in recommend()", e)
            # Return empty results with error info
            return {
                "exact_matches": [],
                "suggestions": [],
                "active_rules": [],
                "display_settings": {"display_mode": "full", "max_trails": max_trails, "hide_images": False},
                "metadata": {
                    "error": str(e),
                    "debug_info": self.debugger.get_debug_info() if self.debugger.enabled else {}
                }
            }
    
    def _get_candidates_with_fallback(self, filters: Dict, context: Dict) -> Tuple[List[Dict], int]:
        """Get candidate trails with progressive fallback."""
        fallback_level = 1
        original_filters = filters.copy()
        
        # Store original min_duration for multi-day trips before relaxing
        time_available = context.get("time_available", 0)
        is_multi_day_trip = time_available >= 1440
        original_min_duration = filters.get("min_duration") if is_multi_day_trip else None
        
        for level in range(1, MAX_FILTER_RELAXATION_LEVELS + 1):
            self.debugger.start_stage(f"candidate_filtering_level_{level}")
            self.debugger.log_filter_application(filters, 0, 0)  # We don't know before count
            
            try:
                candidate_trails = self._get_candidate_trails(filters)
                candidates_before = len(candidate_trails) if level == 1 else 0
                self.debugger.log_filter_application(filters, candidates_before, len(candidate_trails))
                self.debugger.end_stage({"candidates": len(candidate_trails), "level": level})
                
                if candidate_trails:
                    if level > 1:
                        self.debugger.log_fallback_triggered(level, f"No candidates at level {level-1}", original_filters, filters)
                    return candidate_trails, level
                
            except Exception as e:
                self.debugger.add_error(f"Filtering failed at level {level}", e)
            
            # Prepare next fallback level
            if level == 1:
                # Level 2: Relax duration filters
                filters = self._relax_duration_filters(filters, context)
            elif level == 2:
                # Level 3: Remove min_duration, relax other filters
                filters = self._relax_all_filters(filters, context)
            elif level == 3:
                # Level 4: Remove most restrictive filters
                filters = self._minimal_filters(filters)
            elif level >= 4:
                # Level 5+: Keep relaxing but preserve min_duration for multi-day trips
                filters = self._ultra_minimal_filters(original_min_duration)
            
            fallback_level = level + 1
        
        # If we get here, all fallbacks failed
        return [], fallback_level
    
    def _relax_duration_filters(self, filters: Dict, context: Dict) -> Dict:
        """Relax duration filters (Level 2)."""
        relaxed = filters.copy()
        time_available = context.get("time_available", 0)
        
        # For multi-day trips, don't remove min_duration - just relax it slightly
        if time_available >= 1440 and "min_duration" in relaxed:
            # For multi-day, keep requiring multi-day trails but relax the minimum slightly
            days = time_available // 1440
            if days == 1:
                relaxed["min_duration"] = 900  # Relax to 15 hours (0.625 days)
            elif days == 2:
                relaxed["min_duration"] = 1800  # Relax to 1.25 days
            elif days == 3:
                relaxed["min_duration"] = 2520  # Relax to 1.75 days
            else:
                relaxed["min_duration"] = 3240  # Relax to 2.25 days for 4+ days
        elif time_available < 1440:
            # For single-day trips, can remove min_duration
            relaxed.pop("min_duration", None)
        
        if "max_duration" in relaxed:
            relaxed["max_duration"] = relaxed["max_duration"] * 2
        
        return relaxed
    
    def _relax_all_filters(self, filters: Dict, context: Dict) -> Dict:
        """Relax all filters (Level 3)."""
        relaxed = filters.copy()
        time_available = context.get("time_available", 0)
        
        # For multi-day trips, keep a minimum duration requirement
        # Don't allow single-day trails when user selected multi-day
        if time_available >= 1440:
            # Keep min_duration but set it to a very low multi-day threshold (12 hours)
            relaxed["min_duration"] = 720  # 12 hours minimum for multi-day trips
        else:
            # For single-day trips, can remove min_duration
            relaxed.pop("min_duration", None)
        
        relaxed.pop("min_difficulty", None)
        relaxed.pop("min_distance", None)
        
        if "max_duration" in relaxed:
            relaxed["max_duration"] = relaxed["max_duration"] * 3
        if "max_difficulty" in relaxed:
            relaxed["max_difficulty"] = min(10.0, relaxed["max_difficulty"] * 1.5)
        if "max_distance" in relaxed:
            relaxed["max_distance"] = relaxed["max_distance"] * 2
        if "max_elevation" in relaxed:
            relaxed["max_elevation"] = relaxed["max_elevation"] * 2
        
        return relaxed
    
    def _minimal_filters(self, filters: Dict) -> Dict:
        """Minimal filters (Level 4)."""
        minimal = {
            "is_real": filters.get("is_real", True),
            "max_duration": filters.get("max_duration", 10000) if "max_duration" in filters else None
        }
        # Preserve min_duration for multi-day trips if it exists
        if "min_duration" in filters:
            minimal["min_duration"] = filters["min_duration"]
        return minimal
    
    def _ultra_minimal_filters(self, min_duration: Optional[int] = None) -> Dict:
        """Ultra minimal filters (Level 5+)."""
        filters = {"is_real": True}
        # Preserve min_duration for multi-day trips even in ultra minimal mode
        if min_duration:
            filters["min_duration"] = min_duration
        return filters
    
    def _rank_with_fallback(self, scored_trails: List[Dict], filters: Dict, user: Dict, context: Dict, fallback_level: int, debugger) -> Tuple[List[Dict], List[Dict]]:
        """Rank trails with progressive threshold adjustment."""
        self.debugger.start_stage("ranking")
        
        # Try different thresholds based on fallback level
        threshold_index = min(fallback_level - 1, len(THRESHOLD_LEVELS) - 1)
        threshold = THRESHOLD_LEVELS[threshold_index]
        
        # Create ranker with adjusted threshold
        ranker = TrailRanker(exact_match_threshold=threshold)
        
        try:
            exact_matches, suggestions = ranker.rank_trails(scored_trails, filters, user, context, debugger)
            self.debugger.log_ranking_results(len(exact_matches), len(suggestions), threshold)
            self.debugger.end_stage({"exact": len(exact_matches), "suggestions": len(suggestions), "threshold": threshold})
            
            # If no results and we can lower threshold more, try again
            if not exact_matches and not suggestions and threshold_index < len(THRESHOLD_LEVELS) - 1:
                for next_threshold in THRESHOLD_LEVELS[threshold_index + 1:]:
                    ranker = TrailRanker(exact_match_threshold=next_threshold)
                    exact_matches, suggestions = ranker.rank_trails(scored_trails, filters, user, context, debugger)
                    if exact_matches or suggestions:
                        self.debugger.add_warning(f"Lowered threshold to {next_threshold}% to get results")
                        break
            
            return exact_matches, suggestions
            
        except Exception as e:
            self.debugger.add_error("Ranking failed", e)
            # Fallback: just sort by score
            scored_trails.sort(
                key=lambda x: (x.get("relevance_percentage", 0), x.get("popularity", 0)),
                reverse=True
            )
            return [], scored_trails[:10]
    
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

