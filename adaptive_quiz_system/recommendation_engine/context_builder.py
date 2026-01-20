# -*- coding: utf-8 -*-
"""
Context builder for explanation generation.
Extensible design for preparing context data for OpenAI prompts.
"""

from typing import Dict, List, Optional
from backend.user_profiling import UserProfiler


class ContextBuilder:
    """Builds context data for explanation generation with extensible design."""
    
    def __init__(self):
        self.profiler = UserProfiler()
    
    def build_general_context(
        self,
        user: Dict,
        context: Dict,
        exact_matches: List[Dict],
        suggestions: List[Dict],
        active_rules: List[Dict]
    ) -> Dict:
        """
        Build context for general explanation (all recommendations).
        
        Args:
            user: User profile dictionary
            context: Search context dictionary
            exact_matches: List of exact match trails
            suggestions: List of suggestion trails
            active_rules: List of active matching rules
        
        Returns:
            Dictionary with all context data
        """
        context_dict = {}
        
        # Add each context component using extensible pattern
        self._add_user_profile(context_dict, user)
        self._add_search_context(context_dict, context)
        self._add_trail_summary(context_dict, exact_matches, suggestions)
        self._add_matching_rules(context_dict, active_rules)
        
        return context_dict
    
    def build_trail_context(
        self,
        trail: Dict,
        user: Dict,
        context: Dict,
        matched_criteria: List[Dict],
        unmatched_criteria: List[Dict]
    ) -> Dict:
        """
        Build context for per-trail explanation.
        
        Args:
            trail: Trail dictionary
            user: User profile dictionary
            context: Search context dictionary
            matched_criteria: List of matched criteria
            unmatched_criteria: List of unmatched criteria
        
        Returns:
            Dictionary with all context data
        """
        context_dict = {}
        
        # Add each context component
        self._add_user_profile(context_dict, user)
        self._add_search_context(context_dict, context)
        self._add_trail_details(context_dict, trail)
        self._add_criteria_analysis(context_dict, matched_criteria, unmatched_criteria)
        
        return context_dict
    
    def _add_user_profile(self, context_dict: Dict, user: Dict) -> None:
        """Add user profile information to context."""
        profile_name = None
        if user.get("detected_profile"):
            profile_name = self.profiler.PROFILE_NAMES.get(
                user["detected_profile"],
                user["detected_profile"]
            )
        
        context_dict["user"] = {
            "name": user.get("name", "User"),
            "experience": user.get("experience", "Unknown"),
            "fitness_level": user.get("fitness_level", "Unknown"),
            "detected_profile": profile_name,
            "preferences": user.get("preferences", []),
            "fear_of_heights": user.get("fear_of_heights", 0),
            "health_constraints": user.get("health_constraints"),
            "trails_completed": len(user.get("completed_trails", []))
        }
    
    def _add_search_context(self, context_dict: Dict, context: Dict) -> None:
        """Add search context parameters."""
        # Format time available
        time_available = context.get("time_available", 0)
        days = time_available // (24 * 60)
        hours = (time_available % (24 * 60)) // 60
        
        time_str = ""
        if days > 0:
            time_str = f"{days} day{'s' if days != 1 else ''}"
        if hours > 0:
            if days > 0:
                time_str += f" and {hours} hour{'s' if hours != 1 else ''}"
            else:
                time_str = f"{hours} hour{'s' if hours != 1 else ''}"
        
        context_dict["search_context"] = {
            "time_available": time_str or "Not specified",
            "device": context.get("device", "Unknown"),
            "weather": context.get("weather", "Unknown"),
            "season": context.get("season", "Unknown"),
            "connection": context.get("connection", "Unknown"),
            "hike_date": context.get("hike_start_date") or context.get("hike_date")
        }
    
    def _add_trail_summary(
        self,
        context_dict: Dict,
        exact_matches: List[Dict],
        suggestions: List[Dict]
    ) -> None:
        """Add summary statistics about recommended trails."""
        all_trails = exact_matches + suggestions
        
        if not all_trails:
            context_dict["trail_summary"] = {
                "total_count": 0,
                "exact_matches_count": 0,
                "suggestions_count": 0
            }
            return
        
        # Calculate statistics
        difficulties = [t.get("difficulty", 0) for t in all_trails if t.get("difficulty")]
        distances = [t.get("distance", 0) for t in all_trails if t.get("distance")]
        durations = [t.get("duration", 0) for t in all_trails if t.get("duration")]
        elevations = [t.get("elevation_gain", 0) for t in all_trails if t.get("elevation_gain")]
        
        # Collect landscapes
        all_landscapes = []
        for trail in all_trails:
            landscapes = trail.get("landscapes", "")
            if landscapes:
                all_landscapes.extend([l.strip() for l in landscapes.split(",")])
        
        context_dict["trail_summary"] = {
            "total_count": len(all_trails),
            "exact_matches_count": len(exact_matches),
            "suggestions_count": len(suggestions),
            "avg_difficulty": sum(difficulties) / len(difficulties) if difficulties else 0,
            "avg_distance": sum(distances) / len(distances) if distances else 0,
            "avg_duration": sum(durations) / len(durations) if durations else 0,
            "avg_elevation": sum(elevations) / len(elevations) if elevations else 0,
            "common_landscapes": list(set(all_landscapes))[:5]  # Top 5 unique landscapes
        }
    
    def _add_matching_rules(self, context_dict: Dict, active_rules: List[Dict]) -> None:
        """Add active matching rules."""
        context_dict["matching_rules"] = [
            {
                "description": rule.get("description", ""),
                "condition": rule.get("condition", "")
            }
            for rule in active_rules
        ]
    
    def _add_trail_details(self, context_dict: Dict, trail: Dict) -> None:
        """Add specific trail details."""
        landscapes = []
        if trail.get("landscapes"):
            landscapes = [l.strip() for l in trail["landscapes"].split(",")]
        
        context_dict["trail_details"] = {
            "name": trail.get("name", "Unknown Trail"),
            "difficulty": trail.get("difficulty", 0),
            "distance": trail.get("distance", 0),
            "duration": trail.get("duration", 0),
            "elevation_gain": trail.get("elevation_gain", 0),
            "landscapes": landscapes,
            "trail_type": trail.get("trail_type", "Unknown"),
            "safety_risks": trail.get("safety_risks", "none"),
            "forecast_weather": trail.get("forecast_weather"),
            "relevance_percentage": trail.get("relevance_percentage", 0),
            "popularity": trail.get("popularity", 0)
        }
    
    def _add_criteria_analysis(
        self,
        context_dict: Dict,
        matched_criteria: List[Dict],
        unmatched_criteria: List[Dict]
    ) -> None:
        """Add criteria matching analysis."""
        context_dict["criteria"] = {
            "matched": [
                {
                    "name": c.get("name", ""),
                    "message": c.get("message", "")
                }
                for c in matched_criteria
            ],
            "unmatched": [
                {
                    "name": c.get("name", ""),
                    "message": c.get("message", "")
                }
                for c in unmatched_criteria
            ]
        }
    
    def build_prompt(self, context_dict: Dict, explanation_type: str = "general") -> str:
        """
        Build prompt string from context dictionary.
        
        Args:
            context_dict: Context dictionary from build_*_context methods
            explanation_type: "general" or "trail"
        
        Returns:
            Formatted prompt string
        """
        if explanation_type == "general":
            return self._build_general_prompt(context_dict)
        else:
            return self._build_trail_prompt(context_dict)
    
    def _build_general_prompt(self, context_dict: Dict) -> str:
        """Build prompt for general explanation."""
        user = context_dict.get("user", {})
        search = context_dict.get("search_context", {})
        summary = context_dict.get("trail_summary", {})
        rules = context_dict.get("matching_rules", [])
        
        prompt = f"""Generate a personalized explanation for trail recommendations.

User Profile:
- Name: {user.get('name', 'User')}
- Experience: {user.get('experience', 'Unknown')}
- Fitness Level: {user.get('fitness_level', 'Unknown')}
- Detected Profile: {user.get('detected_profile', 'Not detected')}
- Preferences: {', '.join(user.get('preferences', [])) or 'None'}
- Trails Completed: {user.get('trails_completed', 0)}

Search Context:
- Time Available: {search.get('time_available', 'Not specified')}
- Device: {search.get('device', 'Unknown')}
- Desired Weather: {search.get('weather', 'Unknown')}
- Season: {search.get('season', 'Unknown')}
- Hike Date: {search.get('hike_date', 'Not specified')}

Trail Summary:
- Total Recommendations: {summary.get('total_count', 0)} ({summary.get('exact_matches_count', 0)} exact matches, {summary.get('suggestions_count', 0)} suggestions)
- Average Difficulty: {summary.get('avg_difficulty', 0):.1f}/10
- Average Distance: {summary.get('avg_distance', 0):.1f} km
- Average Duration: {summary.get('avg_duration', 0):.0f} minutes
- Average Elevation Gain: {summary.get('avg_elevation', 0):.0f} m
- Common Landscapes: {', '.join(summary.get('common_landscapes', [])) or 'Various'}

Active Matching Rules:
{chr(10).join([f"- {r.get('description', r.get('condition', ''))}" for r in rules[:5]])}

Generate a brief, friendly explanation (2-3 sentences) explaining why these trails were recommended for this user, and provide 3-5 key matching factors as bullet points."""
        
        return prompt
    
    def _build_trail_prompt(self, context_dict: Dict) -> str:
        """Build prompt for per-trail explanation."""
        user = context_dict.get("user", {})
        search = context_dict.get("search_context", {})
        trail = context_dict.get("trail_details", {})
        criteria = context_dict.get("criteria", {})
        
        matched = criteria.get("matched", [])
        unmatched = criteria.get("unmatched", [])
        
        prompt = f"""Generate a personalized explanation for why a specific trail was recommended.

User Profile:
- Name: {user.get('name', 'User')}
- Experience: {user.get('experience', 'Unknown')}
- Fitness Level: {user.get('fitness_level', 'Unknown')}
- Detected Profile: {user.get('detected_profile', 'Not detected')}
- Preferences: {', '.join(user.get('preferences', [])) or 'None'}

Search Context:
- Time Available: {search.get('time_available', 'Not specified')}
- Desired Weather: {search.get('weather', 'Unknown')}
- Season: {search.get('season', 'Unknown')}

Trail Details:
- Name: {trail.get('name', 'Unknown Trail')}
- Difficulty: {trail.get('difficulty', 0):.1f}/10
- Distance: {trail.get('distance', 0):.1f} km
- Duration: {trail.get('duration', 0):.0f} minutes ({trail.get('duration', 0) / 60:.1f} hours)
- Elevation Gain: {trail.get('elevation_gain', 0):.0f} m
- Landscapes: {', '.join(trail.get('landscapes', [])) or 'Various'}
- Trail Type: {trail.get('trail_type', 'Unknown')}
- Forecast Weather: {trail.get('forecast_weather', 'Not available')}
- Relevance: {trail.get('relevance_percentage', 0):.0f}%

Matched Criteria (what fits):
{chr(10).join([f"- {c.get('message', c.get('name', ''))}" for c in matched[:5]]) if matched else 'None'}

Unmatched Criteria (what doesn't fit):
{chr(10).join([f"- {c.get('message', c.get('name', ''))}" for c in unmatched[:5]]) if unmatched else 'None'}

IMPORTANT: Generate a brief, friendly explanation (2-3 sentences) that:
1. Explains why this trail was recommended (mention what fits)
2. Also mentions what aspects don't perfectly match the user's profile (be honest about mismatches)
3. Provides 3-5 key factors as bullet points, including both matches and important mismatches

Be transparent and helpful - if the trail is too long/difficult for a beginner, mention that. If the weather doesn't match, mention that too."""
        
        return prompt
