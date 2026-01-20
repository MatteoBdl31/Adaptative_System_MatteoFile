# -*- coding: utf-8 -*-
"""
Criteria evaluators for trail recommendations.
Each criterion evaluates a specific aspect of trail-user-context matching.
"""

from typing import Dict, List, Optional, Tuple
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class CriterionResult:
    """Result of evaluating a criterion."""
    matches: bool
    score: float  # 0.0 to 1.0
    message: str  # Human-readable explanation
    weight: float = 1.0  # Importance weight for this criterion


class Criterion(ABC):
    """Base class for trail recommendation criteria."""
    
    def __init__(self, weight: float = 1.0):
        self.weight = weight
    
    @abstractmethod
    def evaluate(self, trail: Dict, user: Dict, context: Dict) -> CriterionResult:
        """Evaluate if trail matches this criterion."""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get the name of this criterion."""
        pass


class DifficultyCriterion(Criterion):
    """Evaluates if trail difficulty matches user experience and fitness."""
    
    def evaluate(self, trail: Dict, user: Dict, context: Dict) -> CriterionResult:
        trail_difficulty = trail.get("difficulty", 0)
        experience = (user.get("experience") or "").lower()
        fitness = (user.get("fitness_level") or "").lower()
        
        # Determine appropriate difficulty range
        if experience == "beginner" or fitness == "low":
            max_difficulty = 3.0
            if trail_difficulty <= max_difficulty:
                return CriterionResult(
                    matches=True,
                    score=1.0,
                    message=f"Difficulty appropriate ({trail_difficulty:.1f} ≤ {max_difficulty})"
                )
            else:
                return CriterionResult(
                    matches=False,
                    score=0.0,
                    message=f"Too difficult ({trail_difficulty:.1f} > {max_difficulty})"
                )
        elif experience == "intermediate" or fitness == "medium":
            min_difficulty, max_difficulty = 3.0, 6.0
            if min_difficulty <= trail_difficulty <= max_difficulty:
                return CriterionResult(
                    matches=True,
                    score=1.0,
                    message=f"Difficulty appropriate ({trail_difficulty:.1f} in range {min_difficulty}-{max_difficulty})"
                )
            elif trail_difficulty < min_difficulty:
                return CriterionResult(
                    matches=False,
                    score=0.5,
                    message=f"Too easy ({trail_difficulty:.1f} < {min_difficulty})"
                )
            else:
                return CriterionResult(
                    matches=False,
                    score=0.0,
                    message=f"Too difficult ({trail_difficulty:.1f} > {max_difficulty})"
                )
        else:  # advanced/expert or high fitness
            min_difficulty = 6.0
            if trail_difficulty >= min_difficulty:
                return CriterionResult(
                    matches=True,
                    score=1.0,
                    message=f"Difficulty appropriate ({trail_difficulty:.1f} ≥ {min_difficulty})"
                )
            else:
                return CriterionResult(
                    matches=False,
                    score=0.3,
                    message=f"Not challenging enough ({trail_difficulty:.1f} < {min_difficulty})"
                )
    
    def get_name(self) -> str:
        return "difficulty"


class DurationCriterion(Criterion):
    """Evaluates if trail duration fits available time."""
    
    def evaluate(self, trail: Dict, user: Dict, context: Dict) -> CriterionResult:
        trail_duration = trail.get("duration")
        time_available = context.get("time_available")
        
        if not trail_duration or not time_available:
            return CriterionResult(
                matches=True,
                score=0.5,
                message="Duration data unavailable"
            )
        
        # Calculate max allowed duration with smart buffer
        if time_available < 1440:  # Less than 1 day
            max_allowed = time_available  # No buffer for single day
            # For short durations (< 4 hours), be more flexible with targets
            if time_available < 240:  # Less than 4 hours
                # More lenient targets for short hikes
                target_min = time_available * 0.5
                target_max = time_available * 1.0
            else:
                # Target duration: 70-90% of available time for longer single day hikes
                target_min = time_available * 0.7
                target_max = time_available * 0.9
        else:  # Multi-day
            # Calculate actual number of days (can be fractional, e.g., 2.5 days)
            selected_days = time_available / 1440
            # Allow buffer: trails can be up to 1 day longer than selected (for rest time)
            max_allowed = (selected_days + 1) * 1440
            # Target duration: trails around the selected duration
            # For 2 days, target trails from 1.5 to 2.5 days (allows some flexibility)
            target_min = (selected_days - 0.5) * 1440
            target_max = (selected_days + 0.5) * 1440
            # Ensure target_min is at least 0.75 days (1080 min) for multi-day trips
            if target_min < 1080:
                target_min = 1080
        
        # Check if trail exceeds maximum
        if trail_duration > max_allowed:
            return CriterionResult(
                matches=False,
                score=0.0,
                message=f"Too long ({trail_duration} min > {max_allowed} min)"
            )
        
        # Check if trail is too long for beginner/low fitness users regardless of available time
        experience = (user.get("experience") or "").lower()
        fitness = (user.get("fitness_level") or "").lower()
        if (experience == "beginner" or fitness == "low") and trail_duration > 360:  # 6 hours
            # Beginners shouldn't do trails longer than 6 hours even if they have time
            return CriterionResult(
                matches=False,
                score=0.0,
                message=f"Too long for beginner ({trail_duration} min > 360 min / 6 hours recommended max)"
            )
        
        # Penalize trails that are too short (less than 30% of available time)
        min_threshold = time_available * 0.3
        if trail_duration < min_threshold:
            # Still matches but with low score
            ratio = trail_duration / min_threshold
            return CriterionResult(
                matches=True,
                score=0.2 * ratio,  # Very low score for too-short trails
                message=f"Too short ({trail_duration} min < {min_threshold:.0f} min threshold)"
            )
        
        # Calculate score based on how close to target duration
        if target_min <= trail_duration <= target_max:
            # Perfect match - within target range
            return CriterionResult(
                matches=True,
                score=1.0,
                message=f"Duration matches perfectly ({trail_duration} min within target range)"
            )
        elif trail_duration < target_min:
            # Below target but above minimum threshold
            # Score increases as we approach target_min
            ratio = trail_duration / target_min
            score = 0.5 + (ratio * 0.4)  # Score between 0.5-0.9
            return CriterionResult(
                matches=True,
                score=score,
                message=f"Duration acceptable but shorter than ideal ({trail_duration} min < {target_min:.0f} min target)"
            )
        else:  # trail_duration > target_max but <= max_allowed
            # Above target but within max
            # Score decreases as we move away from target_max
            excess = trail_duration - target_max
            max_excess = max_allowed - target_max
            if max_excess > 0:
                ratio = 1.0 - (excess / max_excess)
                score = 0.7 + (ratio * 0.3)  # Score between 0.7-1.0
            else:
                score = 0.7
            return CriterionResult(
                matches=True,
                score=score,
                message=f"Duration acceptable but longer than ideal ({trail_duration} min > {target_max:.0f} min target)"
            )
    
    def get_name(self) -> str:
        return "duration"


class DistanceCriterion(Criterion):
    """Evaluates if trail distance is appropriate."""
    
    def evaluate(self, trail: Dict, user: Dict, context: Dict) -> CriterionResult:
        trail_distance = trail.get("distance")
        trail_duration = trail.get("duration", 0)
        time_available = context.get("time_available", 0)
        
        if not trail_distance:
            return CriterionResult(
                matches=True,
                score=0.5,
                message="Distance data unavailable"
            )
        
        # For multi-day hikes, relax distance restrictions significantly
        # Multi-day trails are naturally longer and distance limits don't apply the same way
        is_multi_day_trail = trail_duration >= 1440  # 1 day or more
        is_multi_day_trip = time_available >= 1440
        
        if is_multi_day_trail or is_multi_day_trip:
            # For multi-day hikes, distance is less important - focus on duration instead
            # Still check if it's reasonable, but be much more lenient
            experience = (user.get("experience") or "").lower()
            fitness = (user.get("fitness_level") or "").lower()
            
            if experience == "beginner" or fitness == "low":
                # Even for beginners, multi-day trails can be longer since they're spread over days
                max_distance = 50.0  # Much more lenient for multi-day
            elif experience == "intermediate" or fitness == "medium":
                max_distance = 100.0  # Very lenient for multi-day
            else:  # advanced/expert or high fitness
                max_distance = 200.0  # No practical limit for advanced multi-day hikers
            
            if trail_distance <= max_distance:
                return CriterionResult(
                    matches=True,
                    score=1.0,
                    message=f"Distance appropriate for multi-day hike ({trail_distance:.1f} km)"
                )
            else:
                # Still allow but with lower score
                return CriterionResult(
                    matches=True,
                    score=0.7,
                    message=f"Long distance for multi-day hike ({trail_distance:.1f} km), but acceptable"
                )
        
        # For single-day hikes, use original strict distance limits
        experience = (user.get("experience") or "").lower()
        fitness = (user.get("fitness_level") or "").lower()
        persistence = user.get("performance", {}).get("persistence_score", 0.5)
        
        # Determine max distance based on experience and fitness FIRST (most important)
        # Then adjust based on persistence
        if experience == "beginner" or fitness == "low":
            # Beginners should not do long trails regardless of persistence
            max_distance = 10.0  # Strict limit for beginners
            if trail_distance <= max_distance:
                return CriterionResult(
                    matches=True,
                    score=1.0,
                    message=f"Distance appropriate for beginner ({trail_distance:.1f} km ≤ {max_distance} km)"
                )
            else:
                # Penalize heavily - this is too long for a beginner
                return CriterionResult(
                    matches=False,
                    score=0.0,
                    message=f"Too long for beginner ({trail_distance:.1f} km > {max_distance} km recommended max)"
                )
        elif experience == "intermediate" or fitness == "medium":
            # Intermediate hikers can handle moderate distances
            max_distance = 20.0
            if trail_distance <= max_distance:
                return CriterionResult(
                    matches=True,
                    score=1.0,
                    message=f"Distance appropriate ({trail_distance:.1f} km ≤ {max_distance} km)"
                )
            else:
                return CriterionResult(
                    matches=False,
                    score=0.0,
                    message=f"Too long ({trail_distance:.1f} km > {max_distance} km)"
                )
        else:  # advanced/expert or high fitness
            # Advanced hikers can handle longer distances, but still consider persistence
            if persistence < 0.4:
                max_distance = 20.0
            elif persistence < 0.7:
                max_distance = 30.0
            else:
                max_distance = 40.0
            
            if trail_distance <= max_distance:
                return CriterionResult(
                    matches=True,
                    score=1.0,
                    message=f"Distance appropriate ({trail_distance:.1f} km ≤ {max_distance} km)"
                )
            else:
                return CriterionResult(
                    matches=False,
                    score=0.0,
                    message=f"Too long ({trail_distance:.1f} km > {max_distance} km)"
                )
    
    def get_name(self) -> str:
        return "distance"


class ElevationCriterion(Criterion):
    """Evaluates if trail elevation gain matches fitness level."""
    
    def evaluate(self, trail: Dict, user: Dict, context: Dict) -> CriterionResult:
        elevation_gain = trail.get("elevation_gain", 0)
        fitness = (user.get("fitness_level") or "").lower()
        
        if fitness == "low":
            max_elevation = 400
            if elevation_gain <= max_elevation:
                return CriterionResult(
                    matches=True,
                    score=1.0,
                    message=f"Elevation appropriate ({elevation_gain} m ≤ {max_elevation} m)"
                )
            else:
                return CriterionResult(
                    matches=False,
                    score=0.0,
                    message=f"Too challenging ({elevation_gain} m > {max_elevation} m)"
                )
        elif fitness == "high":
            min_elevation = 400
            if elevation_gain >= min_elevation:
                return CriterionResult(
                    matches=True,
                    score=1.0,
                    message=f"Elevation appropriate ({elevation_gain} m ≥ {min_elevation} m)"
                )
            else:
                return CriterionResult(
                    matches=False,
                    score=0.3,
                    message=f"Not challenging enough ({elevation_gain} m < {min_elevation} m)"
                )
        else:  # medium or unknown
            return CriterionResult(
                matches=True,
                score=0.8,
                message=f"Elevation acceptable ({elevation_gain} m)"
            )
    
    def get_name(self) -> str:
        return "elevation"


class SafetyCriterion(Criterion):
    """Evaluates trail safety based on user preferences and weather."""
    
    def evaluate(self, trail: Dict, user: Dict, context: Dict) -> CriterionResult:
        safety_risks = (trail.get("safety_risks") or "").lower()
        fear_of_heights = user.get("fear_of_heights", False)
        weather = context.get("weather", "sunny").lower()
        forecast_weather = trail.get("forecast_weather")
        effective_weather = forecast_weather or weather
        
        # Check fear of heights
        if fear_of_heights and "heights" in safety_risks:
            return CriterionResult(
                matches=False,
                score=0.0,
                message="Contains heights exposure"
            )
        
        # Check weather-related safety
        if effective_weather in {"rainy", "snowy", "storm_risk"}:
            if safety_risks not in ("", "none", "low"):
                return CriterionResult(
                    matches=False,
                    score=0.0,
                    message=f"Not safe for {effective_weather} weather"
                )
        
        # General safety check
        if safety_risks in ("", "none", "low"):
            return CriterionResult(
                matches=True,
                score=1.0,
                message="Safe trail"
            )
        else:
            return CriterionResult(
                matches=False,
                score=0.2,
                message=f"Safety concerns: {safety_risks}"
            )
    
    def get_name(self) -> str:
        return "safety"


class SeasonCriterion(Criterion):
    """Evaluates if trail is open during the season."""
    
    def evaluate(self, trail: Dict, user: Dict, context: Dict) -> CriterionResult:
        season = context.get("season", "").lower()
        closed_seasons = (trail.get("closed_seasons") or "").lower()
        
        if not season:
            return CriterionResult(
                matches=True,
                score=0.8,
                message="Season not specified"
            )
        
        if season in closed_seasons:
            return CriterionResult(
                matches=False,
                score=0.0,
                message=f"Closed in {season}"
            )
        else:
            return CriterionResult(
                matches=True,
                score=1.0,
                message=f"Open in {season}"
            )
    
    def get_name(self) -> str:
        return "season"


class LandscapeCriterion(Criterion):
    """Evaluates if trail landscapes match user preferences."""
    
    def evaluate(self, trail: Dict, user: Dict, context: Dict) -> CriterionResult:
        user_preferences = user.get("preferences", [])
        if not user_preferences:
            return CriterionResult(
                matches=True,
                score=0.5,
                message="No landscape preferences"
            )
        
        trail_landscapes = [
            l.strip().lower() 
            for l in (trail.get("landscapes") or "").split(",") 
            if l.strip()
        ]
        
        # Check if any preference matches
        matches = [pref.lower() for pref in user_preferences if pref.lower() in trail_landscapes]
        
        if matches:
            match_ratio = len(matches) / len(user_preferences)
            return CriterionResult(
                matches=True,
                score=min(1.0, match_ratio * 1.2),  # Bonus for multiple matches
                message=f"Matches preferences: {', '.join(matches)}"
            )
        else:
            return CriterionResult(
                matches=False,
                score=0.0,
                message=f"Doesn't match preferences: {', '.join(user_preferences)}"
            )
    
    def get_name(self) -> str:
        return "landscape"


class WeatherCriterion(Criterion):
    """Evaluates if forecasted weather matches desired weather."""
    
    def evaluate(self, trail: Dict, user: Dict, context: Dict) -> CriterionResult:
        desired_weather = context.get("weather", "sunny").lower()
        forecast_weather = trail.get("forecast_weather")
        hike_date = context.get("hike_start_date") or context.get("hike_date")
        
        if not hike_date:
            return CriterionResult(
                matches=True,
                score=0.5,
                message="No hike date specified"
            )
        
        if forecast_weather is None:
            # Weather not fetched yet or unavailable
            return CriterionResult(
                matches=True,
                score=0.5,
                message="Weather forecast unavailable"
            )
        
        forecast_weather = forecast_weather.lower()
        
        # Exact match
        if desired_weather == forecast_weather:
            return CriterionResult(
                matches=True,
                score=1.0,
                message=f"Weather matches: {forecast_weather}"
            )
        
        # Compatible matches
        if desired_weather == "sunny" and forecast_weather == "cloudy":
            return CriterionResult(
                matches=True,
                score=0.8,
                message="Weather acceptable: cloudy (desired sunny)"
            )
        
        if desired_weather == "rainy" and forecast_weather == "cloudy":
            return CriterionResult(
                matches=True,
                score=0.7,
                message="Weather acceptable: cloudy (desired rainy)"
            )
        
        # Mismatch
        return CriterionResult(
            matches=False,
            score=0.0,
            message=f"Weather mismatch: {forecast_weather} (desired {desired_weather})"
        )
    
    def get_name(self) -> str:
        return "weather"


def get_default_criteria() -> List[Criterion]:
    """Get the default set of criteria with appropriate weights."""
    return [
        DifficultyCriterion(weight=1.5),
        DurationCriterion(weight=2.0),  # Most important
        DistanceCriterion(weight=1.0),
        ElevationCriterion(weight=1.2),
        SafetyCriterion(weight=2.5),  # Critical
        SeasonCriterion(weight=1.5),
        LandscapeCriterion(weight=1.0),
        WeatherCriterion(weight=2.0),  # Increased weight to ensure weather is properly considered
    ]

