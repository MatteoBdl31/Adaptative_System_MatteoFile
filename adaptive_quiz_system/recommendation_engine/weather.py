# -*- coding: utf-8 -*-
"""
Batch weather fetching for trail recommendations.
Efficiently fetches weather forecasts for multiple trails using parallel requests.
"""

from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from backend.weather_service import get_weather_for_trail


class WeatherEnricher:
    """Enriches trails with weather forecast data using parallel fetching."""
    
    def __init__(self, max_workers: int = 10):
        """
        Args:
            max_workers: Maximum number of parallel weather API requests (increased for better performance)
        """
        self._cache = {}  # Simple in-memory cache: {(lat, lon, date): weather}
        self.max_workers = max_workers
    
    def enrich_trails(
        self, 
        trails: List[Dict], 
        hike_date: Optional[str],
        max_trails: Optional[int] = None
    ) -> List[Dict]:
        """
        Enrich trails with weather forecasts using parallel requests.
        
        Args:
            trails: List of trail dictionaries
            hike_date: Hike date in ISO format (YYYY-MM-DD)
            max_trails: Optional limit on number of trails to fetch weather for
        
        Returns:
            List of trails with forecast_weather added
        """
        if not hike_date:
            return trails
        
        # Limit number of trails to fetch weather for (performance optimization)
        trails_to_fetch = trails[:max_trails] if max_trails else trails
        remaining_trails = trails[max_trails:] if max_trails else []
        
        # Prepare trails with cache check
        trails_to_fetch_weather = []
        enriched = []
        
        for trail in trails_to_fetch:
            trail_copy = trail.copy()
            lat = trail.get("latitude")
            lon = trail.get("longitude")
            cache_key = (lat, lon, hike_date) if lat and lon else None
            
            if cache_key and cache_key in self._cache:
                # Use cached value
                trail_copy["forecast_weather"] = self._cache[cache_key]
                enriched.append(trail_copy)
            elif lat and lon:
                # Need to fetch weather
                trails_to_fetch_weather.append((trail_copy, cache_key))
            else:
                trail_copy["forecast_weather"] = None
                enriched.append(trail_copy)
        
        # Fetch weather in parallel for trails that need it
        if trails_to_fetch_weather:
            enriched.extend(self._fetch_weather_parallel(trails_to_fetch_weather, hike_date))
        
        # Add remaining trails without weather (they'll be lower priority anyway)
        for trail in remaining_trails:
            trail_copy = trail.copy()
            trail_copy["forecast_weather"] = None
            enriched.append(trail_copy)
        
        return enriched
    
    def _fetch_weather_parallel(
        self, 
        trails_with_keys: List[tuple], 
        hike_date: str
    ) -> List[Dict]:
        """Fetch weather for multiple trails in parallel."""
        results = {}
        
        def fetch_single(trail_copy, cache_key):
            """Fetch weather for a single trail."""
            try:
                forecast = get_weather_for_trail(trail_copy, hike_date)
                if cache_key:
                    self._cache[cache_key] = forecast
                trail_copy["forecast_weather"] = forecast
                return trail_copy
            except Exception as e:
                # Graceful degradation: continue without weather
                trail_copy["forecast_weather"] = None
                return trail_copy
        
        # Use ThreadPoolExecutor for parallel requests
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_trail = {
                executor.submit(fetch_single, trail_copy, cache_key): trail_copy
                for trail_copy, cache_key in trails_with_keys
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_trail):
                try:
                    result = future.result()
                    results[id(result)] = result
                except Exception as e:
                    trail = future_to_trail[future]
                    trail["forecast_weather"] = None
        
        # Return in original order
        return [results[id(trail_copy)] for trail_copy, _ in trails_with_keys]
    
    def clear_cache(self):
        """Clear the weather cache."""
        self._cache.clear()

