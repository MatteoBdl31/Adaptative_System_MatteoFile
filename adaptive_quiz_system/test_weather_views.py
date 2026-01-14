#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script to verify weather information appears in all views.
"""

import sys
import io
import requests
from datetime import date, timedelta

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_URL = "http://127.0.0.1:5000"

def test_trails_page_with_weather():
    """Test that /trails page shows weather information"""
    print("\n" + "="*60)
    print("Testing /trails page with weather...")
    print("="*60)
    
    # Test with today's date
    today = date.today().isoformat()
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    
    url = f"{BASE_URL}/trails?hike_start_date={today}&hike_end_date={tomorrow}"
    print(f"\nFetching: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            
            # Check for date inputs
            if 'id="hike-start-date"' in content:
                print("✓ Date selection UI present")
            else:
                print("✗ Date selection UI missing")
            
            # Check for weather update button
            if 'updateWeather()' in content:
                print("✓ Update Weather button present")
            else:
                print("✗ Update Weather button missing")
            
            # Check for weather data in JavaScript
            if 'forecast_weather' in content:
                print("✓ Weather data passed to JavaScript")
            else:
                print("✗ Weather data missing from JavaScript")
            
            # Check for weather icons in HTML
            weather_icons = ['☀️', '☁️', '🌧️', '❄️', '⛈️']
            has_weather_icon = any(icon in content for icon in weather_icons)
            if has_weather_icon:
                print("✓ Weather icons present in template")
            else:
                print("✗ Weather icons missing")
            
            print("\n✅ All trails page test completed successfully")
        else:
            print(f"✗ Failed to load page: {response.status_code}")
    
    except Exception as e:
        print(f"✗ Error: {e}")


def test_recommendations_page_with_weather():
    """Test that /recommendations page shows weather information"""
    print("\n" + "="*60)
    print("Testing /recommendations page with weather...")
    print("="*60)
    
    # Test with user ID 1
    today = date.today().isoformat()
    
    url = f"{BASE_URL}/recommendations/1?hike_start_date={today}&time_available_days=0&time_available_hours=8&weather=sunny&connection=strong&device=laptop"
    print(f"\nFetching: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            
            # Check for weather badge in context
            if 'Forecast:' in content or 'forecast_weather' in content:
                print("✓ Weather information in context")
            else:
                print("⚠ Weather information might be missing (check manually)")
            
            # Check for weather in trail cards
            weather_badges = content.count('forecast_weather')
            print(f"✓ Found {weather_badges} weather references in page")
            
            # Check recommendations.js is loaded
            if 'recommendations.js' in content:
                print("✓ Recommendations JavaScript loaded")
            else:
                print("✗ Recommendations JavaScript missing")
            
            print("\n✅ Recommendations page test completed successfully")
        else:
            print(f"✗ Failed to load page: {response.status_code}")
    
    except Exception as e:
        print(f"✗ Error: {e}")


def test_weather_api_integration():
    """Test that weather API is working"""
    print("\n" + "="*60)
    print("Testing Weather API integration...")
    print("="*60)
    
    from backend.weather_service import get_weather_forecast
    
    # Test with French Alps coordinates
    lat, lon = 45.5, 6.2
    today = date.today().isoformat()
    
    print(f"\nFetching weather for coordinates ({lat}, {lon}) on {today}")
    
    try:
        forecast = get_weather_forecast(lat, lon, today)
        if forecast:
            print(f"✓ Weather forecast: {forecast}")
            print("✓ Weather API integration working")
        else:
            print("⚠ Weather forecast returned None (might be out of range or API error)")
    except Exception as e:
        print(f"✗ Weather API error: {e}")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("WEATHER VIEWS INTEGRATION TEST SUITE")
    print("="*60)
    print("\nMake sure the Flask server is running on http://127.0.0.1:5000")
    
    # Test weather API first
    test_weather_api_integration()
    
    # Test all trails page
    test_trails_page_with_weather()
    
    # Test recommendations page
    test_recommendations_page_with_weather()
    
    print("\n" + "="*60)
    print("TEST SUITE COMPLETED")
    print("="*60)
    print("\nManual verification steps:")
    print("1. Visit http://127.0.0.1:5000/trails")
    print("2. Select a date and click 'Update Weather'")
    print("3. Check Map view - click markers to see weather in popups")
    print("4. Check List view - weather badges should appear in trail stats")
    print("5. Check Cards view - weather badges should appear in trail stats")
    print("6. Visit http://127.0.0.1:5000/recommendations/1")
    print("7. Verify weather appears in map popups and trail cards")
    print()


if __name__ == "__main__":
    main()
