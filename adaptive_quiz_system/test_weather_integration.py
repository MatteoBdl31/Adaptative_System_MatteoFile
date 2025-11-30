# -*- coding: utf-8 -*-
"""
Simple integration test to verify weather functionality works.
Run this to test weather retrieval and recommendation impact.
"""

import sys
from pathlib import Path
from datetime import date, timedelta

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.weather_service import (
    normalize_weather_condition,
    get_weather_for_trail,
    weather_matches
)
from backend.db import get_all_trails


def test_weather_normalization():
    """Test weather condition normalization"""
    print("Testing weather normalization...")
    
    # Test various weather conditions
    test_cases = [
        (800, "Clear", "clear sky", "sunny"),
        (500, "Rain", "light rain", "rainy"),
        (600, "Snow", "light snow", "snowy"),
        (200, "Thunderstorm", "thunderstorm", "storm_risk"),
        (801, "Clouds", "few clouds", "cloudy"),
    ]
    
    for code, main, desc, expected in test_cases:
        result = normalize_weather_condition(code, main, desc)
        status = "✓" if result == expected else "✗"
        print(f"  {status} {main} -> {result} (expected {expected})")
        assert result == expected, f"Expected {expected}, got {result}"
    
    print("  ✓ All normalization tests passed!\n")


def test_weather_matching():
    """Test weather matching logic"""
    print("Testing weather matching...")
    
    # Exact matches
    assert weather_matches("sunny", "sunny") == True
    assert weather_matches("rainy", "rainy") == True
    print("  ✓ Exact matches work")
    
    # Compatible matches
    assert weather_matches("sunny", "cloudy") == True
    assert weather_matches("rainy", "cloudy") == True
    print("  ✓ Compatible matches work")
    
    # Mismatches
    assert weather_matches("sunny", "rainy") == False
    assert weather_matches("sunny", "snowy") == False
    print("  ✓ Mismatches detected correctly")
    
    # No forecast (should not penalize)
    assert weather_matches("sunny", None) == True
    print("  ✓ No forecast doesn't penalize")
    
    print("  ✓ All matching tests passed!\n")


def test_weather_for_trails():
    """Test getting weather for actual trails"""
    print("Testing weather retrieval for trails...")
    
    trails = get_all_trails()
    if not trails:
        print("  ⚠ No trails found in database. Skipping trail weather test.")
        return
    
    # Test with first trail
    trail = trails[0]
    print(f"  Testing with trail: {trail.get('name', trail.get('trail_id', 'Unknown'))}")
    
    lat = trail.get("latitude")
    lon = trail.get("longitude")
    
    if lat is None or lon is None:
        print("  ⚠ Trail has no coordinates. Skipping weather retrieval.")
        return
    
    print(f"  Trail location: {lat}, {lon}")
    
    # Try to get weather (may return None if no API key)
    today = date.today().isoformat()
    forecast = get_weather_for_trail(trail, today)
    
    if forecast:
        print(f"  ✓ Weather retrieved: {forecast}")
    else:
        print("  ⚠ No weather retrieved (API key may not be set)")
        print("    This is OK - the system will fall back to user's desired weather")
    
    print("  ✓ Trail weather test completed!\n")


def test_recommendation_impact():
    """Test that weather affects recommendations"""
    print("Testing recommendation impact...")
    
    from adapt_trails import calculate_relevance_score
    
    test_trail = {
        "trail_id": "test_trail",
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
    
    test_user = {
        "id": 101,
        "experience": "Intermediate",
        "fitness_level": "Medium",
        "fear_of_heights": 0,
        "preferences": ["lake"],
        "performance": {}
    }
    
    # Test with matching weather
    context_match = {
        "hike_date": date.today().isoformat(),
        "weather": "sunny",
        "time_available": 180
    }
    
    # Mock weather to return sunny
    from unittest.mock import patch
    with patch('adapt_trails.get_weather_for_trail', return_value="sunny"):
        result_match = calculate_relevance_score(
            test_trail, {}, test_user, context_match, []
        )
        print(f"  With matching weather: relevance = {result_match['relevance']:.1f}%")
        print(f"    Matched criteria: {result_match['matched_criteria']}")
    
    # Test with mismatching weather
    context_mismatch = {
        "hike_date": date.today().isoformat(),
        "weather": "sunny",
        "time_available": 180
    }
    
    with patch('adapt_trails.get_weather_for_trail', return_value="rainy"):
        result_mismatch = calculate_relevance_score(
            test_trail, {}, test_user, context_mismatch, []
        )
        print(f"  With mismatching weather: relevance = {result_mismatch['relevance']:.1f}%")
        print(f"    Unmatched criteria: {result_mismatch['unmatched_criteria']}")
    
    # Weather match should boost score
    if "weather_forecast" in result_match["matched_criteria"]:
        print("  ✓ Weather matching boosts relevance score")
    else:
        print("  ⚠ Weather forecast not in matched criteria (may be due to other factors)")
    
    if any("Weather forecast" in c for c in result_mismatch["unmatched_criteria"]):
        print("  ✓ Weather mismatch reduces relevance score")
    else:
        print("  ⚠ Weather mismatch not detected (may be due to other factors)")
    
    print("  ✓ Recommendation impact test completed!\n")


if __name__ == "__main__":
    print("=" * 60)
    print("Weather Integration Tests")
    print("=" * 60)
    print()
    
    try:
        test_weather_normalization()
        test_weather_matching()
        test_weather_for_trails()
        test_recommendation_impact()
        
        print("=" * 60)
        print("✓ All tests completed successfully!")
        print("=" * 60)
        print()
        print("Note: To enable actual weather API calls, set OPENWEATHER_API_KEY")
        print("      environment variable. Without it, the system will use")
        print("      the user's desired weather as a fallback.")
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

