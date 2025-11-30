# -*- coding: utf-8 -*-
"""
Weather service to fetch weather forecasts for trail locations.
Uses Open-Meteo API (free, no API key required).
"""

import requests
from datetime import datetime, date
from typing import Optional, Dict, List


# Open-Meteo API - free, no API key required
OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"


def normalize_weather_condition(weather_code: int) -> str:
    """
    Convert WMO weather code (used by Open-Meteo) to our weather categories.
    
    WMO Weather Code Reference:
    0 = Clear sky
    1, 2, 3 = Mainly clear, partly cloudy, overcast
    45, 48 = Fog and depositing rime fog
    51, 53, 55 = Drizzle: Light, moderate, dense
    56, 57 = Freezing Drizzle: Light, dense
    61, 63, 65 = Rain: Slight, moderate, heavy
    66, 67 = Freezing Rain: Light, heavy
    71, 73, 75 = Snow fall: Slight, moderate, heavy
    77 = Snow grains
    80, 81, 82 = Rain showers: Slight, moderate, violent
    85, 86 = Snow showers: Slight, heavy
    95 = Thunderstorm
    96, 99 = Thunderstorm with hail
    
    Args:
        weather_code: WMO weather condition code (0-99)
    
    Returns:
        One of: "sunny", "cloudy", "rainy", "storm_risk", "snowy"
    """
    # Thunderstorm conditions (95, 96, 99)
    if weather_code in [95, 96, 99]:
        return "storm_risk"
    
    # Snow conditions (71, 73, 75, 77, 85, 86)
    if weather_code in [71, 73, 75, 77, 85, 86]:
        return "snowy"
    
    # Rain conditions (51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82)
    if weather_code in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82]:
        return "rainy"
    
    # Cloudy conditions (1, 2, 3, 45, 48)
    if weather_code in [1, 2, 3, 45, 48]:
        return "cloudy"
    
    # Clear/Sunny conditions (0)
    if weather_code == 0:
        return "sunny"
    
    # Default to cloudy for unknown conditions
    return "cloudy"


def get_weather_forecast(latitude: float, longitude: float, target_date: str) -> Optional[str]:
    """
    Get weather forecast for a specific location and date using Open-Meteo API.
    
    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
        target_date: Target date in ISO format (YYYY-MM-DD)
    
    Returns:
        Weather condition string: "sunny", "cloudy", "rainy", "storm_risk", "snowy"
        Returns None if request fails
    """
    try:
        # Parse target date
        target = datetime.strptime(target_date, "%Y-%m-%d").date()
        today = date.today()
        days_ahead = (target - today).days
        
        # Open-Meteo supports up to 16 days forecast
        if days_ahead < 0 or days_ahead > 16:
            # For dates outside forecast range, return None
            return None
        
        # Open-Meteo API endpoint
        # https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=weather_code&timezone=auto
        url = OPEN_METEO_BASE_URL
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": "weather_code",  # Get daily weather codes
            "timezone": "auto",  # Automatically detect timezone
            "start_date": target_date,  # Start date for forecast
            "end_date": target_date,  # End date (same as start for single day)
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Open-Meteo response structure:
        # {
        #   "daily": {
        #     "time": ["2024-01-01"],
        #     "weather_code": [0]
        #   }
        # }
        daily = data.get("daily", {})
        weather_codes = daily.get("weather_code", [])
        times = daily.get("time", [])
        
        if not weather_codes or not times:
            return None
        
        # Find the index for our target date
        try:
            date_index = times.index(target_date)
            weather_code = weather_codes[date_index]
            return normalize_weather_condition(weather_code)
        except (ValueError, IndexError):
            # Date not found in response, return None
            return None
            
    except requests.HTTPError as e:
        # Handle specific HTTP errors
        if e.response.status_code == 429:
            print("Weather API error: Rate limit exceeded. Please try again later.")
        else:
            print(f"Weather API error: HTTP {e.response.status_code} - {e}")
        return None
    except (requests.RequestException, ValueError, KeyError, IndexError) as e:
        # Log error in production, but return None to allow fallback
        print(f"Weather API error: {e}")
        return None


def get_weather_for_trail(trail: Dict, target_date: str) -> Optional[str]:
    """
    Get weather forecast for a trail location.
    
    Args:
        trail: Trail dictionary with latitude and longitude
        target_date: Target date in ISO format (YYYY-MM-DD)
    
    Returns:
        Weather condition string or None
    """
    lat = trail.get("latitude")
    lon = trail.get("longitude")
    
    if lat is None or lon is None:
        return None
    
    return get_weather_forecast(float(lat), float(lon), target_date)


def weather_matches(desired_weather: str, forecast_weather: Optional[str]) -> bool:
    """
    Check if forecasted weather matches desired weather.
    
    Args:
        desired_weather: User's desired weather condition
        forecast_weather: Forecasted weather condition (None if unavailable)
    
    Returns:
        True if weather matches or forecast is unavailable, False otherwise
    """
    if forecast_weather is None:
        # If no forecast available, assume it matches (don't penalize)
        return True
    
    # Exact match
    if desired_weather == forecast_weather:
        return True
    
    # Some weather conditions are compatible
    # Cloudy is acceptable for sunny (partial match)
    if desired_weather == "sunny" and forecast_weather == "cloudy":
        return True
    
    # Cloudy is acceptable for rainy (less ideal but not a mismatch)
    if desired_weather == "rainy" and forecast_weather == "cloudy":
        return True
    
    return False

