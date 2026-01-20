# -*- coding: utf-8 -*-
"""
Debug instrumentation for recommendation system.
Tracks the entire pipeline execution for diagnostics.
"""

from typing import Dict, List, Optional, Any
from collections import defaultdict
import json


class RecommendationDebugger:
    """Tracks recommendation pipeline execution for debugging and diagnostics."""
    
    def __init__(self, enabled: bool = True):
        """
        Args:
            enabled: Whether debugging is enabled
        """
        self.enabled = enabled
        self.stages = []
        self.current_stage = None
        self.filtered_out_trails = []
        self.warnings = []
        self.errors = []
        self.stats = defaultdict(dict)
    
    def start_stage(self, stage_name: str, context: Dict = None):
        """Start tracking a new stage."""
        if not self.enabled:
            return
        
        self.current_stage = {
            "name": stage_name,
            "context": context or {},
            "started": True,
            "completed": False
        }
        self.stages.append(self.current_stage)
    
    def end_stage(self, result: Any = None):
        """End the current stage."""
        if not self.enabled or not self.current_stage:
            return
        
        self.current_stage["completed"] = True
        if result is not None:
            self.current_stage["result"] = result
    
    def log_filter_application(self, filters: Dict, candidates_before: int, candidates_after: int):
        """Log filter application results."""
        if not self.enabled:
            return
        
        if self.current_stage:
            self.current_stage["filters_applied"] = filters.copy()
            self.current_stage["candidates_before"] = candidates_before
            self.current_stage["candidates_after"] = candidates_after
            self.current_stage["filtered_count"] = candidates_before - candidates_after
    
    def log_trail_filtered_out(self, trail_id: str, reason: str, filter_name: str = None):
        """Log when a trail is filtered out."""
        if not self.enabled:
            return
        
        self.filtered_out_trails.append({
            "trail_id": trail_id,
            "reason": reason,
            "filter": filter_name,
            "stage": self.current_stage["name"] if self.current_stage else "unknown"
        })
    
    def log_scoring_stats(self, scored_trails: List[Dict]):
        """Log scoring statistics."""
        if not self.enabled or not scored_trails:
            return
        
        scores = [t.get("relevance_percentage", 0) for t in scored_trails]
        if scores:
            self.stats["scoring"] = {
                "min_score": min(scores),
                "max_score": max(scores),
                "avg_score": sum(scores) / len(scores),
                "median_score": sorted(scores)[len(scores) // 2],
                "total_scored": len(scored_trails),
                "scores_above_80": len([s for s in scores if s >= 80]),
                "scores_above_60": len([s for s in scores if s >= 60]),
                "scores_above_40": len([s for s in scores if s >= 40])
            }
    
    def log_ranking_results(self, exact_matches: int, suggestions: int, threshold: float):
        """Log ranking results."""
        if not self.enabled:
            return
        
        self.stats["ranking"] = {
            "exact_matches": exact_matches,
            "suggestions": suggestions,
            "threshold_used": threshold
        }
    
    def add_warning(self, message: str):
        """Add a warning message."""
        if self.enabled:
            self.warnings.append({
                "message": message,
                "stage": self.current_stage["name"] if self.current_stage else "unknown"
            })
    
    def add_error(self, message: str, exception: Exception = None):
        """Add an error message."""
        if self.enabled:
            error_info = {
                "message": message,
                "stage": self.current_stage["name"] if self.current_stage else "unknown"
            }
            if exception:
                error_info["exception_type"] = type(exception).__name__
                error_info["exception_message"] = str(exception)
            self.errors.append(error_info)
    
    def log_fallback_triggered(self, level: int, reason: str, filters_before: Dict, filters_after: Dict):
        """Log when fallback mechanism is triggered."""
        if not self.enabled:
            return
        
        if "fallbacks" not in self.stats:
            self.stats["fallbacks"] = []
        
        self.stats["fallbacks"].append({
            "level": level,
            "reason": reason,
            "filters_before": filters_before.copy(),
            "filters_after": filters_after.copy()
        })
    
    def get_debug_info(self) -> Dict:
        """Get complete debug information."""
        if not self.enabled:
            return {}
        
        return {
            "enabled": True,
            "stages": self.stages,
            "filtered_out_trails": self.filtered_out_trails[:100],  # Limit to first 100
            "filtered_out_count": len(self.filtered_out_trails),
            "stats": dict(self.stats),
            "warnings": self.warnings,
            "errors": self.errors,
            "summary": self._generate_summary()
        }
    
    def _generate_summary(self) -> Dict:
        """Generate a summary of the debug information."""
        summary = {
            "total_stages": len(self.stages),
            "completed_stages": len([s for s in self.stages if s.get("completed")]),
            "total_filtered_out": len(self.filtered_out_trails),
            "total_warnings": len(self.warnings),
            "total_errors": len(self.errors)
        }
        
        if "fallbacks" in self.stats:
            summary["fallback_levels_used"] = [f["level"] for f in self.stats["fallbacks"]]
            summary["max_fallback_level"] = max([f["level"] for f in self.stats["fallbacks"]]) if self.stats["fallbacks"] else 0
        
        return summary
    
    def to_json(self) -> str:
        """Export debug info as JSON string."""
        return json.dumps(self.get_debug_info(), indent=2, default=str)
    
    def clear(self):
        """Clear all debug information."""
        self.stages = []
        self.current_stage = None
        self.filtered_out_trails = []
        self.warnings = []
        self.errors = []
        self.stats = defaultdict(dict)
