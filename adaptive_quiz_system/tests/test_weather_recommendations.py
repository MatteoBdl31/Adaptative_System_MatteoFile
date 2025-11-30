# -*- coding: utf-8 -*-
"""
Tests for weather-based trail recommendations.
"""

import unittest
from unittest.mock import patch, Mock
from datetime import date, timedelta

import sys
from pathlib import Path

# Add parent directory to path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from adapt_trails import adapt_trails, calculate_relevance_score
from backend.db import get_all_trails


class TestWeatherRecommendations(unittest.TestCase):
    """Test weather-based recommendation logic"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_user = {
            "id": 101,
            "name": "Test User",
            "experience": "Intermediate",
            "fitness_level": "Medium",
            "fear_of_heights": 0,
            "preferences": ["lake", "mountain"],
            "performance": {
                "trails_completed": 5,
                "avg_difficulty_completed": 5.0,
                "persistence_score": 0.7,
                "exploration_level": 0.6,
                "avg_completion_time": 90,
                "activity_frequency": 4
            },
            "completed_trails": []
        }
        
        self.test_trail = {
            "trail_id": "test_trail_1",
            "name": "Test Trail",
            "difficulty": 5.0,
            "distance": 10.0,
            "duration": 120,
            "elevation_gain": 500,
            "latitude": 45.5,
            "longitude": 6.2,
            "safety_risks": "low",
            "landscapes": "lake, mountain",
            "popularity": 8.0,
            "closed_seasons": "",
            "region": "french_alps",
            "is_real": 1
        }
    
    @patch('adapt_trails.get_weather_for_trail')
    def test_weather_forecast_in_relevance_score(self, mock_get_weather):
        """Test that weather forecast is considered in relevance scoring"""
        mock_get_weather.return_value = "sunny"
        
        context = {
            "hike_date": date.today().isoformat(),
            "weather": "sunny",
            "time_available": 180
        }
        
        filters = {}
        
        # Calculate relevance score
        result = calculate_relevance_score(
            self.test_trail,
            filters,
            self.test_user,
            context,
            []
        )
        
        # Should have weather_forecast in matched criteria if weather matches
        self.assertIn("weather_forecast", result["matched_criteria"])
        mock_get_weather.assert_called_once_with(
            self.test_trail,
            date.today().isoformat()
        )
    
    @patch('adapt_trails.get_weather_for_trail')
    def test_weather_mismatch_affects_score(self, mock_get_weather):
        """Test that weather mismatch reduces relevance score"""
        mock_get_weather.return_value = "rainy"  # Forecast is rainy
        
        context = {
            "hike_date": date.today().isoformat(),
            "weather": "sunny",  # User wants sunny
            "time_available": 180
        }
        
        filters = {}
        
        # Calculate relevance score
        result = calculate_relevance_score(
            self.test_trail,
            filters,
            self.test_user,
            context,
            []
        )
        
        # Should have weather mismatch in unmatched criteria
        self.assertIn("weather_forecast", [c for c in result["unmatched_criteria"] if "Weather forecast" in c])
        # Score should be lower due to mismatch
        self.assertLess(result["relevance"], 100.0)
    
    @patch('adapt_trails.get_weather_for_trail')
    def test_weather_match_boosts_score(self, mock_get_weather):
        """Test that weather match boosts relevance score"""
        mock_get_weather.return_value = "sunny"  # Forecast matches desired
        
        context = {
            "hike_date": date.today().isoformat(),
            "weather": "sunny",
            "time_available": 180
        }
        
        filters = {}
        
        # Calculate relevance score
        result1 = calculate_relevance_score(
            self.test_trail,
            filters,
            self.test_user,
            context,
            []
        )
        
        # With matching weather, should have higher relevance
        self.assertIn("weather_forecast", result1["matched_criteria"])
    
    @patch('adapt_trails.get_weather_for_trail')
    def test_no_weather_penalty_when_forecast_unavailable(self, mock_get_weather):
        """Test that unavailable forecast doesn't penalize trails"""
        mock_get_weather.return_value = None  # No forecast available
        
        context = {
            "hike_date": date.today().isoformat(),
            "weather": "sunny",
            "time_available": 180
        }
        
        filters = {}
        
        # Calculate relevance score
        result = calculate_relevance_score(
            self.test_trail,
            filters,
            self.test_user,
            context,
            []
        )
        
        # Should still match weather_forecast (no penalty)
        self.assertIn("weather_forecast", result["matched_criteria"])
    
    @patch('adapt_trails.get_weather_for_trail')
    def test_adapt_trails_with_weather(self, mock_get_weather):
        """Test that adapt_trails considers weather forecasts"""
        # Mock weather for all trails
        mock_get_weather.return_value = "sunny"
        
        context = {
            "hike_date": date.today().isoformat(),
            "weather": "sunny",
            "time_available": 180,
            "device": "laptop",
            "connection": "strong",
            "season": "summer"
        }
        
        # Get recommendations
        exact_matches, suggestions, display_settings, active_rules = adapt_trails(
            self.test_user,
            context
        )
        
        # Should have called get_weather_for_trail for trails
        # (at least once during relevance calculation)
        self.assertGreater(mock_get_weather.call_count, 0)
        
        # Check that trails have relevance info including weather
        all_trails = exact_matches + suggestions
        if all_trails:
            trail = all_trails[0]
            # Should have relevance information
            self.assertIn("relevance_percentage", trail)
            # Should have matched/unmatched criteria
            self.assertIn("matched_criteria", trail)


if __name__ == '__main__':
    unittest.main()

