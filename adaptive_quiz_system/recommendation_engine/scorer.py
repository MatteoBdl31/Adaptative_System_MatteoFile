# -*- coding: utf-8 -*-
"""
Scoring system for trail recommendations.
Calculates relevance scores based on multiple criteria.
"""

from typing import Dict, List
from .criteria import Criterion, CriterionResult, get_default_criteria
import logging

logger = logging.getLogger(__name__)


class TrailScorer:
    """Scores trails based on multiple weighted criteria."""
    
    def __init__(self, criteria: List[Criterion] = None):
        self.criteria = criteria or get_default_criteria()
    
    def score_trail(self, trail: Dict, user: Dict, context: Dict) -> Dict:
        """
        Score a trail and return detailed results.
        
        Returns:
            {
                "score": float,  # Weighted score (0-1)
                "relevance_percentage": float,  # 0-100
                "matched_criteria": List[str],
                "unmatched_criteria": List[str],
                "criterion_results": List[CriterionResult]
            }
        """
        criterion_results = []
        matched_criteria = []
        unmatched_criteria = []
        total_weight = 0.0
        weighted_score = 0.0
        
        # Evaluate all criteria
        for criterion in self.criteria:
            result = criterion.evaluate(trail, user, context)
            criterion_results.append(result)
            
            weight = criterion.weight
            total_weight += weight
            
            if result.matches:
                weighted_score += result.score * weight
                matched_criteria.append({
                    "name": criterion.get_name(),
                    "message": result.message
                })
            else:
                unmatched_criteria.append({
                    "name": criterion.get_name(),
                    "message": result.message
                })
        
        # Calculate final scores
        if total_weight == 0:
            final_score = 0.5  # Neutral if no criteria
            relevance = 50.0
        else:
            final_score = weighted_score / total_weight
            relevance = final_score * 100.0
        
        return {
            "score": final_score,
            "relevance_percentage": relevance,
            "matched_criteria": matched_criteria,
            "unmatched_criteria": unmatched_criteria,
            "criterion_results": criterion_results,
            "total_weight": total_weight
        }
    
    def score_trails(self, trails: List[Dict], user: Dict, context: Dict) -> List[Dict]:
        """Score multiple trails."""
        logger.debug(f"Scoring {len(trails)} trails with {len(self.criteria)} criteria")
        scored_trails = []
        errors = 0
        
        for trail in trails:
            try:
                score_data = self.score_trail(trail, user, context)
                trail_copy = trail.copy()
                trail_copy.update(score_data)
                scored_trails.append(trail_copy)
            except Exception as e:
                errors += 1
                logger.warning(f"Error scoring trail {trail.get('trail_id', 'unknown')}: {e}")
                # Add default scores for failed trails
                trail_copy = trail.copy()
                trail_copy.update({
                    "score": 0.5,
                    "relevance_percentage": 50.0,
                    "matched_criteria": [],
                    "unmatched_criteria": [],
                    "criterion_results": [],
                    "total_weight": 0.0
                })
                scored_trails.append(trail_copy)
        
        if errors > 0:
            logger.warning(f"Scoring completed with {errors} errors out of {len(trails)} trails")
        
        logger.debug(f"Scoring completed: {len(scored_trails)} trails scored")
        return scored_trails

