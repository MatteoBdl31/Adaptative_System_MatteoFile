# -*- coding: utf-8 -*-
"""
Trail recommendation service for generating profile-specific AI recommendations.
"""

from typing import Dict, List, Optional
import sqlite3
from backend.explanation_service import ExplanationService
from backend.weather_service import get_weekly_forecast, get_weather_recommendations
from backend.trail_analytics import TrailAnalytics
from backend.db import get_trail, get_user, USERS_DB


class TrailRecommendationService:
    """Generates profile-specific AI recommendations for saved trails."""
    
    def __init__(self):
        self.explanation_service = ExplanationService()
        self.analytics = TrailAnalytics()
    
    def generate_trail_recommendations(
        self,
        trail: Dict,
        user: Dict,
        weather_forecast: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Generate AI-powered recommendations for a trail based on user profile.
        
        Args:
            trail: Trail dictionary
            user: User dictionary
            weather_forecast: Optional weekly weather forecast
        
        Returns:
            {
                "profile_recommendations": Dict,
                "weather_recommendations": Dict,
                "performance_tips": Dict,
                "safety_tips": List[str],
                "ai_explanation": Dict
            }
        """
        user_profile = user.get("detected_profile")
        
        # Generate profile-specific recommendations
        profile_recommendations = self._generate_profile_recommendations(trail, user, user_profile)
        
        # Get weather recommendations if forecast provided
        weather_recommendations = {}
        if weather_forecast:
            weather_recommendations = get_weather_recommendations(trail, weather_forecast)
        elif trail.get("latitude") and trail.get("longitude"):
            # Fetch forecast if not provided
            forecast = get_weekly_forecast(trail["latitude"], trail["longitude"])
            if forecast:
                weather_recommendations = get_weather_recommendations(trail, forecast)
        
        # Generate performance tips
        performance_tips = self._generate_performance_tips(trail, user)
        
        # Generate safety tips
        safety_tips = self._generate_safety_tips(trail, user)
        
        # Get similar profile hiker context (exclude current user)
        similar_hiker_context = self._get_similar_profile_context(trail, user_profile, user.get("id"))
        
        # Generate AI explanation with similar hiker context
        ai_explanation = self._generate_ai_explanation(
            trail, user, user_profile, weather_recommendations, similar_hiker_context
        )
        
        return {
            "profile_recommendations": profile_recommendations,
            "weather_recommendations": weather_recommendations,
            "performance_tips": performance_tips,
            "safety_tips": safety_tips,
            "ai_explanation": ai_explanation
        }
    
    def _generate_profile_recommendations(
        self,
        trail: Dict,
        user: Dict,
        profile: Optional[str]
    ) -> Dict:
        """Generate profile-specific recommendations."""
        recommendations = {
            "tips": [],
            "best_times": [],
            "highlights": []
        }
        
        if profile == "elevation_lover":
            elevation_gain = trail.get("elevation_gain", 0)
            if elevation_gain > 700:
                recommendations["tips"].append(
                    f"This trail offers {elevation_gain}m of elevation gain - perfect for elevation enthusiasts!"
                )
                recommendations["tips"].append(
                    "Start early in the morning to reach the peak during optimal conditions."
                )
                recommendations["highlights"].append("Steepest sections are in the middle third of the trail")
                recommendations["highlights"].append("Peak offers panoramic views - bring a camera!")
            else:
                recommendations["tips"].append(
                    f"At {elevation_gain}m elevation gain, this trail is moderate. Consider more challenging options if seeking elevation."
                )
        
        elif profile == "performance_athlete":
            distance = trail.get("distance", 0)
            duration = trail.get("duration", 0)
            trail_type = trail.get("trail_type", "")
            
            if trail_type == "loop":
                recommendations["tips"].append("Loop trail - great for training consistency!")
            else:
                recommendations["tips"].append("One-way trail - plan transportation for return")
            
            if distance > 10:
                recommendations["tips"].append(
                    f"Long distance trail ({distance}km) - perfect for endurance training"
                )
                recommendations["tips"].append("Maintain steady pace - aim for consistent heart rate zones")
            
            recommendations["highlights"].append(f"Estimated duration: {duration} minutes - plan hydration breaks")
        
        elif profile == "photographer":
            landscapes = trail.get("landscapes", "")
            trail_type = trail.get("trail_type", "")
            
            if "peaks" in landscapes or "lake" in landscapes:
                recommendations["tips"].append("Scenic trail with great photo opportunities!")
                recommendations["best_times"].append("Golden hour (sunrise/sunset) for best lighting")
                recommendations["best_times"].append("Mid-morning for clear mountain views")
            
            if trail_type == "one_way":
                recommendations["tips"].append("One-way trail allows for uninterrupted photography")
            
            recommendations["highlights"].append("Look for viewpoints marked on trail maps")
            recommendations["highlights"].append("Bring extra batteries - cold at elevation drains batteries faster")
        
        elif profile == "explorer":
            popularity = trail.get("popularity", 0)
            region = trail.get("region", "unknown")
            
            if popularity < 7.0:
                recommendations["tips"].append("Less popular trail - perfect for exploration!")
                recommendations["tips"].append("Bring navigation tools - trail may be less marked")
            
            recommendations["highlights"].append(f"Located in {region} - explore nearby areas")
            recommendations["tips"].append("Check for alternative routes or side trails")
        
        elif profile == "contemplative":
            popularity = trail.get("popularity", 0)
            landscapes = trail.get("landscapes", "")
            
            if popularity < 7.0:
                recommendations["tips"].append("Quiet trail - perfect for contemplation")
            
            if "forest" in landscapes or "meadow" in landscapes:
                recommendations["tips"].append("Natural setting ideal for meditation and reflection")
                recommendations["best_times"].append("Early morning for solitude")
            
            recommendations["highlights"].append("Take your time - enjoy the scenery")
        
        elif profile == "casual" or profile == "family":
            difficulty = trail.get("difficulty", 5.0)
            distance = trail.get("distance", 0)
            
            if difficulty <= 4.0 and distance <= 6.0:
                recommendations["tips"].append("Easy trail perfect for casual hiking")
            else:
                recommendations["tips"].append(
                    f"Moderate difficulty ({difficulty}/10) - take breaks as needed"
                )
            
            recommendations["tips"].append("Bring snacks and water - pace yourself")
            recommendations["highlights"].append("Family-friendly - suitable for all ages")
        
        else:
            # Default recommendations
            recommendations["tips"].append("Enjoy this trail at your own pace")
            recommendations["tips"].append("Check weather conditions before starting")
        
        return recommendations
    
    def _generate_performance_tips(self, trail: Dict, user: Dict) -> Dict:
        """Generate performance optimization tips."""
        # Predict metrics
        predictions = self.analytics.predict_metrics(trail, user)
        
        tips = {
            "predicted_duration": predictions.get("predicted_duration"),
            "pacing_tips": [],
            "heart_rate_tips": [],
            "nutrition_tips": []
        }
        
        predicted_hr = predictions.get("predicted_heart_rate", {})
        if predicted_hr:
            avg_hr = predicted_hr.get("avg", 0)
            tips["heart_rate_tips"].append(
                f"Target average heart rate: {avg_hr} bpm"
            )
            tips["heart_rate_tips"].append(
                "Monitor heart rate - slow down if exceeding target zone"
            )
        
        predicted_speed = predictions.get("predicted_speed", 0)
        if predicted_speed:
            tips["pacing_tips"].append(
                f"Recommended average speed: {predicted_speed} km/h"
            )
            tips["pacing_tips"].append("Start slower than target pace - conserve energy for elevation")
        
        predicted_calories = predictions.get("predicted_calories", 0)
        if predicted_calories:
            tips["nutrition_tips"].append(
                f"Estimated calorie burn: {predicted_calories} calories"
            )
            tips["nutrition_tips"].append("Bring energy snacks - consume 200-300 calories per hour")
        
        return tips
    
    def _generate_safety_tips(self, trail: Dict, user: Dict) -> List[str]:
        """Generate safety recommendations."""
        tips = []
        
        # Check elevation
        elevation_gain = trail.get("elevation_gain", 0)
        if elevation_gain > 800:
            tips.append("High elevation trail - be aware of altitude sickness symptoms")
            tips.append("Descend if experiencing headaches, nausea, or dizziness")
        
        # Check difficulty
        difficulty = trail.get("difficulty", 5.0)
        if difficulty > 7.0:
            tips.append("Challenging trail - ensure you have proper equipment")
            tips.append("Consider hiking with a partner for difficult sections")
        
        # Check safety risks
        safety_risks = trail.get("safety_risks", "")
        if safety_risks and safety_risks != "none":
            tips.append(f"Trail has safety considerations: {safety_risks}")
            tips.append("Check current trail conditions before starting")
        
        # Fear of heights
        if user.get("fear_of_heights"):
            if elevation_gain > 500:
                tips.append("High elevation trail - be prepared for exposed sections")
        
        # Health constraints
        health_constraints = user.get("health_constraints")
        if health_constraints:
            tips.append(f"Consider your health constraints: {health_constraints}")
            tips.append("Consult with a doctor if unsure about trail suitability")
        
        # General safety
        tips.append("Inform someone of your hiking plans and expected return time")
        tips.append("Bring first aid kit and emergency supplies")
        
        return tips
    
    def _get_similar_profile_context(
        self,
        trail: Dict,
        profile: Optional[str],
        current_user_id: Optional[int] = None
    ) -> Dict:
        """
        Get context from other hikers with similar profiles who completed this trail.
        
        Returns:
            {
                "completion_count": int,
                "average_duration": float,
                "average_rating": float,
                "common_challenges": List[str],
                "insights": List[str],
                "average_heart_rate": float,
                "average_speed": float
            }
        """
        if not profile:
            return {}
        
        trail_id = trail.get("trail_id")
        if not trail_id:
            return {}
        
        try:
            conn = sqlite3.connect(USERS_DB)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            
            # Get users with the same profile who completed this trail (exclude current user)
            if current_user_id:
                cur.execute("""
                    SELECT 
                        ct.actual_duration,
                        ct.rating,
                        ct.avg_heart_rate,
                        ct.max_heart_rate,
                        ct.avg_speed,
                        ct.max_speed,
                        ct.difficulty_rating,
                        ct.completion_date
                    FROM completed_trails ct
                    JOIN user_profiles up ON ct.user_id = up.user_id
                    WHERE ct.trail_id = ? 
                      AND up.primary_profile = ?
                      AND ct.user_id != ?
                    ORDER BY ct.completion_date DESC
                    LIMIT 20
                """, (trail_id, profile, current_user_id))
            else:
                cur.execute("""
                    SELECT 
                        ct.actual_duration,
                        ct.rating,
                        ct.avg_heart_rate,
                        ct.max_heart_rate,
                        ct.avg_speed,
                        ct.max_speed,
                        ct.difficulty_rating,
                        ct.completion_date
                    FROM completed_trails ct
                    JOIN user_profiles up ON ct.user_id = up.user_id
                    WHERE ct.trail_id = ? 
                      AND up.primary_profile = ?
                    ORDER BY ct.completion_date DESC
                    LIMIT 20
                """, (trail_id, profile))
            
            completions = [dict(row) for row in cur.fetchall()]
            conn.close()
            
            if not completions:
                return {}
            
            # Calculate statistics
            durations = [c["actual_duration"] for c in completions if c.get("actual_duration")]
            ratings = [c["rating"] for c in completions if c.get("rating")]
            heart_rates = [c["avg_heart_rate"] for c in completions if c.get("avg_heart_rate")]
            speeds = [c["avg_speed"] for c in completions if c.get("avg_speed")]
            difficulty_ratings = [c["difficulty_rating"] for c in completions if c.get("difficulty_rating")]
            
            context = {
                "completion_count": len(completions),
                "average_duration": sum(durations) / len(durations) if durations else None,
                "average_rating": sum(ratings) / len(ratings) if ratings else None,
                "average_heart_rate": sum(heart_rates) / len(heart_rates) if heart_rates else None,
                "average_speed": sum(speeds) / len(speeds) if speeds else None,
                "average_difficulty_rating": sum(difficulty_ratings) / len(difficulty_ratings) if difficulty_ratings else None,
                "insights": []
            }
            
            # Generate insights based on data
            if context["average_rating"]:
                if context["average_rating"] >= 4.5:
                    context["insights"].append(f"Highly rated by {profile.replace('_', ' ')}s (avg {context['average_rating']:.1f}/5)")
                elif context["average_rating"] <= 3.0:
                    context["insights"].append(f"Mixed reviews from {profile.replace('_', ' ')}s (avg {context['average_rating']:.1f}/5)")
            
            if context["average_duration"]:
                trail_duration = trail.get("duration", 0)
                if context["average_duration"] > trail_duration * 1.2:
                    context["insights"].append(f"Similar hikers typically take {context['average_duration']/60:.1f} hours (longer than estimated)")
                elif context["average_duration"] < trail_duration * 0.8:
                    context["insights"].append(f"Similar hikers typically complete in {context['average_duration']/60:.1f} hours (faster than estimated)")
            
            if context["average_difficulty_rating"]:
                trail_difficulty = trail.get("difficulty", 5.0)
                if context["average_difficulty_rating"] > trail_difficulty + 1:
                    context["insights"].append(f"Similar hikers found it more challenging than expected (rated {context['average_difficulty_rating']:.1f}/10)")
                elif context["average_difficulty_rating"] < trail_difficulty - 1:
                    context["insights"].append(f"Similar hikers found it easier than expected (rated {context['average_difficulty_rating']:.1f}/10)")
            
            return context
            
        except Exception as e:
            print(f"Error getting similar profile context: {e}")
            return {}
    
    def _generate_ai_explanation(
        self,
        trail: Dict,
        user: Dict,
        profile: Optional[str],
        weather_recommendations: Dict,
        similar_hiker_context: Optional[Dict] = None
    ) -> Dict:
        """Generate AI-powered explanation using ExplanationService."""
        # Build prompt
        prompt = self._build_recommendation_prompt(
            trail, user, profile, weather_recommendations, similar_hiker_context
        )
        
        # Generate explanation
        explanation = self.explanation_service.generate_explanation(prompt)
        
        if not explanation:
            # Fallback
            explanation = {
                "explanation_text": f"This trail ({trail.get('name', 'Unknown')}) is a great choice for your profile. "
                                   f"Consider the weather conditions and your fitness level when planning your hike.",
                "key_factors": [
                    f"Trail difficulty: {trail.get('difficulty', 'Unknown')}/10",
                    f"Distance: {trail.get('distance', 'Unknown')} km",
                    f"Elevation gain: {trail.get('elevation_gain', 'Unknown')}m"
                ]
            }
        
        return explanation
    
    def _build_recommendation_prompt(
        self,
        trail: Dict,
        user: Dict,
        profile: Optional[str],
        weather_recommendations: Dict,
        similar_hiker_context: Optional[Dict] = None
    ) -> str:
        """Build enhanced prompt for AI explanation with similar hiker context."""
        profile_names = {
            "elevation_lover": "Elevation Enthusiast",
            "performance_athlete": "Performance Athlete",
            "photographer": "Photographer",
            "explorer": "Explorer",
            "contemplative": "Contemplative Hiker",
            "casual": "Casual Hiker",
            "family": "Family Hiker"
        }
        
        profile_name = profile_names.get(profile, "Hiker") if profile else "Hiker"
        
        prompt = f"""Generate personalized, actionable hiking recommendations for a {profile_name} planning to hike the trail "{trail.get('name', 'Unknown')}".

TRAIL DETAILS:
- Distance: {trail.get('distance', 'Unknown')} km
- Estimated Duration: {trail.get('duration', 'Unknown')} minutes ({trail.get('duration', 0) / 60:.1f} hours)
- Elevation Gain: {trail.get('elevation_gain', 'Unknown')}m
- Difficulty: {trail.get('difficulty', 'Unknown')}/10
- Landscapes: {trail.get('landscapes', 'Unknown')}
- Trail Type: {trail.get('trail_type', 'Unknown')}
- Region: {trail.get('region', 'Unknown')}
- Popularity: {trail.get('popularity', 'Unknown')}/10

USER PROFILE:
- Experience Level: {user.get('experience', 'Unknown')}
- Fitness Level: {user.get('fitness_level', 'Unknown')}
- Profile Type: {profile_name}
"""
        
        # Add similar hiker context if available
        if similar_hiker_context and similar_hiker_context.get("completion_count", 0) > 0:
            prompt += f"\nINSIGHTS FROM SIMILAR {profile_name.upper()}S WHO COMPLETED THIS TRAIL:\n"
            prompt += f"- {similar_hiker_context['completion_count']} {profile_name.lower()}s have completed this trail\n"
            
            if similar_hiker_context.get("average_rating"):
                prompt += f"- Average rating: {similar_hiker_context['average_rating']:.1f}/5.0\n"
            
            if similar_hiker_context.get("average_duration"):
                avg_hours = similar_hiker_context['average_duration'] / 60
                estimated_hours = trail.get('duration', 0) / 60
                prompt += f"- Average completion time: {avg_hours:.1f} hours (estimated: {estimated_hours:.1f} hours)\n"
            
            if similar_hiker_context.get("average_heart_rate"):
                prompt += f"- Average heart rate: {similar_hiker_context['average_heart_rate']:.0f} bpm\n"
            
            if similar_hiker_context.get("average_speed"):
                prompt += f"- Average speed: {similar_hiker_context['average_speed']:.1f} km/h\n"
            
            if similar_hiker_context.get("average_difficulty_rating"):
                trail_diff = trail.get('difficulty', 5.0)
                user_rated_diff = similar_hiker_context['average_difficulty_rating']
                if abs(user_rated_diff - trail_diff) > 0.5:
                    prompt += f"- Similar hikers rated difficulty: {user_rated_diff:.1f}/10 (trail estimate: {trail_diff:.1f}/10)\n"
            
            if similar_hiker_context.get("insights"):
                prompt += "\nKey observations from similar hikers:\n"
                for insight in similar_hiker_context["insights"][:3]:  # Limit to top 3
                    prompt += f"- {insight}\n"
        
        # Weather context
        if weather_recommendations.get("best_days"):
            prompt += f"\nWEATHER: Best conditions expected on {len(weather_recommendations['best_days'])} day(s) in the forecast. "
            if weather_recommendations.get("best_days"):
                best_day = weather_recommendations['best_days'][0]
                prompt += f"Recommended day: {best_day.get('date', 'N/A')} with {best_day.get('condition', 'good')} conditions. "
        
        # Profile-specific focus areas
        prompt += "\n\nFOCUS AREAS FOR THIS PROFILE:\n"
        if profile == "elevation_lover":
            prompt += "- Best times to reach peaks for optimal views\n"
            prompt += "- Steepest sections and elevation challenges\n"
            prompt += "- Rest points and viewpoints along the ascent\n"
            prompt += "- Weather conditions at elevation\n"
        elif profile == "photographer":
            prompt += "- Best photo opportunities and Instagram-worthy viewpoints\n"
            prompt += "- Golden hour timing (sunrise/sunset) for optimal lighting\n"
            prompt += "- Scenic sections and landscape highlights\n"
            prompt += "- Equipment recommendations for photography\n"
        elif profile == "performance_athlete":
            prompt += "- Optimal pacing strategy and heart rate zones\n"
            prompt += "- Training benefits and fitness goals\n"
            prompt += "- Performance benchmarks from similar athletes\n"
            prompt += "- Recovery and nutrition considerations\n"
        elif profile == "explorer":
            prompt += "- Alternative routes and side trails\n"
            prompt += "- Less-traveled sections and hidden gems\n"
            prompt += "- Navigation tips and trail marking quality\n"
            prompt += "- Nearby exploration opportunities\n"
        elif profile == "contemplative":
            prompt += "- Quiet sections for meditation and reflection\n"
            prompt += "- Best times for solitude\n"
            prompt += "- Natural settings ideal for contemplation\n"
            prompt += "- Peaceful viewpoints and rest areas\n"
        elif profile == "casual" or profile == "family":
            prompt += "- Suitable difficulty and pacing for casual hiking\n"
            prompt += "- Family-friendly sections and safety considerations\n"
            prompt += "- Rest stops and snack breaks\n"
            prompt += "- Accessibility and trail conditions\n"
        else:
            prompt += "- General hiking tips and trail highlights\n"
            prompt += "- Safety considerations\n"
            prompt += "- Best times to hike\n"
        
        prompt += "\nINSTRUCTIONS:\n"
        prompt += "1. Provide a BRIEF 1-2 sentence summary tailored to this hiker profile (max 50 words)\n"
        prompt += "2. Include ONLY 3-4 most important, actionable tips as bullet points (one line each, max 80 characters per tip)\n"
        prompt += "3. Reference insights from similar hikers when relevant (if provided above)\n"
        prompt += "4. Be concise, specific, and practical - avoid generic advice\n"
        prompt += "5. Focus on what matters most for this profile type on this specific trail\n"
        prompt += "6. Do NOT repeat information already shown in trail details\n"
        prompt += "7. Format response as: Brief summary paragraph, then bullet points (no sections like MATCHES/MISMATCHES)\n"
        
        return prompt
