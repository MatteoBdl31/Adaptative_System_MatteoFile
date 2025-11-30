# -*- coding: utf-8 -*-
"""
Modern adaptive trail recommendation system.
Uses the new recommendation engine architecture.
"""

from recommendation_engine import RecommendationEngine


def _prepare_trail_metadata(trail):
    """Prepare trail metadata for display."""
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


def adapt_trails(user, context):
    """
    Main adaptation function for trail recommendations.
    Uses the new recommendation engine.
    
    Args:
        user: User profile dictionary
        context: Context dictionary
    
    Returns:
        (exact_matches, suggestions, display_settings, active_rules)
    """
    engine = RecommendationEngine()
    results = engine.recommend(user, context)
    
    # Prepare trail metadata and normalize criteria format for templates
    def normalize_criteria(trail):
        """Normalize criteria format for template compatibility."""
        trail = _prepare_trail_metadata(trail)
        
        # Convert matched_criteria from list of dicts to list of strings for template
        if "matched_criteria" in trail:
            matched = trail["matched_criteria"]
            if matched and isinstance(matched[0], dict):
                trail["matched_criteria"] = [m.get("message", m.get("name", "")) for m in matched]
        
        # Convert unmatched_criteria from list of dicts to list of strings
        if "unmatched_criteria" in trail:
            unmatched = trail["unmatched_criteria"]
            if unmatched and isinstance(unmatched[0], dict):
                trail["unmatched_criteria"] = [u.get("message", u.get("name", "")) for u in unmatched]
        
        return trail
    
    exact_matches = [normalize_criteria(trail) for trail in results["exact_matches"]]
    suggestions = [normalize_criteria(trail) for trail in results["suggestions"]]
    
    return (
        exact_matches,
        suggestions,
        results["display_settings"],
        results["active_rules"]
    )
