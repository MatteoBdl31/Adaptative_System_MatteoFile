# -*- coding: utf-8 -*-
"""
Trail recommendation service for generating profile-specific AI recommendations.
"""

from typing import Dict, List, Optional
from backend.explanation_service import ExplanationService
from backend.weather_service import get_weekly_forecast, get_weather_recommendations
from backend.trail_analytics import TrailAnalytics
from backend.db import get_trail, get_user


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
        
        # Generate AI explanation
        ai_explanation = self._generate_ai_explanation(trail, user, user_profile, weather_recommendations)
        
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
    
    def _generate_ai_explanation(
        self,
        trail: Dict,
        user: Dict,
        profile: Optional[str],
        weather_recommendations: Dict
    ) -> Dict:
        """Generate AI-powered explanation using ExplanationService."""
        # Build prompt
        prompt = self._build_recommendation_prompt(trail, user, profile, weather_recommendations)
        
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
        weather_recommendations: Dict
    ) -> str:
        """Build prompt for AI explanation."""
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
        
        prompt = f"""Generate personalized hiking recommendations for a {profile_name} planning to hike the trail "{trail.get('name', 'Unknown')}".

Trail Details:
- Distance: {trail.get('distance', 'Unknown')} km
- Duration: {trail.get('duration', 'Unknown')} minutes
- Elevation Gain: {trail.get('elevation_gain', 'Unknown')}m
- Difficulty: {trail.get('difficulty', 'Unknown')}/10
- Landscapes: {trail.get('landscapes', 'Unknown')}
- Trail Type: {trail.get('trail_type', 'Unknown')}

User Profile:
- Experience: {user.get('experience', 'Unknown')}
- Fitness Level: {user.get('fitness_level', 'Unknown')}
- Profile Type: {profile_name}

"""
        
        if weather_recommendations.get("best_days"):
            prompt += f"Weather: Best conditions on {len(weather_recommendations['best_days'])} day(s). "
        
        if profile == "elevation_lover":
            prompt += "Focus on: Best times to reach peaks, steepest sections, elevation challenges. "
        elif profile == "photographer":
            prompt += "Focus on: Best photo opportunities, golden hour timing, Instagram-worthy viewpoints. "
        elif profile == "performance_athlete":
            prompt += "Focus on: Optimal pacing, heart rate zones, training benefits. "
        
        prompt += "\nProvide 2-3 sentences of personalized advice and 3-5 specific tips as bullet points."
        
        return prompt
