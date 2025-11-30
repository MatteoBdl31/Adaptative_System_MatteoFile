# -*- coding: utf-8 -*-
"""
Tests for weather service functionality.
"""

import unittest
from unittest.mock import patch, Mock
from datetime import date, datetime, timedelta

import sys
from pathlib import Path

# Add parent directory to path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.weather_service import (
    normalize_weather_condition,
    get_weather_forecast,
    get_weather_for_trail,
    weather_matches
)


class TestWeatherService(unittest.TestCase):
    """Test weather service functions"""
    
    def test_normalize_weather_condition_sunny(self):
        """Test normalization of sunny weather"""
        self.assertEqual(normalize_weather_condition(800, "Clear", "clear sky"), "sunny")
        self.assertEqual(normalize_weather_condition(800, "Clear", "sunny"), "sunny")
    
    def test_normalize_weather_condition_rainy(self):
        """Test normalization of rainy weather"""
        self.assertEqual(normalize_weather_condition(500, "Rain", "light rain"), "rainy")
        self.assertEqual(normalize_weather_condition(300, "Drizzle", "drizzle"), "rainy")
    
    def test_normalize_weather_condition_snowy(self):
        """Test normalization of snowy weather"""
        self.assertEqual(normalize_weather_condition(600, "Snow", "light snow"), "snowy")
    
    def test_normalize_weather_condition_storm(self):
        """Test normalization of storm weather"""
        self.assertEqual(normalize_weather_condition(200, "Thunderstorm", "thunderstorm"), "storm_risk")
        self.assertEqual(normalize_weather_condition(200, "Thunderstorm", "thunderstorm with rain"), "storm_risk")
    
    def test_normalize_weather_condition_cloudy(self):
        """Test normalization of cloudy weather"""
        self.assertEqual(normalize_weather_condition(801, "Clouds", "few clouds"), "cloudy")
        self.assertEqual(normalize_weather_condition(741, "Fog", "fog"), "cloudy")
        self.assertEqual(normalize_weather_condition(701, "Mist", "mist"), "cloudy")
    
    @patch('backend.weather_service.requests.get')
    def test_get_weather_forecast_current_weather(self, mock_get):
        """Test getting current weather (today)"""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "weather": [{
                "id": 800,
                "main": "Clear",
                "description": "clear sky"
            }]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Set API key
        import os
        with patch.dict(os.environ, {'OPENWEATHER_API_KEY': 'test_key'}):
            from backend import weather_service
            weather_service.OPENWEATHER_API_KEY = 'test_key'
            
            today = date.today().isoformat()
            result = get_weather_forecast(45.0, 6.0, today)
            self.assertEqual(result, "sunny")
            mock_get.assert_called_once()
    
    @patch('backend.weather_service.requests.get')
    def test_get_weather_forecast_future_date(self, mock_get):
        """Test getting forecast for future date"""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "list": [
                {
                    "dt": int((datetime.now() + timedelta(days=1)).replace(hour=12).timestamp()),
                    "weather": [{
                        "id": 500,
                        "main": "Rain",
                        "description": "light rain"
                    }]
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Set API key
        import os
        with patch.dict(os.environ, {'OPENWEATHER_API_KEY': 'test_key'}):
            from backend import weather_service
            weather_service.OPENWEATHER_API_KEY = 'test_key'
            
            future_date = (date.today() + timedelta(days=1)).isoformat()
            result = get_weather_forecast(45.0, 6.0, future_date)
            self.assertEqual(result, "rainy")
            mock_get.assert_called_once()
    
    def test_get_weather_forecast_no_api_key(self):
        """Test that forecast returns None when API key is not set"""
        import os
        with patch.dict(os.environ, {}, clear=True):
            from backend import weather_service
            weather_service.OPENWEATHER_API_KEY = ""
            
            result = get_weather_forecast(45.0, 6.0, date.today().isoformat())
            self.assertIsNone(result)
    
    def test_get_weather_for_trail(self):
        """Test getting weather for a trail"""
        trail = {
            "trail_id": "test_trail",
            "latitude": 45.5,
            "longitude": 6.2,
            "name": "Test Trail"
        }
        
        with patch('backend.weather_service.get_weather_forecast') as mock_forecast:
            mock_forecast.return_value = "sunny"
            result = get_weather_for_trail(trail, date.today().isoformat())
            self.assertEqual(result, "sunny")
            mock_forecast.assert_called_once_with(45.5, 6.2, date.today().isoformat())
    
    def test_get_weather_for_trail_no_coordinates(self):
        """Test getting weather for trail without coordinates"""
        trail = {
            "trail_id": "test_trail",
            "name": "Test Trail"
        }
        
        result = get_weather_for_trail(trail, date.today().isoformat())
        self.assertIsNone(result)
    
    def test_weather_matches_exact(self):
        """Test weather matching with exact match"""
        self.assertTrue(weather_matches("sunny", "sunny"))
        self.assertTrue(weather_matches("rainy", "rainy"))
        self.assertTrue(weather_matches("cloudy", "cloudy"))
    
    def test_weather_matches_compatible(self):
        """Test weather matching with compatible conditions"""
        # Cloudy is acceptable for sunny
        self.assertTrue(weather_matches("sunny", "cloudy"))
        # Cloudy is acceptable for rainy
        self.assertTrue(weather_matches("rainy", "cloudy"))
    
    def test_weather_matches_mismatch(self):
        """Test weather matching with mismatched conditions"""
        self.assertFalse(weather_matches("sunny", "rainy"))
        self.assertFalse(weather_matches("sunny", "snowy"))
        self.assertFalse(weather_matches("rainy", "sunny"))
    
    def test_weather_matches_no_forecast(self):
        """Test weather matching when forecast is unavailable"""
        # Should return True (don't penalize if forecast unavailable)
        self.assertTrue(weather_matches("sunny", None))
        self.assertTrue(weather_matches("rainy", None))


if __name__ == '__main__':
    unittest.main()

