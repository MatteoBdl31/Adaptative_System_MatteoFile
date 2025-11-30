# Weather-Based Trail Recommendations Feature

## Overview

This feature adds weather-based trail recommendations by:
1. Allowing users to select a hike date
2. Retrieving weather forecasts for trail locations
3. Comparing desired weather with forecasted weather
4. Adjusting trail recommendations based on weather matches

## Implementation Details

### 1. Date Input

- **Location**: `templates/index.html` and `templates/demo.html`
- **Behavior**:
  - Single day (today): Shows "Hours Available" input
  - Multi-day: Shows "Days Available" input, hides hours
  - JavaScript automatically toggles based on selected date

### 2. Weather Service

- **File**: `backend/weather_service.py`
- **API**: Uses OpenWeatherMap API (free tier)
- **Features**:
  - Fetches current weather for today
  - Fetches forecast for dates up to 5 days ahead
  - Normalizes weather conditions to: `sunny`, `cloudy`, `rainy`, `storm_risk`, `snowy`
  - Falls back gracefully if API key is not set

### 3. Weather Matching Logic

- **Exact matches**: Desired weather matches forecast exactly
- **Compatible matches**: 
  - Cloudy is acceptable for sunny
  - Cloudy is acceptable for rainy
- **No penalty**: If forecast unavailable, no penalty is applied

### 4. Recommendation Impact

- Weather forecast matching is included in relevance scoring
- Trails with matching weather get higher relevance scores
- Trails with mismatched weather get lower scores
- Weather information appears in matched/unmatched criteria

## Setup

### Environment Variable

To enable actual weather API calls, set the OpenWeatherMap API key:

```bash
export OPENWEATHER_API_KEY=your_api_key_here
```

Or on Windows:
```powershell
$env:OPENWEATHER_API_KEY="your_api_key_here"
```

**Note**: The system works without an API key - it will use the user's desired weather as a fallback.

### Getting an API Key

1. Sign up at https://openweathermap.org/api
2. Free tier includes:
   - Current weather
   - 5-day forecast
   - 60 calls/minute limit

## Testing

### Run Integration Tests

```bash
cd adaptive_quiz_system
python test_weather_integration.py
```

### Run Unit Tests

```bash
cd adaptive_quiz_system
python -m unittest tests.test_weather_service
python -m unittest tests.test_weather_recommendations
```

## Usage

1. **Select Hike Date**: Choose the date for your hike
2. **Select Desired Weather**: Choose the weather condition you want
3. **Get Recommendations**: The system will:
   - Fetch weather forecasts for each trail location
   - Compare with your desired weather
   - Rank trails by weather match (among other factors)

## Files Modified

- `templates/index.html` - Added date input with conditional hours/days
- `templates/demo.html` - Added date input with JavaScript logic
- `app/__init__.py` - Updated routes to handle date parameters
- `adapt_trails.py` - Added weather forecast comparison in relevance scoring
- `backend/weather_service.py` - New weather service module
- `tests/test_weather_service.py` - Weather service unit tests
- `tests/test_weather_recommendations.py` - Recommendation impact tests

## API Integration

The weather service uses OpenWeatherMap's free tier:
- **Current Weather**: `GET /weather`
- **Forecast**: `GET /forecast` (5-day forecast)

Weather conditions are normalized to match the system's weather categories.

## Future Enhancements

- Support for multi-day weather forecasts (check weather for each day)
- Weather-based filtering (strictly filter out mismatched trails)
- Caching weather data to reduce API calls
- Support for other weather APIs as alternatives

