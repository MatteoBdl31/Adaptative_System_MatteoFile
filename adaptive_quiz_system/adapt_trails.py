# -*- coding: utf-8 -*-
"""
Backward-compatible wrapper for the recommendation engine.
Provides the adapt_trails() function interface.
"""

from typing import Dict, List, Tuple
from recommendation_engine import RecommendationEngine


def adapt_trails(
    user: Dict,
    context: Dict,
    max_trails: int = 10
) -> Tuple[List[Dict], List[Dict], Dict, List[Dict], Dict]:
    """
    Generate trail recommendations (backward-compatible interface).
    
    Args:
        user: User profile dictionary
        context: Context dictionary (time, weather, device, etc.)
        max_trails: Maximum number of trails to return per category
    
    Returns:
        Tuple of:
        - exact_matches: List of trails with ≥95% relevance
        - suggestions: List of other recommended trails
        - display_settings: UI configuration dictionary
        - active_rules: List of rules that were applied
        - metadata: Metadata dictionary with debug info
    """
    engine = RecommendationEngine()
    result = engine.recommend(user, context, max_trails)
    
    return (
        result["exact_matches"],
        result["suggestions"],
        result["display_settings"],
        result["active_rules"],
        result["metadata"]
    )


def calculate_relevance_score(trail: Dict, user: Dict, context: Dict) -> float:
    """
    Calculate relevance score for a single trail (for testing/debugging).
    
    Args:
        trail: Trail dictionary
        user: User profile dictionary
        context: Context dictionary
    
    Returns:
        Relevance score (0.0 to 1.0)
    """
    engine = RecommendationEngine()
    scored_trails = engine.scorer.score_trails([trail], user, context)
    if scored_trails:
        return scored_trails[0].get("score", 0.0)
    return 0.0
