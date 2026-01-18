# -*- coding: utf-8 -*-
"""
User profiling system based on trail history.
Calculates statistics and maps users to behavioral profiles.
"""

import statistics
import sqlite3
import os
from collections import Counter
from typing import Dict, List, Optional, Tuple
from backend.db import get_trail

BASE_DIR = os.path.dirname(__file__)
USERS_DB = os.path.join(BASE_DIR, "users.db")


class UserProfiler:
    """Calculates user profile statistics from trail history."""
    
    PROFILE_NAMES = {
        "elevation_lover": "L'Amateur de dénivelé",
        "performance_athlete": "Le Sportif de performance",
        "contemplative": "Le Contemplatif",
        "casual": "Le Randonneur occasionnel",
        "family": "La Famille / Groupe hétérogène",
        "explorer": "L'Explorateur / Aventurier",
        "photographer": "Le Photographe / Créateur de contenu"
    }
    
    def calculate_statistics(self, user_id: int) -> Dict:
        """
        Calculate statistics from user's completed trails.
        
        Returns:
            {
                "distance": {"mean": float, "median": float, "q25": float, "q75": float},
                "elevation_gain": {...},
                "difficulty": {...},
                "landscapes": {"lake": 0.3, "peaks": 0.5, ...},  # frequencies
                "safety_risks": {"none": 0.8, "low": 0.2, ...},
                "trail_type": {"loop": 0.6, "one_way": 0.4},
                "avg_popularity": float,
                "trail_count": int
            }
        """
        # Get completed trails directly from database to avoid circular import
        conn = sqlite3.connect(USERS_DB)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT trail_id, completion_date, rating FROM completed_trails WHERE user_id=? ORDER BY completion_date DESC", (user_id,))
        completed_trails = [dict(row) for row in cur.fetchall()]
        conn.close()
        
        if not completed_trails:
            return {"trail_count": 0}
        
        # Get full trail data
        trail_data = []
        for ct in completed_trails:
            trail = get_trail(ct["trail_id"])
            if trail:
                trail_data.append(trail)
        
        if not trail_data:
            return {"trail_count": 0}
        
        stats = {
            "trail_count": len(trail_data),
            "distance": self._calc_stats([t.get("distance", 0) for t in trail_data]),
            "elevation_gain": self._calc_stats([t.get("elevation_gain", 0) for t in trail_data]),
            "difficulty": self._calc_stats([t.get("difficulty", 0) for t in trail_data]),
            "duration": self._calc_stats([t.get("duration", 0) for t in trail_data]),
            "landscapes": self._calc_landscape_freq(trail_data),
            "safety_risks": self._calc_safety_distribution(trail_data),
            "trail_type": self._calc_trail_type_distribution(trail_data),
            "avg_popularity": statistics.mean([t.get("popularity", 0) for t in trail_data]),
        }
        
        # Add standard deviation for popularity if we have enough data
        popularity_values = [t.get("popularity", 0) for t in trail_data]
        if len(popularity_values) > 1:
            stats["popularity_std"] = statistics.stdev(popularity_values)
        else:
            stats["popularity_std"] = 0
        
        return stats
    
    def _calc_stats(self, values: List[float]) -> Dict:
        """Calculate mean, median, quartiles for a list of values."""
        if not values:
            return {}
        sorted_vals = sorted(values)
        n = len(sorted_vals)
        result = {
            "mean": statistics.mean(values),
            "median": sorted_vals[n // 2],
        }
        
        # Calculate quartiles
        if n >= 4:
            result["q25"] = sorted_vals[n // 4]
            result["q75"] = sorted_vals[3 * n // 4]
        else:
            result["q25"] = sorted_vals[0]
            result["q75"] = sorted_vals[-1]
        
        # Calculate standard deviation
        if n > 1:
            result["std"] = statistics.stdev(values)
        else:
            result["std"] = 0
        
        return result
    
    def _calc_landscape_freq(self, trails: List[Dict]) -> Dict[str, float]:
        """Calculate frequency of each landscape tag."""
        all_landscapes = []
        for trail in trails:
            landscapes = trail.get("landscapes", "")
            if landscapes:
                all_landscapes.extend([l.strip() for l in landscapes.split(",")])
        
        if not all_landscapes:
            return {}
        
        counter = Counter(all_landscapes)
        total = len(all_landscapes)
        return {landscape: count / total for landscape, count in counter.items()}
    
    def _calc_safety_distribution(self, trails: List[Dict]) -> Dict[str, float]:
        """Calculate distribution of safety risks."""
        risk_counts = Counter()
        for trail in trails:
            risks = trail.get("safety_risks", "none")
            if risks:
                risk_list = [r.strip() for r in risks.split(",")]
                for risk in risk_list:
                    risk_counts[risk] += 1
            else:
                risk_counts["none"] += 1
        
        total = len(trails)
        return {risk: count / total for risk, count in risk_counts.items()}
    
    def _calc_trail_type_distribution(self, trails: List[Dict]) -> Dict[str, float]:
        """Calculate distribution of loop vs one_way."""
        type_counts = Counter()
        for trail in trails:
            trail_type = trail.get("trail_type", "one_way")
            type_counts[trail_type] += 1
        
        total = len(trails)
        return {ttype: count / total for ttype, count in type_counts.items()}
    
    def detect_profile(self, user_id: int) -> Tuple[Optional[str], Dict]:
        """
        Detect user profile from statistics.
        Returns a single primary profile even if multiple profiles have the same score.
        
        Returns:
            (profile_name, confidence_scores)
        """
        stats = self.calculate_statistics(user_id)
        
        if stats.get("trail_count", 0) < 3:
            # Not enough data
            return None, {}
        
        scores = self._score_profiles(stats)
        if not scores:
            return None, {}
        
        # Find the maximum score
        max_score = max(scores.values())
        
        # Get all profiles with the maximum score
        profiles_with_max_score = [profile for profile, score in scores.items() if score == max_score]
        
        # If multiple profiles have the same max score, use a deterministic priority order
        # This ensures we always return a single profile
        if len(profiles_with_max_score) > 1:
            # Priority order for tie-breaking (based on profile importance/complexity)
            priority_order = [
                "elevation_lover",
                "performance_athlete", 
                "explorer",
                "photographer",
                "contemplative",
                "family",
                "casual"
            ]
            # Select the first profile in priority order that has the max score
            for profile in priority_order:
                if profile in profiles_with_max_score:
                    return profile, scores
            # Fallback: return the first one alphabetically if not in priority list
            best_profile = sorted(profiles_with_max_score)[0]
        else:
            best_profile = profiles_with_max_score[0]
        
        return best_profile, scores
    
    def _score_profiles(self, stats: Dict) -> Dict[str, float]:
        """Score each profile based on statistics."""
        scores = {}
        
        # 1. Amateur de dénivelé (Elevation Enthusiast)
        elev_median = stats.get("elevation_gain", {}).get("median", 0)
        elev_mean = stats.get("elevation_gain", {}).get("mean", 0)
        difficulty_mean = stats.get("difficulty", {}).get("mean", 0)
        distance_mean = stats.get("distance", {}).get("mean", 0)
        # Normalize elevation score (700m = 0.7, 1000m+ = 1.0) - Focus on high elevation
        elev_score = min(1.0, elev_median / 700.0) if elev_median > 0 else 0
        diff_score = min(1.0, difficulty_mean / 10.0)
        # Low sensitivity to distance if elevation is high (threshold raised to 600m)
        distance_penalty = 0 if elev_median > 600 else min(0.15, (distance_mean / 15.0) * 0.15)
        # Boost if both elevation and difficulty are high - but don't over-penalize others
        if elev_median > 700 and difficulty_mean > 6.5:
            scores["elevation_lover"] = max(0, (elev_score * 0.7 + diff_score * 0.3) - distance_penalty) * 1.15
        elif elev_median > 600 and difficulty_mean > 6.0:
            scores["elevation_lover"] = max(0, (elev_score * 0.65 + diff_score * 0.35) - distance_penalty) * 1.05
        else:
            scores["elevation_lover"] = max(0, (elev_score * 0.6 + diff_score * 0.4) - distance_penalty) * 0.9  # Slight penalty if not high enough
        
        # 2. Sportif de performance (Performance Athlete)
        distance_mean = stats.get("distance", {}).get("mean", 0)
        duration_mean = stats.get("duration", {}).get("mean", 0)
        loop_ratio = stats.get("trail_type", {}).get("loop", 0)
        distance_score = min(1.0, distance_mean / 12.0)  # Prefer longer trails
        duration_score = min(1.0, duration_mean / 150.0)  # Prefer longer duration
        # Low variance in terrain (std of difficulty) - consistent difficulty preferred
        difficulty_std = stats.get("difficulty", {}).get("std", 0)
        variance_score = max(0.5, 1.0 - (difficulty_std / 4.0))  # Prefer consistency
        # Bonus for loops (preferred for training)
        loop_bonus = loop_ratio * 0.15
        # Check if user matches Photographer criteria (peaks/lakes landscapes, one-way) - if so, reduce Performance score
        landscapes = stats.get("landscapes", {})
        target_landscapes = ["lake", "peaks"]
        target_score = sum(landscapes.get(l, 0) for l in target_landscapes)
        one_way_ratio = stats.get("trail_type", {}).get("one_way", 0)
        is_likely_photographer = target_score > 0.6 and one_way_ratio > 0.5
        # Check if user matches Elevation Enthusiast criteria (high elevation >700m, high difficulty >6.5)
        elev_median = stats.get("elevation_gain", {}).get("median", 0)
        difficulty_mean = stats.get("difficulty", {}).get("mean", 0)
        is_likely_elevation = elev_median > 700 and difficulty_mean > 6.5
        # Boost if distance AND duration are both high - key differentiator
        # But reduce boost if user is likely Photographer or Elevation Enthusiast (to avoid misclassification)
        if is_likely_photographer:
            # Penalty for Photographer users - they should be Photographer, not Performance Athlete
            if distance_mean > 10.0 and duration_mean > 120:
                scores["performance_athlete"] = (distance_score * 0.45 + duration_score * 0.4 + 
                                                variance_score * 0.1 + loop_bonus) * 0.85
            elif distance_mean > 8.0 and duration_mean > 90:
                scores["performance_athlete"] = (distance_score * 0.4 + duration_score * 0.4 + 
                                                variance_score * 0.15 + loop_bonus) * 0.9
            else:
                scores["performance_athlete"] = (distance_score * 0.35 + duration_score * 0.35 + 
                                                variance_score * 0.2 + loop_bonus) * 0.8
        elif is_likely_elevation:
            # Penalty for Elevation Enthusiast users - they should be Elevation Enthusiast, not Performance Athlete
            if distance_mean > 10.0 and duration_mean > 120:
                scores["performance_athlete"] = (distance_score * 0.45 + duration_score * 0.4 + 
                                                variance_score * 0.1 + loop_bonus) * 0.9
            elif distance_mean > 8.0 and duration_mean > 90:
                scores["performance_athlete"] = (distance_score * 0.4 + duration_score * 0.4 + 
                                                variance_score * 0.15 + loop_bonus) * 0.95
            else:
                scores["performance_athlete"] = (distance_score * 0.35 + duration_score * 0.35 + 
                                                variance_score * 0.2 + loop_bonus) * 0.85
        elif distance_mean > 10.0 and duration_mean > 120:
            scores["performance_athlete"] = (distance_score * 0.45 + duration_score * 0.4 + 
                                            variance_score * 0.1 + loop_bonus) * 1.15
        elif distance_mean > 8.0 and duration_mean > 90:
            scores["performance_athlete"] = (distance_score * 0.4 + duration_score * 0.4 + 
                                            variance_score * 0.15 + loop_bonus) * 1.05
        else:
            scores["performance_athlete"] = (distance_score * 0.35 + duration_score * 0.35 + 
                                            variance_score * 0.2 + loop_bonus) * 0.9  # Penalty if not long enough
        
        # 3. Contemplatif (Contemplative Hiker)
        landscapes = stats.get("landscapes", {})
        # Focus on truly scenic landscapes (peaks are most common in dataset)
        contemplative_landscapes = ["lake", "peaks", "glacier"]
        contemplative_score = sum(landscapes.get(l, 0) for l in contemplative_landscapes)
        popularity = stats.get("avg_popularity", 0)
        # Moderate popularity (6.5-7.5 is ideal) - Scenic spots are moderately popular
        popularity_score = 1.0 if 6.5 <= popularity <= 7.5 else (0.85 if 6.8 <= popularity <= 7.2 else (0.6 if 6.0 <= popularity <= 8.0 else 0.3))
        # Strong boost if strong landscape preference (peaks) with moderate popularity - key differentiator
        if contemplative_score >= 0.7 and 6.5 <= popularity <= 7.5:
            scores["contemplative"] = (contemplative_score * 0.6 + popularity_score * 0.4) * 1.4
        elif contemplative_score >= 0.6 and 6.8 <= popularity <= 7.2:
            scores["contemplative"] = (contemplative_score * 0.6 + popularity_score * 0.4) * 1.3
        elif contemplative_score >= 0.5 and 6.5 <= popularity <= 7.5:
            scores["contemplative"] = (contemplative_score * 0.55 + popularity_score * 0.45) * 1.15
        else:
            scores["contemplative"] = (contemplative_score * 0.5 + popularity_score * 0.5) * 0.7  # Penalty if criteria not met
        
        # 4. Randonneur occasionnel (Casual Hiker)
        distance_mean = stats.get("distance", {}).get("mean", 0)
        difficulty_mean = stats.get("difficulty", {}).get("mean", 0)
        safety_none = stats.get("safety_risks", {}).get("none", 0)
        # Prefer shorter trails - very strict for casual
        distance_score = max(0, 1.0 - (distance_mean / 5.0))  # 5km = 0, 0km = 1.0
        # Prefer easier trails - very strict for casual
        difficulty_score = max(0, 1.0 - (difficulty_mean / 4.5))  # 4.5 = 0, 0 = 1.0
        # Strong boost if both distance and difficulty are low - key differentiator for casual
        # Increase boost to better compete with Explorer
        if distance_mean < 4.0 and difficulty_mean < 3.8:
            scores["casual"] = (distance_score * 0.55 + difficulty_score * 0.35 + safety_none * 0.1) * 1.7
        elif distance_mean < 4.5 and difficulty_mean < 4.0:
            scores["casual"] = (distance_score * 0.5 + difficulty_score * 0.4 + safety_none * 0.1) * 1.55
        elif distance_mean < 5.0 and difficulty_mean < 4.5:
            scores["casual"] = (distance_score * 0.45 + difficulty_score * 0.4 + safety_none * 0.15) * 1.35
        else:
            scores["casual"] = (distance_score * 0.4 + difficulty_score * 0.35 + safety_none * 0.25) * 0.8  # Penalty if too long/hard
        
        # 5. Famille / Groupe (Family / Group Hiker)
        difficulty_mean = stats.get("difficulty", {}).get("mean", 0)
        safety_none = stats.get("safety_risks", {}).get("none", 0)
        landscapes_count = len(stats.get("landscapes", {}))
        variety_score = min(1.0, landscapes_count / 2.0)  # Prefer variety
        # Prefer easier trails - very strict for family
        difficulty_score = max(0, 1.0 - (difficulty_mean / 4.0))  # 4.0 = 0, 0 = 1.0
        # Safety is critical for family - strong boost if high safety
        # Check if user matches Casual criteria (short AND easy) - if so, reduce Family score
        distance_mean = stats.get("distance", {}).get("mean", 0)
        is_likely_casual = distance_mean < 4.5 and difficulty_mean < 4.0
        # Strong boost if low difficulty AND high safety (key differentiator for family)
        # But reduce boost if user is likely Casual (to avoid misclassification)
        if is_likely_casual:
            # Penalty for Casual users - they should be Casual, not Family
            if difficulty_mean < 3.8 and safety_none > 0.85:
                scores["family"] = (difficulty_score * 0.5 + safety_none * 0.4 + variety_score * 0.1) * 0.9
            elif difficulty_mean < 4.0 and safety_none > 0.8:
                scores["family"] = (difficulty_score * 0.5 + safety_none * 0.4 + variety_score * 0.1) * 0.85
            else:
                scores["family"] = (difficulty_score * 0.45 + safety_none * 0.45 + variety_score * 0.1) * 0.8
        elif difficulty_mean < 3.8 and safety_none > 0.85:
            scores["family"] = (difficulty_score * 0.5 + safety_none * 0.4 + variety_score * 0.1) * 1.5
        elif difficulty_mean < 4.0 and safety_none > 0.8:
            scores["family"] = (difficulty_score * 0.5 + safety_none * 0.4 + variety_score * 0.1) * 1.4
        elif difficulty_mean < 4.5 and safety_none > 0.7:
            scores["family"] = (difficulty_score * 0.45 + safety_none * 0.45 + variety_score * 0.1) * 1.25
        else:
            scores["family"] = (difficulty_score * 0.4 + safety_none * 0.4 + variety_score * 0.2) * 0.85  # Penalty if too hard/unsafe
        
        # 6. Explorateur / Aventurier (Explorer / Adventurer)
        popularity = stats.get("avg_popularity", 0)
        landscapes = stats.get("landscapes", {})
        # Rare landscapes - alpine is common, so we need to be more selective
        rare_landscapes = ["glacier", "alpine"]
        rare_score = sum(landscapes.get(l, 0) for l in rare_landscapes)
        # Low popularity + accepts risks - key differentiator
        safety_risks = stats.get("safety_risks", {})
        risk_acceptance = 1.0 - safety_risks.get("none", 1.0)
        # Prefer low popularity - adjust for dataset where avg is 8.2
        # Score higher if popularity is significantly below average
        popularity_score = max(0, 1.0 - ((popularity - 7.5) / 2.0))  # 7.5 = good, 9.5 = bad
        # Check if user matches Casual/Family criteria - if so, reduce Explorer score
        distance_mean = stats.get("distance", {}).get("mean", 0)
        difficulty_mean = stats.get("difficulty", {}).get("mean", 0)
        # More strict criteria for Casual (short AND easy)
        is_likely_casual = distance_mean < 4.5 and difficulty_mean < 4.0
        # Family criteria (easy AND safe)
        is_likely_family = difficulty_mean < 4.0 and safety_risks.get("none", 0) > 0.8
        is_likely_casual_or_family = is_likely_casual or is_likely_family
        # Boost if popularity is below 7.0 (significantly below dataset average) - key differentiator
        # But reduce boost significantly if user is likely Casual/Family (to avoid misclassification)
        if is_likely_casual:
            # Strong penalty for Casual users - they shouldn't be Explorers
            scores["explorer"] = (popularity_score * 0.4 + rare_score * 0.35 + risk_acceptance * 0.25) * 0.6
        elif is_likely_family:
            # Penalty for Family users - they shouldn't be Explorers
            scores["explorer"] = (popularity_score * 0.4 + rare_score * 0.35 + risk_acceptance * 0.25) * 0.7
        elif popularity < 7.0 and not is_likely_casual_or_family:
            scores["explorer"] = (popularity_score * 0.5 + rare_score * 0.3 + risk_acceptance * 0.2) * 1.25
        elif popularity < 7.5 and not is_likely_casual_or_family:
            scores["explorer"] = (popularity_score * 0.45 + rare_score * 0.35 + risk_acceptance * 0.2) * 1.1
        elif popularity < 8.0:
            scores["explorer"] = (popularity_score * 0.4 + rare_score * 0.35 + risk_acceptance * 0.25) * 1.0
        else:
            scores["explorer"] = (popularity_score * 0.4 + rare_score * 0.35 + risk_acceptance * 0.25) * 0.85  # Penalty if too popular
        
        # 7. Photographe (Photographer / Content Creator)
        landscapes = stats.get("landscapes", {})
        target_landscapes = ["lake", "peaks"]
        target_score = sum(landscapes.get(l, 0) for l in target_landscapes)
        one_way_ratio = stats.get("trail_type", {}).get("one_way", 0)
        duration_mean = stats.get("duration", {}).get("mean", 0)
        # Flexible duration (60-240 min is ideal for photography) - more selective
        duration_flexibility = 1.0 if 60 <= duration_mean <= 240 else (0.8 if 45 <= duration_mean <= 300 else 0.5)
        # Check if user matches Performance Athlete criteria (long distance) - if so, reduce Performance score
        distance_mean = stats.get("distance", {}).get("mean", 0)
        is_likely_performance = distance_mean > 10.0
        # Boost if strong preference for target landscapes (peaks/lakes) with one-way trails
        # Peaks are most common, so we need to ensure it's significant
        if target_score > 0.7 and one_way_ratio > 0.6:  # Strong preference + one-way
            scores["photographer"] = (target_score * 0.5 + one_way_ratio * 0.35 + duration_flexibility * 0.15) * 1.25
        elif target_score > 0.6 and one_way_ratio > 0.5:  # At least 60% landscapes + mostly one-way
            scores["photographer"] = (target_score * 0.5 + one_way_ratio * 0.3 + duration_flexibility * 0.2) * 1.1
        elif target_score > 0.6:  # At least 60% of landscapes are lake/peaks
            scores["photographer"] = (target_score * 0.5 + one_way_ratio * 0.3 + duration_flexibility * 0.2) * 1.05
        else:
            scores["photographer"] = (target_score * 0.45 + one_way_ratio * 0.3 + duration_flexibility * 0.25) * 0.75
        
        return scores
