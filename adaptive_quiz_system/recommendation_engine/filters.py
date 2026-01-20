# -*- coding: utf-8 -*-
"""
Filter builder for trail recommendations.
Converts rules and context into database filters.
"""

from typing import Dict, List, Optional, Tuple
from backend.db import get_rules
import logging

logger = logging.getLogger(__name__)


class FilterBuilder:
    """Builds trail filters from rules and context."""
    
    def __init__(self):
        self.rules = get_rules()
    
    def build_filters(self, user: Dict, context: Dict, debugger=None) -> Tuple[Dict, List[Dict]]:
        """
        Build filters from rules and context.
        
        Args:
            user: User profile dictionary
            context: Context dictionary
            debugger: Optional RecommendationDebugger instance for logging
        
        Returns:
            (filters_dict, active_rules_list)
        """
        filters = {
            "is_real": True
            # Note: region filter removed to allow trails from all French regions
            # This enables more diverse trail types for better user profile detection
        }
        active_rules = []
        
        try:
            logger.debug(f"Building filters for user {user.get('id')}, context: {context.get('time_available')} min")
            
            # Evaluate rules
            for rule in self.rules:
                try:
                    if self._evaluate_condition(rule["condition"], user, context):
                        self._apply_adaptation(filters, rule["adaptation"])
                        active_rules.append(rule)
                        logger.debug(f"Rule activated: {rule.get('description', rule.get('condition'))}")
                except Exception as e:
                    logger.warning(f"Error evaluating rule {rule.get('id', 'unknown')}: {e}")
                    if debugger:
                        debugger.add_warning(f"Rule evaluation failed: {rule.get('description', 'unknown')}")
            
            # Apply time-based filters if not set by rules
            self._apply_time_filters(filters, context)
            
            # Apply safety filters
            self._apply_safety_filters(filters, user, context)
            
            logger.debug(f"Final filters: {filters}, Active rules: {len(active_rules)}")
            
        except Exception as e:
            logger.error(f"Error building filters: {e}")
            if debugger:
                debugger.add_error("Filter building failed", e)
        
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
        
        # Handle multi-day trips: remove distance restrictions and set appropriate duration filters
        is_multi_day_trip = time_available >= 1440
        if is_multi_day_trip:
            # Remove distance restrictions for multi-day trips
            # Multi-day trails are naturally longer and distance limits don't apply the same way
            if filters.get("max_distance"):
                filters.pop("max_distance", None)
            if filters.get("prefer_short"):
                filters.pop("prefer_short", None)
            
            # Override max_duration if rule set it too low, or set it if not present
            if filters.get("max_duration") and filters["max_duration"] < 1440:
                days = (time_available // 1440) + 1
                filters["max_duration"] = days * 1440
            elif "max_duration" not in filters:
                days = (time_available // 1440) + 1
                filters["max_duration"] = days * 1440
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
        
        # Set min_duration filter for multi-day trips to ensure appropriate trail lengths
        if "min_duration" not in filters and is_multi_day_trip:
            days = time_available // 1440
            # Require trails that match the selected duration (not just 1-day hikes)
            min_duration_map = {
                1: 1080,   # 0.75 days (18 hours) minimum
                2: 2160,   # 1.5 days minimum
                3: 2880,   # 2 days minimum
            }
            filters["min_duration"] = min_duration_map.get(days, 3600)  # 2.5 days for 4+ days
    
    def _apply_safety_filters(self, filters: Dict, user: Dict, context: Dict):
        """Apply safety-related filters."""
        # Fear of heights is handled in post-filtering
        # Weather-based safety is handled in scoring
        
        # Season-based closure is handled in post-filtering
        pass

