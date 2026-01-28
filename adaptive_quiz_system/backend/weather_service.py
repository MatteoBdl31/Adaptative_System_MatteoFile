# -*- coding: utf-8 -*-
"""
Weather service to fetch weather forecasts for trail locations.
Uses Open-Meteo API (free, no API key required).
"""

import requests
from datetime import datetime, date, timedelta
from typing import Optional, Dict, List


# Open-Meteo API - free, no API key required
OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"

# Timeouts: (connect_sec, read_sec). Read timeouts often occur when we send many
# concurrent requests (e.g. demo enriching 15+ trails); Open-Meteo may rate-limit
# or queue, so the server doesn't send the response within the limit.
WEATHER_REQUEST_TIMEOUT = (4, 10)  # 4s to connect, 10s to receive full response


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
        
        response = requests.get(url, params=params, timeout=WEATHER_REQUEST_TIMEOUT)
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
    except requests.ConnectTimeout as e:
        print(f"Weather API error: Connect timeout (server {OPEN_METEO_BASE_URL} not reachable within {WEATHER_REQUEST_TIMEOUT[0]}s): {e}")
        return None
    except requests.ReadTimeout as e:
        print(f"Weather API error: Read timeout (server took longer than {WEATHER_REQUEST_TIMEOUT[1]}s to respond, often due to rate limiting or load): {e}")
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


def get_weekly_forecast(latitude: float, longitude: float, start_date: Optional[str] = None) -> List[Dict]:
    """
    Get 7-day weather forecast for a location.
    
    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
        start_date: Start date in ISO format (YYYY-MM-DD). If None, uses today.
    
    Returns:
        List of forecast dictionaries:
        [
            {
                "date": "YYYY-MM-DD",
                "weather": "sunny" | "cloudy" | "rainy" | "storm_risk" | "snowy",
                "weather_code": int
            },
            ...
        ]
    """
    try:
        if start_date is None:
            start_date = date.today().isoformat()
        
        # Calculate end date (7 days from start)
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = start + timedelta(days=6)
        end_date = end.isoformat()
        
        # Open-Meteo API endpoint
        url = OPEN_METEO_BASE_URL
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": "weather_code",  # Get daily weather codes
            "timezone": "auto",
            "start_date": start_date,
            "end_date": end_date,
        }
        
        response = requests.get(url, params=params, timeout=WEATHER_REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()

        # Parse response
        daily = data.get("daily", {})
        weather_codes = daily.get("weather_code", [])
        times = daily.get("time", [])
        
        if not weather_codes or not times:
            return []
        
        # Build forecast list
        forecast = []
        for i, date_str in enumerate(times):
            if i < len(weather_codes):
                weather_code = weather_codes[i]
                forecast.append({
                    "date": date_str,
                    "weather": normalize_weather_condition(weather_code),
                    "weather_code": weather_code
                })
        
        return forecast
        
    except requests.HTTPError as e:
        if e.response.status_code == 429:
            print("Weather API error: Rate limit exceeded. Please try again later.")
        else:
            print(f"Weather API error: HTTP {e.response.status_code} - {e}")
        return []
    except requests.ConnectTimeout as e:
        print(f"Weather API error: Connect timeout (server not reachable within {WEATHER_REQUEST_TIMEOUT[0]}s): {e}")
        return []
    except requests.ReadTimeout as e:
        print(f"Weather API error: Read timeout (server took longer than {WEATHER_REQUEST_TIMEOUT[1]}s): {e}")
        return []
    except (requests.RequestException, ValueError, KeyError, IndexError) as e:
        print(f"Weather API error: {e}")
        return []


def get_weather_recommendations(trail: Dict, forecast: List[Dict]) -> Dict:
    """
    Get weather-based recommendations for a trail.
    
    Args:
        trail: Trail dictionary
        forecast: Weekly forecast from get_weekly_forecast()
    
    Returns:
        {
            "best_days": List[Dict],
            "avoid_days": List[Dict],
            "recommendations": List[str]
        }
    """
    if not forecast:
        return {
            "best_days": [],
            "avoid_days": [],
            "recommendations": ["Weather forecast unavailable"]
        }
    
    best_days = []
    avoid_days = []
    recommendations = []
    
    # Categorize days
    for day in forecast:
        weather = day.get("weather", "cloudy")
        if weather in ["sunny", "cloudy"]:
            best_days.append(day)
        elif weather in ["storm_risk", "snowy"]:
            avoid_days.append(day)
    
    # Generate recommendations
    if best_days:
        recommendations.append(f"Best conditions on {len(best_days)} day(s): {', '.join([d['date'] for d in best_days[:3]])}")
    
    if avoid_days:
        recommendations.append(f"Avoid {len(avoid_days)} day(s) with poor conditions: {', '.join([d['date'] for d in avoid_days])}")
    
    # Check for elevation-specific recommendations
    elevation_gain = trail.get("elevation_gain", 0)
    if elevation_gain > 800:
        storm_days = [d for d in forecast if d.get("weather") == "storm_risk"]
        if storm_days:
            recommendations.append("High elevation trail - avoid storm days for safety")
    
    return {
        "best_days": best_days[:3],  # Top 3 best days
        "avoid_days": avoid_days,
        "recommendations": recommendations
    }


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

