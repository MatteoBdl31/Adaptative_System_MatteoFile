# -*- coding: utf-8 -*-
"""
Trail analytics service for analyzing performance data and predicting metrics.
"""

import sqlite3
import json
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from backend.db import USERS_DB, TRAILS_DB, get_trail, get_user, _ensure_new_tables
from backend.weather_service import get_weather_forecast

_ensure_new_tables()


class TrailAnalytics:
    """Analyzes trail performance and predicts metrics."""
    
    def __init__(self):
        self.users_db = USERS_DB
        self.trails_db = TRAILS_DB
    
    def analyze_trail_performance(self, completed_trail_id: int) -> Dict:
        """
        Analyze time-series performance data for a completed trail.
        
        Args:
            completed_trail_id: ID from completed_trails table
        
        Returns:
            {
                "summary": Dict,
                "heart_rate_analysis": Dict,
                "speed_analysis": Dict,
                "elevation_profile": List[Dict],
                "zones": Dict
            }
        """
        conn = sqlite3.connect(self.users_db)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # Get performance data
        cur.execute("""
            SELECT * FROM trail_performance_data
            WHERE completed_trail_id = ?
            ORDER BY timestamp ASC
        """, (completed_trail_id,))
        data_points = [dict(row) for row in cur.fetchall()]
        
        # Get completed trail info
        cur.execute("""
            SELECT * FROM completed_trails WHERE id = ?
        """, (completed_trail_id,))
        completed_trail = dict(cur.fetchone()) if cur.fetchone() else None
        
        conn.close()
        
        if not data_points:
            return {"error": "No performance data available"}
        
        # Summary statistics
        heart_rates = [d["heart_rate"] for d in data_points if d.get("heart_rate")]
        speeds = [d["speed"] for d in data_points if d.get("speed")]
        elevations = [d["elevation"] for d in data_points if d.get("elevation")]
        calories = [d["calories"] for d in data_points if d.get("calories")]
        
        summary = {
            "total_points": len(data_points),
            "duration_minutes": max((d["timestamp"] for d in data_points), default=0) // 60,
            "avg_heart_rate": round(statistics.mean(heart_rates), 1) if heart_rates else None,
            "max_heart_rate": max(heart_rates) if heart_rates else None,
            "avg_speed": round(statistics.mean(speeds), 2) if speeds else None,
            "max_speed": round(max(speeds), 2) if speeds else None,
            "total_calories": sum(calories) if calories else None,
            "elevation_gain": max(elevations) - min(elevations) if elevations and len(elevations) > 1 else None
        }
        
        # Heart rate analysis
        heart_rate_analysis = {
            "avg": round(statistics.mean(heart_rates), 1) if heart_rates else None,
            "min": min(heart_rates) if heart_rates else None,
            "max": max(heart_rates) if heart_rates else None,
            "zones": self._calculate_hr_zones(heart_rates) if heart_rates else {}
        }
        
        # Speed analysis
        speed_analysis = {
            "avg": round(statistics.mean(speeds), 2) if speeds else None,
            "min": round(min(speeds), 2) if speeds else None,
            "max": round(max(speeds), 2) if speeds else None,
            "variation": round(statistics.stdev(speeds), 2) if speeds and len(speeds) > 1 else None
        }
        
        # Elevation profile
        elevation_profile = [
            {
                "timestamp": d["timestamp"],
                "elevation": d["elevation"],
                "distance": self._estimate_distance(data_points[:i+1]) if i > 0 else 0
            }
            for i, d in enumerate(data_points)
            if d.get("elevation") is not None
        ]
        
        # Zones (time spent in different intensity zones)
        zones = self._calculate_zones(data_points)
        
        return {
            "summary": summary,
            "heart_rate_analysis": heart_rate_analysis,
            "speed_analysis": speed_analysis,
            "elevation_profile": elevation_profile,
            "zones": zones
        }
    
    def predict_metrics(
        self,
        trail: Dict,
        user: Dict,
        weather: Optional[str] = None,
        target_date: Optional[str] = None
    ) -> Dict:
        """
        Predict performance metrics for a trail based on user profile and conditions.
        
        Args:
            trail: Trail dictionary
            user: User dictionary
            weather: Weather condition (optional)
            target_date: Target date for prediction (optional)
        
        Returns:
            {
                "predicted_duration": int,
                "predicted_heart_rate": Dict,
                "predicted_speed": float,
                "predicted_calories": int,
                "difficulty_adjustment": Dict
            }
        """
        # Base predictions from user's historical data
        user_trails = self._get_user_completed_trails(user["id"])
        
        # Base duration prediction
        base_duration = trail.get("duration", 120)
        
        # Adjust based on user's average completion time vs estimated
        if user_trails:
            avg_ratio = statistics.mean([
                ct.get("actual_duration", 0) / max(ct.get("duration", 1), 1)
                for ct in user_trails
                if ct.get("duration") and ct.get("actual_duration")
            ])
            predicted_duration = int(base_duration * avg_ratio) if avg_ratio else base_duration
        else:
            # Use fitness level as proxy
            fitness_multiplier = {
                "High": 0.9,
                "Medium": 1.0,
                "Low": 1.2
            }.get(user.get("fitness_level", "Medium"), 1.0)
            predicted_duration = int(base_duration * fitness_multiplier)
        
        # Predicted heart rate (based on difficulty and fitness)
        difficulty = trail.get("difficulty", 5.0)
        fitness_level = user.get("fitness_level", "Medium")
        
        base_hr = {
            "High": 140,
            "Medium": 150,
            "Low": 160
        }.get(fitness_level, 150)
        
        # Adjust for difficulty
        hr_adjustment = (difficulty - 5.0) * 5  # ±5 bpm per difficulty point
        predicted_avg_hr = int(base_hr + hr_adjustment)
        predicted_max_hr = int(predicted_avg_hr * 1.2)
        
        # Predicted speed (based on distance and duration)
        distance = trail.get("distance", 5.0)
        predicted_speed = round((distance / predicted_duration) * 60, 2) if predicted_duration > 0 else 0
        
        # Predicted calories (rough estimate: ~50-100 cal/km based on difficulty)
        calories_per_km = 50 + (difficulty * 5)
        predicted_calories = int(distance * calories_per_km)
        
        # Weather adjustments
        difficulty_adjustment = {"factor": 1.0, "reason": "Normal conditions"}
        if weather:
            weather_adjustments = {
                "rainy": {"factor": 1.15, "reason": "Wet conditions slow progress"},
                "storm_risk": {"factor": 1.25, "reason": "Storm conditions require caution"},
                "snowy": {"factor": 1.3, "reason": "Snow slows movement significantly"},
                "sunny": {"factor": 0.95, "reason": "Good conditions"},
                "cloudy": {"factor": 1.0, "reason": "Normal conditions"}
            }
            adjustment = weather_adjustments.get(weather, {"factor": 1.0, "reason": "Normal conditions"})
            predicted_duration = int(predicted_duration * adjustment["factor"])
            difficulty_adjustment = adjustment
        
        return {
            "predicted_duration": predicted_duration,
            "predicted_heart_rate": {
                "avg": predicted_avg_hr,
                "max": predicted_max_hr,
                "zones": {
                    "resting": predicted_avg_hr - 30,
                    "active": predicted_avg_hr,
                    "peak": predicted_max_hr
                }
            },
            "predicted_speed": predicted_speed,
            "predicted_calories": predicted_calories,
            "difficulty_adjustment": difficulty_adjustment
        }
    
    def compare_performance(self, trail_id: str, user_id: int) -> Dict:
        """
        Compare user's performance on a trail vs average/other users.
        
        Args:
            trail_id: Trail ID
            user_id: User ID
        
        Returns:
            {
                "user_performance": Dict,
                "average_performance": Dict,
                "percentile_rank": Dict,
                "personal_records": Dict
            }
        """
        # Get user's completed trails for this trail
        conn = sqlite3.connect(self.users_db)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        cur.execute("""
            SELECT * FROM completed_trails
            WHERE user_id = ? AND trail_id = ?
            ORDER BY completion_date DESC
        """, (user_id, trail_id))
        user_completions = [dict(row) for row in cur.fetchall()]
        
        # Get all completions of this trail
        cur.execute("""
            SELECT * FROM completed_trails
            WHERE trail_id = ?
        """, (trail_id,))
        all_completions = [dict(row) for row in cur.fetchall()]
        
        conn.close()
        
        if not user_completions:
            return {"error": "User has not completed this trail"}
        
        # User's latest performance
        latest = user_completions[0]
        user_performance = {
            "duration": latest.get("actual_duration", 0),
            "rating": latest.get("rating", 0),
            "completion_count": len(user_completions)
        }
        
        # Average performance
        if all_completions:
            avg_duration = statistics.mean([c.get("actual_duration", 0) for c in all_completions])
            avg_rating = statistics.mean([c.get("rating", 0) for c in all_completions])
            average_performance = {
                "duration": round(avg_duration, 1),
                "rating": round(avg_rating, 1),
                "total_completions": len(all_completions)
            }
        else:
            average_performance = {"duration": 0, "rating": 0, "total_completions": 0}
        
        # Percentile rank
        user_duration = latest.get("actual_duration", 0)
        if all_completions and len(all_completions) > 1:
            durations = sorted([c.get("actual_duration", 0) for c in all_completions])
            percentile = (sum(1 for d in durations if d <= user_duration) / len(durations)) * 100
        else:
            percentile = 50
        
        percentile_rank = {
            "duration_percentile": round(percentile, 1),
            "interpretation": self._interpret_percentile(percentile)
        }
        
        # Personal records
        personal_records = {
            "best_duration": min((c.get("actual_duration", 999999) for c in user_completions), default=0),
            "best_rating": max((c.get("rating", 0) for c in user_completions), default=0),
            "total_completions": len(user_completions)
        }
        
        return {
            "user_performance": user_performance,
            "average_performance": average_performance,
            "percentile_rank": percentile_rank,
            "personal_records": personal_records
        }
    
    # Helper methods
    
    def _get_user_completed_trails(self, user_id: int) -> List[Dict]:
        """Get user's completed trails with details."""
        conn = sqlite3.connect(self.users_db)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM completed_trails
            WHERE user_id = ?
        """, (user_id,))
        completed_trails = [dict(row) for row in cur.fetchall()]
        conn.close()
        
        # Enrich with trail details from trails database
        enriched_trails = []
        for ct in completed_trails:
            trail = get_trail(ct.get("trail_id"))
            if trail:
                ct.update({
                    "duration": trail.get("duration"),
                    "difficulty": trail.get("difficulty"),
                    "distance": trail.get("distance"),
                    "elevation_gain": trail.get("elevation_gain")
                })
            enriched_trails.append(ct)
        
        return enriched_trails
    
    def _calculate_hr_zones(self, heart_rates: List[int]) -> Dict:
        """Calculate heart rate zones."""
        if not heart_rates:
            return {}
        
        avg_hr = statistics.mean(heart_rates)
        max_hr = max(heart_rates)
        
        return {
            "resting": sum(1 for hr in heart_rates if hr < 100),
            "active": sum(1 for hr in heart_rates if 100 <= hr < 150),
            "peak": sum(1 for hr in heart_rates if hr >= 150),
            "avg": round(avg_hr, 1),
            "max": max_hr
        }
    
    def _calculate_zones(self, data_points: List[Dict]) -> Dict:
        """Calculate time spent in different intensity zones."""
        if not data_points:
            return {}
        
        total_time = max((d["timestamp"] for d in data_points), default=0)
        
        # Simple zone calculation based on speed
        speeds = [d.get("speed", 0) for d in data_points if d.get("speed")]
        if not speeds:
            return {}
        
        avg_speed = statistics.mean(speeds)
        max_speed = max(speeds)
        
        # Define zones (can be improved)
        slow_zone = sum(1 for s in speeds if s < avg_speed * 0.8)
        moderate_zone = sum(1 for s in speeds if avg_speed * 0.8 <= s < avg_speed * 1.2)
        fast_zone = sum(1 for s in speeds if s >= avg_speed * 1.2)
        
        return {
            "slow": round((slow_zone / len(speeds)) * 100, 1) if speeds else 0,
            "moderate": round((moderate_zone / len(speeds)) * 100, 1) if speeds else 0,
            "fast": round((fast_zone / len(speeds)) * 100, 1) if speeds else 0
        }
    
    def _estimate_distance(self, data_points: List[Dict]) -> float:
        """Estimate distance from GPS points."""
        if len(data_points) < 2:
            return 0.0
        
        total_distance = 0.0
        for i in range(1, len(data_points)):
            prev = data_points[i-1]
            curr = data_points[i]
            
            if prev.get("latitude") and prev.get("longitude") and curr.get("latitude") and curr.get("longitude"):
                # Simple distance calculation (Haversine would be better)
                lat_diff = abs(curr["latitude"] - prev["latitude"])
                lon_diff = abs(curr["longitude"] - prev["longitude"])
                # Rough approximation (1 degree ≈ 111 km)
                distance = ((lat_diff ** 2 + lon_diff ** 2) ** 0.5) * 111
                total_distance += distance
        
        return round(total_distance, 2)
    
    def _interpret_percentile(self, percentile: float) -> str:
        """Interpret percentile rank."""
        if percentile >= 90:
            return "Excellent - Top 10%"
        elif percentile >= 75:
            return "Great - Top 25%"
        elif percentile >= 50:
            return "Good - Above average"
        elif percentile >= 25:
            return "Average"
        else:
            return "Below average - Room for improvement"
