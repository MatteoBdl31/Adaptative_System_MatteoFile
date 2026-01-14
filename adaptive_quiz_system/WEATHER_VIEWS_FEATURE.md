# Weather Information in Trail Views

## Overview
This feature adds real-time weather forecast information to all trail views (map, list, and cards) based on selected dates.

## Implementation Summary

### 1. Backend Changes (`app/__init__.py`)

**Route: `/trails` (all_trails function)**
- Added date parameters (`hike_start_date`, `hike_end_date`) from query string
- Fetches weather forecasts for all trails using the weather service
- Passes weather data and dates to the template

```python
# Fetches weather forecasts for each trail
for trail in trails:
    if trail.get("latitude") and trail.get("longitude"):
        forecast = get_weather_forecast(
            float(trail["latitude"]), 
            float(trail["longitude"]), 
            hike_start_date
        )
        trail["forecast_weather"] = forecast
```

### 2. Template Changes (`templates/all_trails.html`)

#### Date Selection UI
- Added date input fields for hike start and end dates
- Added "Update Weather" button to refresh weather data
- Dates default to today if not specified

#### Weather Display in Cards View
- Shows weather icon and condition in trail stats
- Icons: ☀️ (sunny), ☁️ (cloudy), 🌧️ (rainy), ❄️ (snowy), ⛈️ (storm_risk)
- Displays "N/A" for unavailable weather data
- Includes tooltip showing the forecast date

#### Weather Display in List View
- Same weather information as cards view
- Consistent styling and icons

### 3. JavaScript Changes

#### Map View (`all_trails.html`)
- Added `forecast_weather` field to trail data
- Updated map marker popups to include weather information
- Weather icon and condition appear in popup below elevation info

#### Recommendations Map (`static/recommendations.js`)
- Added weather information to recommendation map popups
- Shows weather icon and condition for each trail marker
- Consistent with other views

#### Weather Update Function
```javascript
function updateWeather() {
    var startDate = document.getElementById('hike-start-date').value;
    var endDate = document.getElementById('hike-end-date').value;
    
    // Reload page with new date parameters
    var url = window.location.pathname + '?hike_start_date=' + startDate;
    if (endDate) url += '&hike_end_date=' + endDate;
    window.location.href = url;
}
```

## User Experience

### All Trails Page (`/trails`)
1. Users can select hike dates using the date pickers
2. Click "Update Weather" to fetch forecasts for selected dates
3. Weather information appears:
   - In **Map View**: Popups show weather when clicking markers
   - In **List View**: Weather badge in trail stats
   - In **Cards View**: Weather badge in trail stats (with mini maps)

### Recommendations Page (`/recommendations/<user_id>`)
- Weather data is automatically fetched based on selected hike dates
- Map markers show weather in popups
- Card grid displays weather badges for each trail
- Weather aligns with user's desired weather preferences

## Weather Icons
- ☀️ **Sunny**: Clear skies
- ☁️ **Cloudy**: Overcast or partly cloudy
- 🌧️ **Rainy**: Rain or drizzle
- ❄️ **Snowy**: Snow conditions
- ⛈️ **Storm Risk**: Thunderstorms
- 🌤️ **N/A**: Weather data unavailable

## Technical Details

### Weather Service Integration
- Uses Open-Meteo API (free, no API key required)
- Supports forecasts up to 16 days ahead
- Gracefully handles API failures (shows "N/A")
- Weather conditions normalized to 5 categories

### Performance
- Weather fetched once per page load
- Cached during single request
- Only fetches for trails with valid coordinates
- Non-blocking errors (continues if weather API fails)

## Testing

To test the feature:
1. Navigate to `/trails`
2. Select a date (today or future date within 16 days)
3. Click "Update Weather"
4. Verify weather appears in:
   - Map popups (click markers)
   - List view (scroll through trails)
   - Cards view (if connection is strong)
5. Try different dates to see forecast changes

## Future Enhancements
- Add multi-day weather forecast for multi-day hikes
- Show weather trends (e.g., "improving", "worsening")
- Filter trails by desired weather conditions
- Weather-based recommendations ranking boost
