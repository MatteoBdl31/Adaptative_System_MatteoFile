# -*- coding: utf-8 -*-
"""Debug script to test weather retrieval"""

import sys
from pathlib import Path
from datetime import date

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.weather_service import get_weather_for_trail, OPENWEATHER_API_KEY
from backend.db import get_all_trails

print("=" * 60)
print("Weather Service Debug")
print("=" * 60)
print(f"API Key Set: {'YES' if OPENWEATHER_API_KEY else 'NO'}")
print(f"API Key Length: {len(OPENWEATHER_API_KEY) if OPENWEATHER_API_KEY else 0}")
print()

# Get a sample trail
trails = get_all_trails()
if not trails:
    print("ERROR: No trails found in database")
    sys.exit(1)

trail = trails[0]
print(f"Testing with trail: {trail.get('name', trail.get('trail_id'))}")
print(f"Trail has latitude: {trail.get('latitude')}")
print(f"Trail has longitude: {trail.get('longitude')}")
print()

# Test weather retrieval
test_date = date.today().isoformat()
print(f"Testing weather for date: {test_date}")
print()

try:
    forecast = get_weather_for_trail(trail, test_date)
    print(f"Weather result: {forecast}")
    print(f"Result type: {type(forecast)}")
    print(f"Is None: {forecast is None}")
except Exception as e:
    print(f"ERROR retrieving weather: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)

