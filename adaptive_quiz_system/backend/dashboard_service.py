# -*- coding: utf-8 -*-
"""
Dashboard service for calculating metrics for different dashboard views.
"""

import sqlite3
import json
import os
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import Counter, defaultdict
from backend.db import USERS_DB, TRAILS_DB, get_trail, _ensure_new_tables

_ensure_new_tables()


class DashboardCalculator:
    """Calculates dashboard metrics for different user profiles."""
    
    def __init__(self):
        self.users_db = USERS_DB
        self.trails_db = TRAILS_DB
    
    def calculate_elevation_metrics(self, user_id: int) -> Dict:
        """
        Calculate elevation-focused metrics for Elevation Enthusiast dashboard.
        
        Returns:
            {
                "top_elevation_trails": List[Dict],
                "elevation_gain_over_time": List[Dict],
                "avg_elevation_speed": float,
                "highest_point": float,
                "elevation_distribution": Dict,
                "peak_achievements": List[Dict]
            }
        """
        completed_trails = self._get_completed_trails_with_details(user_id)
        
        if not completed_trails:
            return self._empty_elevation_metrics()
        
        # Top elevation gain trails
        top_trails = sorted(
            completed_trails,
            key=lambda t: t.get("elevation_gain", 0),
            reverse=True
        )[:10]
        
        # Elevation gain over time
        elevation_over_time = []
        cumulative_gain = 0
        for trail in sorted(completed_trails, key=lambda t: t.get("completion_date", "")):
            gain = trail.get("elevation_gain", 0)
            cumulative_gain += gain
            elevation_over_time.append({
                "date": trail.get("completion_date", ""),
                "elevation_gain": gain,
                "cumulative": cumulative_gain
            })
        
        # Average elevation speed (m/hour)
        elevation_speeds = []
        for trail in completed_trails:
            elevation_gain = trail.get("elevation_gain", 0)
            duration = trail.get("actual_duration", trail.get("duration", 60))
            if duration > 0:
                speed = (elevation_gain / duration) * 60  # m/hour
                elevation_speeds.append(speed)
        
        avg_elevation_speed = statistics.mean(elevation_speeds) if elevation_speeds else 0
        
        # Highest point reached
        highest_point = max(
            (t.get("elevation_gain", 0) for t in completed_trails),
            default=0
        )
        
        # Elevation distribution
        elevation_ranges = {
            "0-300m": 0,
            "300-600m": 0,
            "600-900m": 0,
            "900-1200m": 0,
            "1200m+": 0
        }
        for trail in completed_trails:
            gain = trail.get("elevation_gain", 0)
            if gain < 300:
                elevation_ranges["0-300m"] += 1
            elif gain < 600:
                elevation_ranges["300-600m"] += 1
            elif gain < 900:
                elevation_ranges["600-900m"] += 1
            elif gain < 1200:
                elevation_ranges["900-1200m"] += 1
            else:
                elevation_ranges["1200m+"] += 1
        
        # Peak achievements
        peak_achievements = []
        for trail in sorted(completed_trails, key=lambda t: t.get("elevation_gain", 0), reverse=True)[:5]:
            peak_achievements.append({
                "trail_id": trail.get("trail_id"),
                "name": trail.get("name", "Unknown"),
                "elevation_gain": trail.get("elevation_gain", 0),
                "date": trail.get("completion_date", "")
            })
        
        return {
            "top_elevation_trails": [
                {
                    "trail_id": t.get("trail_id"),
                    "name": t.get("name", "Unknown"),
                    "elevation_gain": t.get("elevation_gain", 0),
                    "difficulty": t.get("difficulty", 0),
                    "date": t.get("completion_date", "")
                }
                for t in top_trails
            ],
            "elevation_gain_over_time": elevation_over_time,
            "avg_elevation_speed": round(avg_elevation_speed, 2),
            "highest_point": highest_point,
            "elevation_distribution": elevation_ranges,
            "peak_achievements": peak_achievements
        }
    
    def calculate_fitness_metrics(self, user_id: int) -> Dict:
        """
        Calculate fitness-focused metrics for Performance Athlete dashboard.
        
        Returns:
            {
                "heart_rate_zones": Dict,
                "heart_rate_trends": List[Dict],
                "distance_over_time": List[Dict],
                "calories_burned": int,
                "speed_trends": List[Dict],
                "training_consistency": Dict
            }
        """
        completed_trails = self._get_completed_trails_with_details(user_id)
        performance_data = self._get_performance_data(user_id)
        
        if not completed_trails:
            return self._empty_fitness_metrics()
        
        # Heart rate zones
        heart_rates = []
        for trail in completed_trails:
            if trail.get("avg_heart_rate"):
                heart_rates.append(trail["avg_heart_rate"])
        
        # Get all heart rate data points
        for data in performance_data:
            if data.get("heart_rate"):
                heart_rates.append(data["heart_rate"])
        
        heart_rate_zones = self._calculate_heart_rate_zones(heart_rates)
        
        # Heart rate trends
        heart_rate_trends = []
        for trail in sorted(completed_trails, key=lambda t: t.get("completion_date", "")):
            if trail.get("avg_heart_rate"):
                heart_rate_trends.append({
                    "date": trail.get("completion_date", ""),
                    "avg": trail.get("avg_heart_rate", 0),
                    "max": trail.get("max_heart_rate", 0)
                })
        
        # Distance over time
        distance_over_time = []
        cumulative_distance = 0
        for trail in sorted(completed_trails, key=lambda t: t.get("completion_date", "")):
            distance = trail.get("distance", 0)
            cumulative_distance += distance
            distance_over_time.append({
                "date": trail.get("completion_date", ""),
                "distance": distance,
                "cumulative": round(cumulative_distance, 2)
            })
        
        # Calories burned
        total_calories = sum(t.get("total_calories", 0) or 0 for t in completed_trails)
        
        # Speed trends
        speed_trends = []
        for trail in sorted(completed_trails, key=lambda t: t.get("completion_date", "")):
            if trail.get("avg_speed"):
                speed_trends.append({
                    "date": trail.get("completion_date", ""),
                    "avg": trail.get("avg_speed", 0),
                    "max": trail.get("max_speed", 0)
                })
        
        # Training consistency
        training_consistency = self._calculate_training_consistency(completed_trails)
        
        return {
            "heart_rate_zones": heart_rate_zones,
            "heart_rate_trends": heart_rate_trends,
            "distance_over_time": distance_over_time,
            "calories_burned": total_calories,
            "speed_trends": speed_trends,
            "training_consistency": training_consistency
        }
    
    def calculate_persistence_metrics(self, user_id: int) -> Dict:
        """
        Calculate persistence-focused metrics for Casual/Family dashboard.
        
        Returns:
            {
                "completion_rate": float,
                "started_vs_completed": Dict,
                "completion_time_comparison": List[Dict],
                "longest_streak": int,
                "abandoned_trails": List[Dict],
                "difficulty_progression": List[Dict]
            }
        """
        saved_trails = self._get_saved_trails(user_id)
        started_trails = self._get_started_trails(user_id)
        completed_trails = self._get_completed_trails_with_details(user_id)
        
        # Completion rate
        total_started = len(started_trails) + len(completed_trails)
        completion_rate = (len(completed_trails) / total_started * 100) if total_started > 0 else 0
        
        # Started vs completed
        started_vs_completed = {
            "started": len(started_trails),
            "completed": len(completed_trails),
            "saved": len(saved_trails)
        }
        
        # Completion time comparison
        completion_time_comparison = []
        for trail in completed_trails:
            estimated = trail.get("duration", 0)
            actual = trail.get("actual_duration", 0)
            if estimated > 0:
                completion_time_comparison.append({
                    "trail_id": trail.get("trail_id"),
                    "name": trail.get("name", "Unknown"),
                    "estimated": estimated,
                    "actual": actual,
                    "difference": actual - estimated,
                    "percentage": round((actual / estimated) * 100, 1) if estimated > 0 else 0
                })
        
        # Longest streak
        longest_streak = self._calculate_longest_streak(completed_trails)
        
        # Abandoned trails (started but not completed)
        abandoned = []
        started_trail_ids = {t.get("trail_id") for t in started_trails}
        completed_trail_ids = {t.get("trail_id") for t in completed_trails}
        abandoned_ids = started_trail_ids - completed_trail_ids
        
        for trail_id in abandoned_ids:
            trail_info = next((t for t in started_trails if t.get("trail_id") == trail_id), None)
            if trail_info:
                trail = get_trail(trail_id)
                if trail:
                    abandoned.append({
                        "trail_id": trail_id,
                        "name": trail.get("name", "Unknown"),
                        "start_date": trail_info.get("start_date", ""),
                        "progress": trail_info.get("progress_percentage", 0)
                    })
        
        # Difficulty progression
        difficulty_progression = []
        for trail in sorted(completed_trails, key=lambda t: t.get("completion_date", "")):
            difficulty_progression.append({
                "date": trail.get("completion_date", ""),
                "difficulty": trail.get("difficulty", 0),
                "trail_id": trail.get("trail_id")
            })
        
        return {
            "completion_rate": round(completion_rate, 1),
            "started_vs_completed": started_vs_completed,
            "completion_time_comparison": completion_time_comparison,
            "longest_streak": longest_streak,
            "abandoned_trails": abandoned,
            "difficulty_progression": difficulty_progression
        }
    
    def calculate_exploration_metrics(self, user_id: int) -> Dict:
        """
        Calculate exploration-focused metrics for Explorer dashboard.
        
        Returns:
            {
                "unique_regions": List[str],
                "trail_diversity_score": float,
                "landscapes_discovered": Dict,
                "rare_trail_types": Dict,
                "exploration_map": List[Dict],
                "uncharted_suggestions": List[Dict]
            }
        """
        completed_trails = self._get_completed_trails_with_details(user_id)
        
        if not completed_trails:
            return self._empty_exploration_metrics()
        
        # Unique regions
        regions = set(t.get("region", "unknown") for t in completed_trails)
        
        # Trail diversity score (based on variety of regions, landscapes, types)
        landscapes = set()
        trail_types = set()
        for trail in completed_trails:
            landscapes.update(trail.get("landscapes", "").split(",") if trail.get("landscapes") else [])
            trail_types.add(trail.get("trail_type", "unknown"))
        
        diversity_score = (len(regions) * 0.4 + len(landscapes) * 0.4 + len(trail_types) * 0.2) / max(len(completed_trails), 1) * 100
        
        # Landscapes discovered
        landscapes_discovered = Counter()
        for trail in completed_trails:
            if trail.get("landscapes"):
                for landscape in trail["landscapes"].split(","):
                    landscapes_discovered[landscape.strip()] += 1
        
        # Rare trail types
        trail_type_counts = Counter(t.get("trail_type", "unknown") for t in completed_trails)
        rare_trail_types = {k: v for k, v in trail_type_counts.items() if v <= 2}
        
        # Exploration map (trail locations)
        exploration_map = []
        for trail in completed_trails:
            if trail.get("latitude") and trail.get("longitude"):
                exploration_map.append({
                    "trail_id": trail.get("trail_id"),
                    "name": trail.get("name", "Unknown"),
                    "lat": trail.get("latitude"),
                    "lon": trail.get("longitude"),
                    "region": trail.get("region", "unknown")
                })
        
        return {
            "unique_regions": sorted(list(regions)),
            "trail_diversity_score": round(diversity_score, 1),
            "landscapes_discovered": dict(landscapes_discovered),
            "rare_trail_types": rare_trail_types,
            "exploration_map": exploration_map
        }
    
    def calculate_photography_metrics(self, user_id: int) -> Dict:
        """
        Calculate photography-focused metrics for Photographer dashboard.
        
        Returns:
            {
                "scenic_trails": List[Dict],
                "best_photo_opportunities": List[Dict],
                "landscape_variety": Dict,
                "peak_viewing_times": List[Dict],
                "instagram_locations": List[Dict]
            }
        """
        completed_trails = self._get_completed_trails_with_details(user_id)
        
        if not completed_trails:
            return self._empty_photography_metrics()
        
        # Scenic trails (high popularity, scenic landscapes)
        scenic_trails = []
        for trail in completed_trails:
            popularity = trail.get("popularity", 0)
            landscapes = trail.get("landscapes", "")
            scenic_landscapes = ["lake", "peaks", "mountain", "glacier"]
            has_scenic = any(landscape in landscapes for landscape in scenic_landscapes)
            
            if popularity >= 7.0 and has_scenic:
                scenic_trails.append({
                    "trail_id": trail.get("trail_id"),
                    "name": trail.get("name", "Unknown"),
                    "popularity": popularity,
                    "landscapes": landscapes,
                    "date": trail.get("completion_date", "")
                })
        
        scenic_trails.sort(key=lambda x: x["popularity"], reverse=True)
        
        # Best photo opportunities (one-way trails with scenic views)
        best_photo_opportunities = []
        for trail in completed_trails:
            if trail.get("trail_type") == "one_way":
                landscapes = trail.get("landscapes", "")
                if "peaks" in landscapes or "lake" in landscapes:
                    best_photo_opportunities.append({
                        "trail_id": trail.get("trail_id"),
                        "name": trail.get("name", "Unknown"),
                        "landscapes": landscapes,
                        "duration": trail.get("duration", 0)
                    })
        
        # Landscape variety
        landscape_variety = Counter()
        for trail in completed_trails:
            if trail.get("landscapes"):
                for landscape in trail["landscapes"].split(","):
                    landscape_variety[landscape.strip()] += 1
        
        # Peak viewing times (trails completed, sorted by time)
        peak_viewing_times = []
        for trail in sorted(completed_trails, key=lambda t: t.get("completion_date", "")):
            if "peaks" in trail.get("landscapes", ""):
                peak_viewing_times.append({
                    "trail_id": trail.get("trail_id"),
                    "name": trail.get("name", "Unknown"),
                    "date": trail.get("completion_date", ""),
                    "duration": trail.get("duration", 0)
                })
        
        # Instagram-worthy locations (high popularity + scenic)
        instagram_locations = [
            {
                "trail_id": t.get("trail_id"),
                "name": t.get("name", "Unknown"),
                "popularity": t.get("popularity", 0),
                "landscapes": t.get("landscapes", "")
            }
            for t in sorted(completed_trails, key=lambda x: x.get("popularity", 0), reverse=True)[:10]
            if t.get("popularity", 0) >= 7.5
        ]
        
        return {
            "scenic_trails": scenic_trails[:10],
            "best_photo_opportunities": best_photo_opportunities[:10],
            "landscape_variety": dict(landscape_variety),
            "peak_viewing_times": peak_viewing_times[:10],
            "instagram_locations": instagram_locations
        }
    
    def calculate_contemplative_metrics(self, user_id: int) -> Dict:
        """
        Calculate contemplative-focused metrics for Contemplative dashboard.
        
        Returns:
            {
                "scenic_beauty_score": float,
                "quiet_trails": List[Dict],
                "avg_time_spent": float,
                "meditation_friendly": List[Dict],
                "nature_immersion": Dict
            }
        """
        completed_trails = self._get_completed_trails_with_details(user_id)
        
        if not completed_trails:
            return self._empty_contemplative_metrics()
        
        # Scenic beauty score (based on landscapes and popularity)
        beauty_scores = []
        for trail in completed_trails:
            popularity = trail.get("popularity", 0)
            landscapes = trail.get("landscapes", "")
            scenic_count = sum(1 for l in ["lake", "peaks", "forest", "meadow"] if l in landscapes)
            score = (popularity * 0.5) + (scenic_count * 2)
            beauty_scores.append(score)
        
        scenic_beauty_score = statistics.mean(beauty_scores) if beauty_scores else 0
        
        # Quiet trails (low popularity)
        quiet_trails = [
            {
                "trail_id": t.get("trail_id"),
                "name": t.get("name", "Unknown"),
                "popularity": t.get("popularity", 0),
                "landscapes": t.get("landscapes", "")
            }
            for t in completed_trails
            if t.get("popularity", 10) < 7.0
        ]
        quiet_trails.sort(key=lambda x: x["popularity"])
        
        # Average time spent
        times = [t.get("actual_duration", t.get("duration", 0)) for t in completed_trails]
        avg_time_spent = statistics.mean(times) if times else 0
        
        # Meditation-friendly routes (quiet, scenic, moderate duration)
        meditation_friendly = []
        for trail in completed_trails:
            popularity = trail.get("popularity", 0)
            duration = trail.get("duration", 0)
            landscapes = trail.get("landscapes", "")
            if popularity < 7.0 and 60 <= duration <= 180 and ("forest" in landscapes or "meadow" in landscapes):
                meditation_friendly.append({
                    "trail_id": trail.get("trail_id"),
                    "name": trail.get("name", "Unknown"),
                    "popularity": popularity,
                    "duration": duration,
                    "landscapes": landscapes
                })
        
        # Nature immersion (trails with natural landscapes)
        nature_landscapes = ["forest", "meadow", "lake", "river", "mountain"]
        nature_count = sum(
            1 for trail in completed_trails
            if any(nl in trail.get("landscapes", "") for nl in nature_landscapes)
        )
        
        nature_immersion = {
            "total_nature_trails": nature_count,
            "percentage": round((nature_count / len(completed_trails)) * 100, 1) if completed_trails else 0
        }
        
        return {
            "scenic_beauty_score": round(scenic_beauty_score, 1),
            "quiet_trails": quiet_trails[:10],
            "avg_time_spent": round(avg_time_spent, 1),
            "meditation_friendly": meditation_friendly[:10],
            "nature_immersion": nature_immersion
        }
    
    def calculate_performance_metrics(self, user_id: int) -> Dict:
        """
        Calculate overall performance analytics.
        
        Returns:
            {
                "performance_trends": List[Dict],
                "personal_records": Dict,
                "improvement_metrics": Dict,
                "comparison_to_average": Dict
            }
        """
        completed_trails = self._get_completed_trails_with_details(user_id)
        
        if not completed_trails:
            return self._empty_performance_metrics()
        
        # Performance trends over time
        performance_trends = []
        for trail in sorted(completed_trails, key=lambda t: t.get("completion_date", "")):
            performance_trends.append({
                "date": trail.get("completion_date", ""),
                "distance": trail.get("distance", 0),
                "elevation": trail.get("elevation_gain", 0),
                "difficulty": trail.get("difficulty", 0),
                "duration": trail.get("actual_duration", trail.get("duration", 0))
            })
        
        # Personal records
        personal_records = {
            "longest_distance": max((t.get("distance", 0) for t in completed_trails), default=0),
            "highest_elevation": max((t.get("elevation_gain", 0) for t in completed_trails), default=0),
            "most_difficult": max((t.get("difficulty", 0) for t in completed_trails), default=0),
            "longest_duration": max((t.get("actual_duration", t.get("duration", 0)) for t in completed_trails), default=0)
        }
        
        # Improvement metrics (compare recent vs older)
        if len(completed_trails) >= 4:
            recent = completed_trails[-len(completed_trails)//2:]
            older = completed_trails[:len(completed_trails)//2]
            
            recent_avg_distance = statistics.mean([t.get("distance", 0) for t in recent])
            older_avg_distance = statistics.mean([t.get("distance", 0) for t in older])
            
            recent_avg_difficulty = statistics.mean([t.get("difficulty", 0) for t in recent])
            older_avg_difficulty = statistics.mean([t.get("difficulty", 0) for t in older])
            
            improvement_metrics = {
                "distance_improvement": round(recent_avg_distance - older_avg_distance, 2),
                "difficulty_improvement": round(recent_avg_difficulty - older_avg_difficulty, 2)
            }
        else:
            improvement_metrics = {
                "distance_improvement": 0,
                "difficulty_improvement": 0
            }
        
        # Comparison to average (would need all users' data, simplified here)
        avg_distance = statistics.mean([t.get("distance", 0) for t in completed_trails])
        avg_difficulty = statistics.mean([t.get("difficulty", 0) for t in completed_trails])
        
        comparison_to_average = {
            "avg_distance": round(avg_distance, 2),
            "avg_difficulty": round(avg_difficulty, 2),
            "total_trails": len(completed_trails)
        }
        
        return {
            "performance_trends": performance_trends,
            "personal_records": personal_records,
            "improvement_metrics": improvement_metrics,
            "comparison_to_average": comparison_to_average
        }
    
    # Helper methods
    
    def _get_completed_trails_with_details(self, user_id: int) -> List[Dict]:
        """Get completed trails with full trail details, including predicted metrics."""
        conn = sqlite3.connect(self.users_db)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""
            SELECT ct.id, ct.trail_id, ct.completion_date, ct.actual_duration, ct.rating,
                   ct.avg_heart_rate, ct.max_heart_rate, ct.avg_speed, ct.max_speed,
                   ct.total_calories,
                   ct.predicted_duration, ct.predicted_avg_heart_rate, ct.predicted_max_heart_rate,
                   ct.predicted_avg_speed, ct.predicted_max_speed, ct.predicted_calories,
                   ct.predicted_profile_category,
                   CASE WHEN EXISTS (
                       SELECT 1 FROM trail_performance_data tpd WHERE tpd.completed_trail_id = ct.id
                   ) THEN 1 ELSE 0 END as has_time_series_data
            FROM completed_trails ct
            WHERE ct.user_id = ?
            ORDER BY ct.completion_date DESC
        """, (user_id,))
        completed = [dict(row) for row in cur.fetchall()]
        conn.close()
        
        # Enrich with trail details
        enriched = []
        for ct in completed:
            trail = get_trail(ct["trail_id"])
            if trail:
                enriched.append({**ct, **trail})
        
        return enriched
    
    def _get_performance_data(self, user_id: int) -> List[Dict]:
        """Get time-series performance data for a user."""
        conn = sqlite3.connect(self.users_db)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""
            SELECT tpd.*
            FROM trail_performance_data tpd
            JOIN completed_trails ct ON tpd.completed_trail_id = ct.id
            WHERE ct.user_id = ?
            ORDER BY tpd.timestamp ASC
        """, (user_id,))
        data = [dict(row) for row in cur.fetchall()]
        conn.close()
        return data
    
    def _get_aggregated_heart_rate_metrics(self, user_id: int) -> Dict:
        """Calculate aggregated heart rate metrics across all completions."""
        conn = sqlite3.connect(self.users_db)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # Get all heart rate data from time-series
        cur.execute("""
            SELECT tpd.heart_rate, ct.completion_date
            FROM trail_performance_data tpd
            JOIN completed_trails ct ON tpd.completed_trail_id = ct.id
            WHERE ct.user_id = ? AND tpd.heart_rate IS NOT NULL
            ORDER BY ct.completion_date ASC, tpd.timestamp ASC
        """, (user_id,))
        
        heart_rate_data = [dict(row) for row in cur.fetchall()]
        conn.close()
        
        if not heart_rate_data:
            return {
                "avg_heart_rate": None,
                "max_heart_rate": None,
                "min_heart_rate": None,
                "heart_rate_trend": []
            }
        
        heart_rates = [d["heart_rate"] for d in heart_rate_data]
        
        # Calculate trends by completion date
        trends_by_date = {}
        for d in heart_rate_data:
            date = d["completion_date"][:10]  # Just the date part
            if date not in trends_by_date:
                trends_by_date[date] = []
            trends_by_date[date].append(d["heart_rate"])
        
        heart_rate_trend = [
            {
                "date": date,
                "avg_hr": int(sum(hrs) / len(hrs)),
                "max_hr": max(hrs),
                "min_hr": min(hrs)
            }
            for date, hrs in sorted(trends_by_date.items())
        ]
        
        return {
            "avg_heart_rate": int(sum(heart_rates) / len(heart_rates)),
            "max_heart_rate": max(heart_rates),
            "min_heart_rate": min(heart_rates),
            "heart_rate_trend": heart_rate_trend
        }
    
    def _get_aggregated_gps_metrics(self, user_id: int) -> Dict:
        """Calculate aggregated GPS-based metrics (total distance, elevation profiles)."""
        conn = sqlite3.connect(self.users_db)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # Get GPS data from time-series
        cur.execute("""
            SELECT tpd.latitude, tpd.longitude, tpd.elevation, tpd.speed, ct.completion_date, ct.trail_id
            FROM trail_performance_data tpd
            JOIN completed_trails ct ON tpd.completed_trail_id = ct.id
            WHERE ct.user_id = ? AND tpd.latitude IS NOT NULL AND tpd.longitude IS NOT NULL
            ORDER BY ct.completion_date ASC, tpd.timestamp ASC
        """, (user_id,))
        
        gps_data = [dict(row) for row in cur.fetchall()]
        conn.close()
        
        if not gps_data:
            return {
                "total_distance_km": 0,
                "total_elevation_gain_m": 0,
                "gps_points_count": 0,
                "elevation_profiles": []
            }
        
        # Calculate distance from GPS points (simplified - using Haversine would be more accurate)
        total_distance = 0
        elevation_profiles = {}
        
        for i in range(len(gps_data) - 1):
            p1 = gps_data[i]
            p2 = gps_data[i + 1]
            
            # Simple distance calculation (approximate)
            lat_diff = abs(p2["latitude"] - p1["latitude"])
            lon_diff = abs(p2["longitude"] - p1["longitude"])
            # Rough conversion: 1 degree ≈ 111 km
            distance_km = ((lat_diff ** 2 + lon_diff ** 2) ** 0.5) * 111
            total_distance += distance_km
            
            # Group elevation profiles by trail
            trail_id = p1["trail_id"]
            if trail_id not in elevation_profiles:
                elevation_profiles[trail_id] = []
            elevation_profiles[trail_id].append({
                "elevation": p1.get("elevation", 0),
                "timestamp": i
            })
        
        # Calculate total elevation gain
        total_elevation_gain = 0
        for trail_id, profile in elevation_profiles.items():
            elevations = [p["elevation"] for p in profile if p["elevation"]]
            if elevations:
                total_elevation_gain += max(elevations) - min(elevations)
        
        return {
            "total_distance_km": round(total_distance, 2),
            "total_elevation_gain_m": int(total_elevation_gain),
            "gps_points_count": len(gps_data),
            "elevation_profiles": {
                trail_id: profile[:100]  # Limit to 100 points per trail
                for trail_id, profile in elevation_profiles.items()
            }
        }
    
    def calculate_heart_rate_trends(self, user_id: int) -> Dict:
        """Calculate heart rate trends over time."""
        metrics = self._get_aggregated_heart_rate_metrics(user_id)
        return {
            "trends": metrics.get("heart_rate_trend", []),
            "overall_avg": metrics.get("avg_heart_rate"),
            "overall_max": metrics.get("max_heart_rate"),
            "overall_min": metrics.get("min_heart_rate")
        }
    
    def calculate_gps_aggregates(self, user_id: int) -> Dict:
        """Calculate GPS-based aggregates (total distance, elevation gain from GPS data)."""
        return self._get_aggregated_gps_metrics(user_id)
    
    def calculate_performance_improvements(self, user_id: int) -> Dict:
        """Compare actual vs predicted performance over time."""
        completed_trails = self._get_completed_trails_with_details(user_id)
        
        if not completed_trails:
            return {
                "improvements": [],
                "avg_duration_diff_pct": 0,
                "avg_hr_diff_pct": 0,
                "avg_speed_diff_pct": 0
            }
        
        improvements = []
        duration_diffs = []
        hr_diffs = []
        speed_diffs = []
        
        for trail in completed_trails:
            if not trail.get("predicted_duration"):
                continue
            
            actual_duration = trail.get("actual_duration", 0)
            predicted_duration = trail.get("predicted_duration", 0)
            actual_hr = trail.get("avg_heart_rate")
            predicted_hr = trail.get("predicted_avg_heart_rate")
            actual_speed = trail.get("avg_speed")
            predicted_speed = trail.get("predicted_avg_speed")
            
            duration_diff_pct = 0
            hr_diff_pct = 0
            speed_diff_pct = 0
            
            if predicted_duration > 0:
                duration_diff_pct = ((actual_duration - predicted_duration) / predicted_duration) * 100
                duration_diffs.append(duration_diff_pct)
            
            if predicted_hr and actual_hr:
                hr_diff_pct = ((actual_hr - predicted_hr) / predicted_hr) * 100
                hr_diffs.append(hr_diff_pct)
            
            if predicted_speed and actual_speed:
                speed_diff_pct = ((actual_speed - predicted_speed) / predicted_speed) * 100
                speed_diffs.append(speed_diff_pct)
            
            improvements.append({
                "trail_id": trail.get("trail_id"),
                "completion_date": trail.get("completion_date"),
                "duration_diff_pct": round(duration_diff_pct, 1),
                "hr_diff_pct": round(hr_diff_pct, 1),
                "speed_diff_pct": round(speed_diff_pct, 1)
            })
        
        return {
            "improvements": improvements,
            "avg_duration_diff_pct": round(sum(duration_diffs) / len(duration_diffs), 1) if duration_diffs else 0,
            "avg_hr_diff_pct": round(sum(hr_diffs) / len(hr_diffs), 1) if hr_diffs else 0,
            "avg_speed_diff_pct": round(sum(speed_diffs) / len(speed_diffs), 1) if speed_diffs else 0
        }
    
    def _get_saved_trails(self, user_id: int) -> List[Dict]:
        """Get saved trails for a user."""
        conn = sqlite3.connect(self.users_db)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM saved_trails WHERE user_id = ?", (user_id,))
        trails = [dict(row) for row in cur.fetchall()]
        conn.close()
        return trails
    
    def _get_started_trails(self, user_id: int) -> List[Dict]:
        """Get started trails for a user."""
        conn = sqlite3.connect(self.users_db)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM started_trails WHERE user_id = ?", (user_id,))
        trails = [dict(row) for row in cur.fetchall()]
        conn.close()
        return trails
    
    def _calculate_heart_rate_zones(self, heart_rates: List[int]) -> Dict:
        """Calculate heart rate zones from heart rate data."""
        if not heart_rates:
            return {
                "resting": 0,
                "active": 0,
                "peak": 0,
                "avg": 0,
                "max": 0
            }
        
        avg_hr = statistics.mean(heart_rates)
        max_hr = max(heart_rates)
        
        # Simple zones (can be improved with age-based calculations)
        resting = sum(1 for hr in heart_rates if hr < 100)
        active = sum(1 for hr in heart_rates if 100 <= hr < 150)
        peak = sum(1 for hr in heart_rates if hr >= 150)
        
        total = len(heart_rates)
        return {
            "resting": round((resting / total) * 100, 1) if total > 0 else 0,
            "active": round((active / total) * 100, 1) if total > 0 else 0,
            "peak": round((peak / total) * 100, 1) if total > 0 else 0,
            "avg": round(avg_hr, 1),
            "max": max_hr
        }
    
    def _calculate_training_consistency(self, completed_trails: List[Dict]) -> Dict:
        """Calculate training consistency metrics."""
        if not completed_trails:
            return {"consistency_score": 0, "trails_per_month": 0}
        
        # Group by month
        monthly_counts = defaultdict(int)
        for trail in completed_trails:
            date_str = trail.get("completion_date", "")
            if date_str:
                try:
                    date_obj = datetime.fromisoformat(date_str.split("T")[0])
                    month_key = f"{date_obj.year}-{date_obj.month:02d}"
                    monthly_counts[month_key] += 1
                except:
                    pass
        
        if not monthly_counts:
            return {"consistency_score": 0, "trails_per_month": 0}
        
        avg_per_month = statistics.mean(list(monthly_counts.values()))
        consistency_score = min(100, avg_per_month * 10)  # Scale to 0-100
        
        return {
            "consistency_score": round(consistency_score, 1),
            "trails_per_month": round(avg_per_month, 1),
            "monthly_breakdown": dict(monthly_counts)
        }
    
    def _calculate_longest_streak(self, completed_trails: List[Dict]) -> int:
        """Calculate longest consecutive completion streak."""
        if not completed_trails:
            return 0
        
        sorted_trails = sorted(completed_trails, key=lambda t: t.get("completion_date", ""))
        
        streak = 1
        max_streak = 1
        
        for i in range(1, len(sorted_trails)):
            try:
                prev_date = datetime.fromisoformat(sorted_trails[i-1].get("completion_date", "").split("T")[0])
                curr_date = datetime.fromisoformat(sorted_trails[i].get("completion_date", "").split("T")[0])
                days_diff = (curr_date - prev_date).days
                
                if days_diff <= 7:  # Within a week
                    streak += 1
                    max_streak = max(max_streak, streak)
                else:
                    streak = 1
            except:
                pass
        
        return max_streak
    
    # Empty metrics helpers
    
    def _empty_elevation_metrics(self) -> Dict:
        return {
            "top_elevation_trails": [],
            "elevation_gain_over_time": [],
            "avg_elevation_speed": 0,
            "highest_point": 0,
            "elevation_distribution": {},
            "peak_achievements": []
        }
    
    def _empty_fitness_metrics(self) -> Dict:
        return {
            "heart_rate_zones": {"resting": 0, "active": 0, "peak": 0, "avg": 0, "max": 0},
            "heart_rate_trends": [],
            "distance_over_time": [],
            "calories_burned": 0,
            "speed_trends": [],
            "training_consistency": {"consistency_score": 0, "trails_per_month": 0}
        }
    
    def _empty_exploration_metrics(self) -> Dict:
        return {
            "unique_regions": [],
            "trail_diversity_score": 0,
            "landscapes_discovered": {},
            "rare_trail_types": {},
            "exploration_map": []
        }
    
    def _empty_photography_metrics(self) -> Dict:
        return {
            "scenic_trails": [],
            "best_photo_opportunities": [],
            "landscape_variety": {},
            "peak_viewing_times": [],
            "instagram_locations": []
        }
    
    def _empty_contemplative_metrics(self) -> Dict:
        return {
            "scenic_beauty_score": 0,
            "quiet_trails": [],
            "avg_time_spent": 0,
            "meditation_friendly": [],
            "nature_immersion": {"total_nature_trails": 0, "percentage": 0}
        }
    
    def _empty_performance_metrics(self) -> Dict:
        return {
            "performance_trends": [],
            "personal_records": {},
            "improvement_metrics": {},
            "comparison_to_average": {}
        }
