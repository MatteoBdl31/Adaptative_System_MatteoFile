# -*- coding: utf-8 -*-
"""
Filter builder for trail recommendations.
Converts rules and context into database filters.
"""

from typing import Dict, List, Optional, Tuple
from backend.db import get_rules


class FilterBuilder:
    """Builds trail filters from rules and context."""
    
    def __init__(self):
        self.rules = get_rules()
    
    def build_filters(self, user: Dict, context: Dict) -> Tuple[Dict, List[Dict]]:
        """
        Build filters from rules and context.
        
        Returns:
            (filters_dict, active_rules_list)
        """
        filters = {
            "region": "french_alps",
            "is_real": True
        }
        active_rules = []
        
        # Evaluate rules
        for rule in self.rules:
            if self._evaluate_condition(rule["condition"], user, context):
                self._apply_adaptation(filters, rule["adaptation"])
                active_rules.append(rule)
        
        # Apply time-based filters if not set by rules
        self._apply_time_filters(filters, context)
        
        # Apply safety filters
        self._apply_safety_filters(filters, user, context)
        
        return filters, active_rules
    
    def _evaluate_condition(self, condition: str, user: Dict, context: Dict) -> bool:
        """Evaluate a rule condition string."""
        clauses = condition.split("AND")
        for clause in clauses:
            clause = clause.strip()
            if not self._evaluate_clause(clause, user, context):
                return False
        return True
    
    def _evaluate_clause(self, clause: str, user: Dict, context: Dict) -> bool:
        """Evaluate a single condition clause."""
        clause = clause.strip()
        
        # Equality check: key=value
        if "=" in clause and "CONTAINS" not in clause:
            key, val = clause.split("=", 1)
            key, val = key.strip(), val.strip()
            
            # Check user attributes
            if key in user:
                if str(user[key]) != val:
                    return False
            # Check context attributes
            elif key in context:
                if str(context[key]) != val:
                    return False
            # Check performance attributes
            elif key.startswith("performance."):
                perf_key = key.split(".")[1]
                perf_value = user.get("performance", {}).get(perf_key, 0)
                if str(perf_value) != val:
                    return False
            else:
                return False
        
        # Less than or equal: key<=value
        elif "<=" in clause:
            key, val = clause.split("<=", 1)
            key, val = key.strip(), val.strip()
            try:
                threshold = float(val)
                # Check context
                if key in context:
                    if float(context[key]) > threshold:
                        return False
                # Check performance
                elif key.startswith("performance."):
                    perf_key = key.split(".")[1]
                    perf_value = user.get("performance", {}).get(perf_key, 0)
                    if float(perf_value) > threshold:
                        return False
                else:
                    return False
            except (ValueError, TypeError):
                return False
        
        # Greater than or equal: key>=value
        elif ">=" in clause:
            key, val = clause.split(">=", 1)
            key, val = key.strip(), val.strip()
            try:
                threshold = float(val)
                # Check context
                if key in context:
                    if float(context[key]) < threshold:
                        return False
                # Check performance
                elif key.startswith("performance."):
                    perf_key = key.split(".")[1]
                    perf_value = user.get("performance", {}).get(perf_key, 0)
                    if float(perf_value) < threshold:
                        return False
                else:
                    return False
            except (ValueError, TypeError):
                return False
        
        # Contains check: key CONTAINS value
        elif "CONTAINS" in clause:
            key, val = clause.split("CONTAINS", 1)
            key, val = key.strip(), val.strip()
            
            if key == "landscape_preference":
                preferences = user.get("preferences", [])
                if val not in preferences:
                    return False
            elif key in user:
                user_value = user[key]
                if isinstance(user_value, list):
                    if val not in user_value:
                        return False
                elif isinstance(user_value, str):
                    if val not in user_value:
                        return False
                else:
                    return False
            else:
                return False
        
        return True
    
    def _apply_adaptation(self, filters: Dict, adaptation: str):
        """Apply adaptation rules to filters."""
        for rule in adaptation.split(";"):
            rule = rule.strip()
            if not rule:
                continue
            
            if "=" in rule:
                key, val = rule.split("=", 1)
                key, val = key.strip(), val.strip()
                
                if key == "max_difficulty":
                    filters["max_difficulty"] = self._parse_difficulty(val)
                elif key == "min_difficulty":
                    filters["min_difficulty"] = self._parse_difficulty(val)
                elif key in ["max_distance", "min_distance", "max_duration", "max_elevation"]:
                    filters[key] = float(val) if "." in val else int(val)
                elif key == "landscape_filter":
                    filters["landscape_filter"] = val
                elif key == "prefer_peaks":
                    filters["prefer_peaks"] = True
                elif key == "prefer_short":
                    filters["prefer_short"] = True
                elif key in ["avoid_risky", "prefer_safe"]:
                    filters["avoid_risky"] = True
                elif key == "avoid_closed":
                    filters["avoid_closed"] = True
                elif key == "display_mode":
                    filters["display_mode"] = val
                elif key == "max_trails":
                    filters["max_trails"] = int(val)
                elif key == "hide_images":
                    filters["hide_images"] = val.lower() == "true"
    
    def _parse_difficulty(self, val: str) -> float:
        """Parse difficulty value (easy/medium/hard or numeric)."""
        val_lower = val.lower()
        if val_lower == "easy":
            return 3.0
        elif val_lower == "medium":
            return 6.0
        elif val_lower == "hard":
            return 10.0
        else:
            return float(val)
    
    def _apply_time_filters(self, filters: Dict, context: Dict):
        """Apply time-based filters with smart buffer logic."""
        time_available = context.get("time_available")
        if not time_available:
            return
        
        # If user has multi-day availability but rule set short duration, override
        if time_available >= 1440 and filters.get("max_duration") and filters["max_duration"] < 1440:
            days = (time_available // 1440) + 1
            filters["max_duration"] = days * 1440
            # Remove restrictive distance filters for multi-day trips
            if filters.get("max_distance") and filters["max_distance"] < 15:
                filters.pop("max_distance", None)
            if filters.get("prefer_short"):
                filters.pop("prefer_short", None)
        elif "max_duration" not in filters:
            # Calculate max_duration from time_available
            if time_available < 1440:  # Less than 1 day
                filters["max_duration"] = max(60, time_available)
            else:  # Multi-day
                days = (time_available // 1440) + 1
                filters["max_duration"] = days * 1440
        
        # Ensure max_duration is reasonable
        if filters.get("max_duration") and filters["max_duration"] < 60:
            filters["max_duration"] = 60
            if filters.get("min_distance"):
                filters.pop("min_distance", None)
            if filters.get("min_difficulty"):
                filters.pop("min_difficulty", None)
    
    def _apply_safety_filters(self, filters: Dict, user: Dict, context: Dict):
        """Apply safety-related filters."""
        # Fear of heights is handled in post-filtering
        # Weather-based safety is handled in scoring
        
        # Season-based closure is handled in post-filtering
        pass

