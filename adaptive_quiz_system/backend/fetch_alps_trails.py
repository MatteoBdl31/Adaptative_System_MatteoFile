# -*- coding: utf-8 -*-
"""
Script to fetch real hiking trails from French Alps
Supports both TrailHUB.org API and OpenStreetMap Overpass API
"""

import requests  # type: ignore
import json
import sqlite3
import os
import math
import re
from datetime import datetime

try:
    import shapefile  # type: ignore
    SHAPEFILE_AVAILABLE = True
except ImportError:
    SHAPEFILE_AVAILABLE = False

BASE_DIR = os.path.dirname(__file__)
TRAILS_DB = os.path.join(BASE_DIR, "trails.db")
# Path to local Shapefile (if downloaded)
SHAPEFILE_PATH = os.path.join(os.path.dirname(BASE_DIR), "hiking_foot_routes_lineLine.shp")
TRAILHUB_API = "https://trailhub.org/api/trails"
# French government open data portal for hiking trails
# Dataset page: https://www.data.gouv.fr/datasets/itineraires-de-randonnee-dans-openstreetmap/
# We need to get the actual resource URL from the dataset API
DATAGOUV_DATASET_ID = "itineraires-de-randonnee-dans-openstreetmap"
DATAGOUV_API = "https://www.data.gouv.fr/api/1/datasets"
# Try alternative Overpass servers if one times out
OVERPASS_API = "https://overpass-api.de/api/interpreter"
# Alternative servers:
# "https://overpass.kumi.systems/api/interpreter"
# "https://overpass.openstreetmap.fr/api/interpreter"

def fetch_trails_from_shapefile(shapefile_path=None, limit=20, bbox=None):
    """
    Fetch hiking trails from a local Shapefile
    Source: https://www.data.gouv.fr/datasets/itineraires-de-randonnee-dans-openstreetmap/
    
    Args:
        shapefile_path: Path to the .shp file (if None, uses default path)
        limit: Maximum number of trails to fetch
        bbox: Optional bounding box as (min_lon, min_lat, max_lon, max_lat) to filter trails
    """
    if not SHAPEFILE_AVAILABLE:
        print("pyshp library not installed. Install with: pip install pyshp")
        return []
    
    try:
        if shapefile_path is None:
            shapefile_path = SHAPEFILE_PATH
        
        if not os.path.exists(shapefile_path):
            print(f"Shapefile not found at {shapefile_path}")
            return []
        
        print(f"Reading trails from Shapefile: {shapefile_path}")
        
        # Open the Shapefile with encoding handling
        try:
            sf = shapefile.Reader(shapefile_path, encoding='latin1')
        except:
            sf = shapefile.Reader(shapefile_path, encoding='utf-8')
        shapes = sf.shapes()
        records = sf.records()
        fields = [f[0] for f in sf.fields[1:]]  # Skip deletion flag field
        
        print(f"Found {len(shapes)} trail features in Shapefile")
        
        # Helper function to convert EPSG:3857 (Web Mercator) to WGS84
        def mercator_to_wgs84(x, y):
            """Convert Web Mercator (EPSG:3857) to WGS84"""
            lon = x / 20037508.34 * 180.0
            lat = y / 20037508.34 * 180.0
            lat = 180.0 / math.pi * (2 * math.atan(math.exp(lat * math.pi / 180.0)) - math.pi / 2.0)
            return [lon, lat]
        
        trails = []
        checked = 0
        
        for i, (shape, record) in enumerate(zip(shapes, records)):
            try:
                if len(trails) >= limit:
                    break
                
                checked += 1
                if checked % 1000 == 0:
                    print(f"Processed {checked} features, found {len(trails)} trails so far...")
                
                # Create a dict from record fields
                props = dict(zip(fields, record))
                
                # Filter for hiking/foot routes
                route_type = props.get('route', '')
                if route_type not in ['hiking', 'foot']:
                    continue
                
                # Extract coordinates from shape (Polyline)
                if shape.shapeType != 3:  # 3 = Polyline
                    continue
                
                # Convert coordinates from EPSG:3857 to WGS84
                coordinates = []
                for part in shape.parts:
                    part_coords = shape.points[part:part + (shape.parts[shape.parts.index(part) + 1] if shape.parts.index(part) + 1 < len(shape.parts) else len(shape.points))]
                    for point in part_coords:
                        lon, lat = mercator_to_wgs84(point[0], point[1])
                        coordinates.append([lon, lat])
                
                if not coordinates or len(coordinates) < 2:
                    continue
                
                # Filter by bounding box if provided
                if bbox:
                    min_lon, min_lat, max_lon, max_lat = bbox
                    trail_in_bbox = False
                    for coord in coordinates:
                        lon, lat = coord[0], coord[1]
                        if min_lon <= lon <= max_lon and min_lat <= lat <= max_lat:
                            trail_in_bbox = True
                            break
                    if not trail_in_bbox:
                        continue
                
                # Calculate center point
                center_lat = sum(coord[1] for coord in coordinates) / len(coordinates)
                center_lon = sum(coord[0] for coord in coordinates) / len(coordinates)
                
                # Extract trail information - ensure name is never empty
                # Try multiple name fields in order of preference
                name = (props.get('name', '') or 
                       props.get('short_name', '') or 
                       props.get('ref', ''))
                
                # If still no name, create a descriptive name from available fields
                if not name or name.strip() == '':
                    name_parts = []
                    # Use location-based name if available
                    if props.get('from') and props.get('to'):
                        name = f"Trail: {props.get('from')} to {props.get('to')}"
                    elif props.get('from'):
                        name = f"Trail from {props.get('from')}"
                    elif props.get('to'):
                        name = f"Trail to {props.get('to')}"
                    # Use network and colour if available
                    elif props.get('network') and props.get('colour'):
                        name = f"{props.get('network', '').upper()} {props.get('colour', '').title()} Trail"
                    elif props.get('network'):
                        # Include approximate location in name
                        location_hint = f"near {center_lat:.2f}°N, {center_lon:.2f}°E"
                        name = f"{props.get('network', '').upper()} Trail {location_hint}"
                    else:
                        # Fallback: use location coordinates
                        name = f"Hiking Trail ({center_lat:.3f}°N, {center_lon:.3f}°E)"
                
                # Build description from multiple sources
                description_parts = []
                if props.get('descriptio'):
                    description_parts.append(props.get('descriptio'))
                if props.get('note'):
                    description_parts.append(props.get('note'))
                if props.get('network'):
                    description_parts.append(f"Part of {props.get('network')} network")
                if props.get('operator'):
                    description_parts.append(f"Operated by {props.get('operator')}")
                
                description = ' '.join(description_parts) if description_parts else f"Hiking trail in French Alps: {name}"
                
                # Extract distance - calculate from coordinates if not provided
                distance = None
                distance_str = props.get('distance', '')
                if distance_str:
                    try:
                        # Try to parse distance string (might be "5 km", "5000 m", "5.2", etc.)
                        # Remove units and extract number
                        distance_match = re.search(r'([\d.]+)', str(distance_str))
                        if distance_match:
                            distance = float(distance_match.group(1))
                            # Check for units
                            distance_str_lower = str(distance_str).lower()
                            if 'km' in distance_str_lower or 'kilometer' in distance_str_lower:
                                # Already in km
                                pass
                            elif 'm' in distance_str_lower and 'km' not in distance_str_lower:
                                # In meters, convert to km
                                distance = distance / 1000.0
                            elif distance > 1000:
                                # Large number, assume meters
                                distance = distance / 1000.0
                    except (ValueError, TypeError):
                        distance = None
                
                # Calculate distance from coordinates if not provided
                if distance is None or distance == 0:
                    # Calculate approximate distance using Haversine formula
                    total_distance = 0.0
                    for j in range(len(coordinates) - 1):
                        lat1, lon1 = coordinates[j][1], coordinates[j][0]
                        lat2, lon2 = coordinates[j+1][1], coordinates[j+1][0]
                        # Haversine formula
                        R = 6371  # Earth radius in km
                        dlat = math.radians(lat2 - lat1)
                        dlon = math.radians(lon2 - lon1)
                        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
                        c = 2 * math.asin(math.sqrt(a))
                        total_distance += R * c
                    if total_distance > 0:
                        distance = round(total_distance, 2)
                
                # Extract difficulty
                difficulty_str = props.get('sac_scale', props.get('difficulty', 'moderate'))
                difficulty = _parse_difficulty(difficulty_str)
                
                # Extract duration - parse ISO 8601 format (PT2H30M) or other formats
                duration = None
                duration_str = props.get('duration', '')
                if duration_str:
                    try:
                        # Try ISO 8601 format (PT2H30M, PT1H, PT30M, etc.)
                        if str(duration_str).startswith('PT'):
                            hours = 0
                            minutes = 0
                            hours_match = re.search(r'(\d+)H', str(duration_str))
                            minutes_match = re.search(r'(\d+)M', str(duration_str))
                            if hours_match:
                                hours = int(hours_match.group(1))
                            if minutes_match:
                                minutes = int(minutes_match.group(1))
                            duration = hours * 60 + minutes
                        else:
                            # Try to parse as number (assume minutes)
                            duration = int(float(duration_str))
                    except (ValueError, TypeError):
                        duration = None
                
                # Estimate duration from distance if not provided
                if duration is None or duration == 0:
                    duration = _estimate_duration(str(distance * 1000) if distance else None)
                
                # Determine trail type
                trail_type = 'loop' if props.get('roundtrip') == 'yes' or props.get('type') == 'circular' else 'one_way'
                
                # Extract landscapes - use network/colour from shapefile if available
                landscapes = _parse_landscapes(props)
                # Enhance with shapefile-specific fields
                if props.get('network'):
                    # network field might indicate trail network type
                    network = props.get('network', '').lower()
                    if 'lwn' in network or 'local' in network:
                        if 'alpine' not in landscapes.lower():
                            landscapes = landscapes + ',alpine' if landscapes else 'alpine'
                if props.get('colour'):
                    # Colour might indicate trail marking
                    colour = props.get('colour', '').lower()
                    if 'blue' in colour or 'yellow' in colour or 'red' in colour:
                        # Marked trails often indicate alpine/mountain areas
                        if 'alpine' not in landscapes.lower():
                            landscapes = landscapes + ',alpine' if landscapes else 'alpine'
                
                # Extract safety risks
                safety_risks = _parse_safety(props)
                
                # Extract accessibility
                accessibility = _parse_accessibility(props)
                
                # Create GeoJSON LineString for storage
                geojson_storage = {
                    "type": "LineString",
                    "coordinates": coordinates
                }
                
                trail = {
                    'trail_id': f"shapefile_{props.get('osm_id', i)}",
                    'name': name,
                    'latitude': center_lat,
                    'longitude': center_lon,
                    'coordinates': json.dumps(geojson_storage),
                    'description': description,
                    'distance': distance,
                    'difficulty': difficulty,
                    'duration': duration,
                    'elevation_gain': None,  # Not in Shapefile
                    'trail_type': trail_type,
                    'landscapes': landscapes,
                    'popularity': 7.0,
                    'safety_risks': safety_risks,
                    'accessibility': accessibility,
                    'closed_seasons': '',
                }
                
                trails.append(trail)
                
            except Exception as e:
                print(f"Error parsing trail {i}: {e}")
                continue
        
        print(f"Parsed {len(trails)} hiking trails from Shapefile")
        return trails
        
    except Exception as e:
        print(f"Error reading Shapefile: {e}")
        return []

def fetch_trails_from_datagouv(limit=20, bbox=None):
    """
    Fetch hiking trails from French government open data portal (data.gouv.fr)
    Source: https://www.data.gouv.fr/datasets/itineraires-de-randonnee-dans-openstreetmap/
    
    Args:
        limit: Maximum number of trails to fetch
        bbox: Optional bounding box as (min_lon, min_lat, max_lon, max_lat) to filter trails
    """
    try:
        print(f"Fetching trails from data.gouv.fr (French Open Data Portal)...")
        print("Note: This may take a while as the dataset is large (~99 MB)")
        
        # First, get the dataset information to find the JSON resource URL
        dataset_url = f"{DATAGOUV_API}/{DATAGOUV_DATASET_ID}"
        print(f"Fetching dataset info from {dataset_url}...")
        dataset_response = requests.get(dataset_url, timeout=30)
        dataset_response.raise_for_status()
        dataset_data = dataset_response.json()
        
        # Find the JSON resource URL
        json_url = None
        resources = dataset_data.get('resources', [])
        for resource in resources:
            if resource.get('format') == 'json' or 'json' in resource.get('url', '').lower():
                json_url = resource.get('url')
                break
        
        if not json_url:
            print("Could not find JSON resource URL in dataset")
            return []
        
        print(f"Downloading JSON file from {json_url}...")
        # Download the JSON file
        response = requests.get(json_url, timeout=120, stream=True)
        response.raise_for_status()
        
        # Parse JSON (it's a large file, so we'll process it in chunks if needed)
        print("Downloading and parsing JSON data...")
        data = response.json()
        
        # The data structure may vary, but typically it's a GeoJSON FeatureCollection
        features = []
        if isinstance(data, dict):
            if 'features' in data:
                features = data['features']
            elif 'type' in data and data['type'] == 'FeatureCollection':
                features = data.get('features', [])
        elif isinstance(data, list):
            features = data
        
        print(f"Found {len(features)} trail features in dataset")
        
        # Helper function to convert EPSG:3857 (Web Mercator) to WGS84 if needed
        def convert_coords(coords, from_epsg3857=False):
            """Convert coordinates from EPSG:3857 to WGS84 if needed"""
            if from_epsg3857:
                # EPSG:3857 to WGS84 conversion
                lon = coords[0] / 20037508.34 * 180.0
                lat = coords[1] / 20037508.34 * 180.0
                lat = 180.0 / 3.14159265358979323846 * (2 * math.atan(math.exp(lat * 3.14159265358979323846 / 180.0)) - 3.14159265358979323846 / 2.0)
                return [lon, lat]
            return coords
        
        trails = []
        checked = 0
        for feature in features:
            try:
                if len(trails) >= limit:
                    break
                
                checked += 1
                if checked % 1000 == 0:
                    print(f"Processed {checked} features, found {len(trails)} trails so far...")
                
                # Extract properties
                props = feature.get('properties', {})
                geometry = feature.get('geometry', {})
                
                # Filter for hiking/foot routes
                route_type = props.get('route', '')
                if route_type not in ['hiking', 'foot']:
                    continue
                
                # Extract coordinates from geometry
                geom_type = geometry.get('type', '')
                if geom_type not in ['LineString', 'MultiLineString']:
                    continue
                
                coordinates = []
                if geom_type == 'LineString':
                    coords = geometry.get('coordinates', [])
                    # Check if coordinates are in EPSG:3857 (Web Mercator) - they're usually very large numbers
                    if coords and abs(coords[0][0]) > 180:
                        # Convert from EPSG:3857 to WGS84
                        import math
                        coordinates = [convert_coords(coord, from_epsg3857=True) for coord in coords]
                    else:
                        coordinates = coords
                elif geom_type == 'MultiLineString':
                    # Flatten MultiLineString to single LineString
                    coords_list = geometry.get('coordinates', [])
                    for coords in coords_list:
                        if coords and abs(coords[0][0]) > 180:
                            import math
                            coordinates.extend([convert_coords(coord, from_epsg3857=True) for coord in coords])
                        else:
                            coordinates.extend(coords)
                
                if not coordinates or len(coordinates) < 2:
                    continue
                
                # Filter by bounding box if provided
                if bbox:
                    min_lon, min_lat, max_lon, max_lat = bbox
                    # Check if trail intersects with bounding box
                    trail_in_bbox = False
                    for coord in coordinates:
                        lon, lat = coord[0], coord[1]
                        if min_lon <= lon <= max_lon and min_lat <= lat <= max_lat:
                            trail_in_bbox = True
                            break
                    if not trail_in_bbox:
                        continue
                
                # Calculate center point
                center_lat = sum(coord[1] for coord in coordinates) / len(coordinates)
                center_lon = sum(coord[0] for coord in coordinates) / len(coordinates)
                
                # Extract trail information
                name = props.get('name', props.get('ref', f"Trail {props.get('osm_id', 'unknown')}"))
                description = props.get('description', f"Hiking trail: {name}")
                
                # Extract distance (might be in meters)
                distance = props.get('distance')
                if distance:
                    try:
                        distance = float(distance) / 1000.0  # Convert to km
                    except (ValueError, TypeError):
                        distance = None
                
                # Extract difficulty
                difficulty_str = props.get('difficulty', 'moderate')
                difficulty = _parse_difficulty(difficulty_str)
                
                # Estimate duration
                duration = _estimate_duration(str(distance * 1000) if distance else None)
                
                # Extract elevation gain if available
                elevation_gain = props.get('ascent') or props.get('elevation_gain')
                if elevation_gain:
                    try:
                        elevation_gain = int(float(elevation_gain))
                    except (ValueError, TypeError):
                        elevation_gain = None
                
                # Determine trail type
                trail_type = 'loop' if props.get('circular') == 'yes' or props.get('type') == 'circular' else 'one_way'
                
                # Extract landscapes
                landscapes = _parse_landscapes(props)
                
                # Extract safety risks
                safety_risks = _parse_safety(props)
                
                # Extract accessibility
                accessibility = _parse_accessibility(props)
                
                # Create GeoJSON LineString for storage
                geojson_storage = {
                    "type": "LineString",
                    "coordinates": coordinates
                }
                
                trail = {
                    'trail_id': f"datagouv_{props.get('osm_id', 'unknown')}",
                    'name': name,
                    'latitude': center_lat,
                    'longitude': center_lon,
                    'coordinates': json.dumps(geojson_storage),
                    'description': description,
                    'distance': distance,
                    'difficulty': difficulty,
                    'duration': duration,
                    'elevation_gain': elevation_gain,
                    'trail_type': trail_type,
                    'landscapes': landscapes,
                    'popularity': 7.0,
                    'safety_risks': safety_risks,
                    'accessibility': accessibility,
                    'closed_seasons': props.get('seasonal', ''),
                }
                
                trails.append(trail)
                
            except Exception as e:
                print(f"Error parsing trail feature: {e}")
                continue
        
        print(f"Parsed {len(trails)} hiking trails from data.gouv.fr")
        return trails
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from data.gouv.fr: {e}")
        return []
    except Exception as e:
        print(f"Error parsing data.gouv.fr data: {e}")
        return []

def fetch_trails_from_trailhub(trail_system_id=None, limit=20):
    """
    Fetch hiking trails from TrailHUB.org API
    
    Args:
        trail_system_id: Trail System ID (if None, will try to discover systems)
        limit: Maximum number of trails to fetch
    """
    try:
        trails = []
        
        # If no trail system ID provided, try to discover or use a default
        # For French Alps, we might need to search for appropriate trail system IDs
        if trail_system_id is None:
            # Try some common trail system IDs or search
            # You may need to visit trailhub.org to find specific French Alps trail system IDs
            print("No trail system ID provided. Please provide a Trail System ID.")
            print("Visit https://trailhub.org to find trail system IDs for French Alps region.")
            return []
        
        print(f"Fetching trails from TrailHUB API (Trail System ID: {trail_system_id})...")
        url = f"{TRAILHUB_API}/{trail_system_id}"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        print(f"Received {len(data) if isinstance(data, list) else 1} trails from TrailHUB API")
        
        # Parse trail data
        trail_list = data if isinstance(data, list) else [data]
        
        for trail_data in trail_list[:limit]:
            try:
                # Extract trail information
                name = trail_data.get('name', f"Trail {trail_data.get('id', 'unknown')}")
                description = trail_data.get('description', f"Hiking trail: {name}")
                
                # Parse GeoJSON from the geoJson field
                geo_json_str = trail_data.get('geoJson', '')
                if not geo_json_str:
                    print(f"Skipping trail {name}: No GeoJSON data")
                    continue
                
                try:
                    geo_json = json.loads(geo_json_str) if isinstance(geo_json_str, str) else geo_json_str
                except json.JSONDecodeError:
                    print(f"Skipping trail {name}: Invalid GeoJSON")
                    continue
                
                # Extract coordinates from GeoJSON
                coordinates = []
                if geo_json.get('type') == 'LineString' and 'coordinates' in geo_json:
                    coordinates = geo_json['coordinates']
                elif geo_json.get('type') == 'Feature' and 'geometry' in geo_json:
                    geom = geo_json['geometry']
                    if geom.get('type') == 'LineString' and 'coordinates' in geom:
                        coordinates = geom['coordinates']
                
                if not coordinates or len(coordinates) < 2:
                    print(f"Skipping trail {name}: Insufficient coordinates")
                    continue
                
                # Calculate center point
                center_lat = sum(coord[1] for coord in coordinates) / len(coordinates)
                center_lon = sum(coord[0] for coord in coordinates) / len(coordinates)
                
                # Extract other properties
                distance = trail_data.get('distance')  # in meters, convert to km
                if distance:
                    distance = float(distance) / 1000.0
                
                difficulty_str = trail_data.get('difficulty', 'moderate')
                difficulty = _parse_difficulty(difficulty_str)
                
                # Estimate duration
                duration = _estimate_duration(str(distance * 1000) if distance else None)
                
                # Get elevation data if available
                elevations = trail_data.get('elevations', [])
                elevation_gain = None
                if elevations and len(elevations) > 1:
                    elevation_gain = int(max(elevations) - min(elevations))
                
                # Determine trail type
                activities = trail_data.get('activities', [])
                trail_type = 'loop' if 'loop' in str(activities).lower() else 'one_way'
                
                # Create GeoJSON LineString for storage
                geojson_storage = {
                    "type": "LineString",
                    "coordinates": coordinates
                }
                
                trail = {
                    'trail_id': f"trailhub_{trail_data.get('id', 'unknown')}",
                    'name': name,
                    'latitude': center_lat,
                    'longitude': center_lon,
                    'coordinates': json.dumps(geojson_storage),
                    'description': description,
                    'distance': distance,
                    'difficulty': difficulty,
                    'duration': duration,
                    'elevation_gain': elevation_gain,
                    'trail_type': trail_type,
                    'landscapes': _parse_landscapes({}),  # TrailHUB might not have landscape tags
                    'popularity': 7.0,
                    'safety_risks': 'none',
                    'accessibility': '',
                    'closed_seasons': '',
                }
                
                trails.append(trail)
                
            except Exception as e:
                print(f"Error parsing trail: {e}")
                continue
        
        print(f"Parsed {len(trails)} hiking trails from TrailHUB")
        return trails
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from TrailHUB API: {e}")
        return []
    except Exception as e:
        print(f"Error parsing TrailHUB data: {e}")
        return []

def fetch_trails_from_overpass(bbox="5.0,44.0,7.5,46.5", limit=20):
    """
    Fetch hiking trails from Overpass API for French Alps region
    
    Args:
        bbox: Bounding box as "min_lon,min_lat,max_lon,max_lat" (French Alps region)
        limit: Maximum number of trails to fetch
    """
    # Overpass query to find hiking routes in the bounding box
    # Using geom to get full geometry with all coordinate points
    # Simplified query to avoid timeout - focusing on relations first (they're usually better documented)
    query = f"""
    [out:json][timeout:15];
    (
      relation["route"="hiking"]({bbox});
      relation["route"="foot"]({bbox});
    );
    out geom;
    """
    
    # Try multiple Overpass servers in case one is down
    overpass_servers = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass.openstreetmap.fr/api/interpreter"
    ]
    
    response = None
    for server_url in overpass_servers:
        try:
            print(f"Fetching trails from Overpass API (bbox: {bbox}) using {server_url}...")
            response = requests.post(server_url, data=query, timeout=25)
            response.raise_for_status()
            break  # Success, exit the loop
        except requests.exceptions.RequestException as e:
            print(f"Server {server_url} failed: {e}")
            if server_url == overpass_servers[-1]:  # Last server
                raise  # Re-raise if all servers failed
            continue  # Try next server
    
    # Check if we got a valid response
    if response is None:
        raise requests.exceptions.RequestException("All Overpass API servers failed")
    
    try:
        data = response.json()
        print(f"Received {len(data.get('elements', []))} elements from Overpass API")
        
        # Parse the data and extract trail information
        trails = []
        ways = {}
        nodes = {}
        
        # First pass: collect ways and nodes (for fallback if geometry not available)
        for element in data.get('elements', []):
            if element['type'] == 'way':
                ways[element['id']] = element
            elif element['type'] == 'node':
                nodes[element['id']] = element
        
        # Process relations first (they often contain multiple ways)
        relations = {}
        for element in data.get('elements', []):
            if element['type'] == 'relation' and element.get('tags', {}).get('route') == 'hiking':
                relations[element['id']] = element
        
        # Second pass: process ways and relations that are hiking routes
        for element in data.get('elements', []):
            is_hiking_route = False
            tags = {}
            name = ""
            
            # Check if it's a hiking-related route or path
            tags = element.get('tags', {})
            route_type = tags.get('route', '')
            highway_type = tags.get('highway', '')
            hiking_tag = tags.get('hiking', '')
            
            is_hiking_route = (
                (element['type'] == 'way' and (route_type in ['hiking', 'foot', 'walking'] or 
                 (highway_type in ['path', 'footway'] and hiking_tag == 'yes'))) or
                (element['type'] == 'relation' and route_type in ['hiking', 'foot', 'walking'])
            )
            
            if is_hiking_route:
                name = tags.get('name', tags.get('ref', f"Trail {element['id']}"))
            
            if is_hiking_route:
                # Get coordinates for the way or relation
                coordinates = []
                
                # For relations, collect coordinates from member ways
                if element['type'] == 'relation' and 'members' in element:
                    # Collect all way members
                    member_ways = []
                    for member in element['members']:
                        if member['type'] == 'way' and member['ref'] in ways:
                            member_ways.append(ways[member['ref']])
                    
                    # Sort ways by role if available, otherwise use order
                    # For now, just process all ways in order
                    for way in member_ways:
                        if 'geometry' in way:
                            for point in way['geometry']:
                                coordinates.append([point['lon'], point['lat']])
                        elif 'nodes' in way:
                            for node_id in way['nodes']:
                                if node_id in nodes:
                                    node = nodes[node_id]
                                    coordinates.append([node['lon'], node['lat']])
                
                # For ways, get geometry directly
                elif element['type'] == 'way':
                    # First try to get geometry directly (from out geom)
                    if 'geometry' in element:
                        # Geometry is already in the element when using out geom
                        for point in element['geometry']:
                            coordinates.append([point['lon'], point['lat']])
                    elif 'nodes' in element:
                        # Fallback: get coordinates from nodes
                        for node_id in element['nodes']:
                            if node_id in nodes:
                                node = nodes[node_id]
                                coordinates.append([node['lon'], node['lat']])
                
                if coordinates and len(coordinates) > 1:
                    # Calculate approximate center point
                    center_lat = sum(coord[1] for coord in coordinates) / len(coordinates)
                    center_lon = sum(coord[0] for coord in coordinates) / len(coordinates)
                    
                    # Create GeoJSON LineString
                    geojson = {
                        "type": "LineString",
                        "coordinates": coordinates
                    }
                    
                    trail = {
                        'trail_id': f"osm_{element['type']}_{element['id']}",
                        'name': name,
                        'latitude': center_lat,
                        'longitude': center_lon,
                        'coordinates': json.dumps(geojson),
                        'description': tags.get('description', f"Hiking trail: {name}"),
                        'distance': float(tags.get('distance', 0)) if tags.get('distance') else None,
                        'difficulty': _parse_difficulty(tags.get('difficulty', 'medium')),
                        'duration': _estimate_duration(tags.get('distance')),
                        'elevation_gain': int(tags.get('ascent', 0)) if tags.get('ascent') else None,
                        'trail_type': 'loop' if tags.get('circular') == 'yes' or tags.get('type') == 'circular' else 'one_way',
                        'landscapes': _parse_landscapes(tags),
                        'popularity': 7.0,  # Default, could be enhanced with OSM data
                        'safety_risks': _parse_safety(tags),
                        'accessibility': _parse_accessibility(tags),
                        'closed_seasons': tags.get('seasonal', ''),
                    }
                    
                    trails.append(trail)
                    if len(trails) >= limit:
                        break
        
        print(f"Parsed {len(trails)} hiking trails")
        return trails
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from Overpass API: {e}")
        return []
    except Exception as e:
        print(f"Error parsing Overpass data: {e}")
        return []

def _parse_difficulty(difficulty_str):
    """Convert OSM difficulty to numeric value (1-10)"""
    difficulty_map = {
        'easy': 3.0,
        'moderate': 5.0,
        'hard': 7.5,
        'difficult': 8.5,
        'extreme': 9.5
    }
    return difficulty_map.get(difficulty_str.lower(), 5.0)

def _estimate_duration(distance_str):
    """Estimate duration in minutes based on distance"""
    if not distance_str:
        return 120  # Default 2 hours
    try:
        distance_km = float(distance_str)
        # Assume average hiking speed of 4 km/h
        return int(distance_km / 4 * 60)
    except:
        return 120

def _parse_landscapes(tags):
    """Extract landscape types from OSM tags"""
    landscapes = []
    if tags and tags.get('waterway'):
        landscapes.append('river')
    if tags and (tags.get('natural') == 'water' or tags.get('water')):
        landscapes.append('lake')
    name = tags.get('name', '') if tags else ''
    if tags and (tags.get('mountain') == 'yes' or (name and 'peak' in name.lower())):
        landscapes.append('peaks')
    if tags and (tags.get('landuse') == 'forest' or (name and 'forest' in name.lower())):
        landscapes.append('forest')
    if not landscapes:
        landscapes.append('alpine')
    return ','.join(landscapes)

def _parse_safety(tags):
    """Extract safety information from OSM tags"""
    risks = []
    if tags.get('hazard'):
        risks.append(tags['hazard'])
    if tags.get('slippery') == 'yes':
        risks.append('slippery')
    if tags.get('exposed') == 'yes':
        risks.append('exposed')
    return ','.join(risks) if risks else 'none'

def _parse_accessibility(tags):
    """Extract accessibility information"""
    access = []
    if tags and tags.get('dog') == 'yes':
        access.append('dog-friendly')
    if tags and tags.get('bicycle') == 'yes':
        access.append('bike-friendly')
    return ','.join(access) if access else ''

def _ensure_trail_fields(trail):
    """Ensure all required trail fields have default values"""
    defaults = {
        'trail_id': f"unknown_{hash(str(trail))}",
        'name': 'Unnamed Trail',
        'difficulty': 5.0,
        'distance': None,
        'duration': 120,  # Default 2 hours
        'elevation_gain': None,
        'trail_type': 'one_way',
        'landscapes': 'alpine',
        'popularity': 7.0,
        'safety_risks': 'none',
        'accessibility': '',
        'closed_seasons': '',
        'description': '',
        'latitude': None,
        'longitude': None,
        'coordinates': None
    }
    
    # Create a new dict with defaults, then update with trail values
    complete_trail = defaults.copy()
    complete_trail.update(trail)
    
    # Ensure required fields are not None (except for optional ones)
    if complete_trail['name'] is None or complete_trail['name'] == '':
        complete_trail['name'] = defaults['name']
    if complete_trail['difficulty'] is None:
        complete_trail['difficulty'] = defaults['difficulty']
    if complete_trail['duration'] is None:
        complete_trail['duration'] = defaults['duration']
    if complete_trail['trail_type'] is None or complete_trail['trail_type'] == '':
        complete_trail['trail_type'] = defaults['trail_type']
    if complete_trail['landscapes'] is None or complete_trail['landscapes'] == '':
        complete_trail['landscapes'] = defaults['landscapes']
    if complete_trail['popularity'] is None:
        complete_trail['popularity'] = defaults['popularity']
    if complete_trail['safety_risks'] is None or complete_trail['safety_risks'] == '':
        complete_trail['safety_risks'] = defaults['safety_risks']
    if complete_trail['accessibility'] is None:
        complete_trail['accessibility'] = defaults['accessibility']
    if complete_trail['closed_seasons'] is None:
        complete_trail['closed_seasons'] = defaults['closed_seasons']
    if complete_trail['description'] is None:
        complete_trail['description'] = defaults['description']
    
    # Ensure coordinates is a JSON string if it's a dict
    if isinstance(complete_trail.get('coordinates'), dict):
        complete_trail['coordinates'] = json.dumps(complete_trail['coordinates'])
    elif complete_trail.get('coordinates') is None:
        complete_trail['coordinates'] = None
    
    return complete_trail

def save_trails_to_db(trails):
    """Save fetched trails to the database"""
    if not trails:
        print("No trails to save")
        return
    
    conn = sqlite3.connect(TRAILS_DB)
    cur = conn.cursor()
    
    saved = 0
    for trail in trails:
        try:
            # Ensure all required fields are present with defaults
            complete_trail = _ensure_trail_fields(trail)
            
            # Validate required fields
            if not complete_trail.get('trail_id'):
                print(f"Skipping trail: missing trail_id")
                continue
            if complete_trail.get('latitude') is None or complete_trail.get('longitude') is None:
                print(f"Skipping trail {complete_trail.get('trail_id')}: missing coordinates")
                continue
            
            # Check if trail already exists
            cur.execute("SELECT trail_id FROM trails WHERE trail_id=?", (complete_trail['trail_id'],))
            if cur.fetchone():
                print(f"Trail {complete_trail['trail_id']} already exists, skipping...")
                continue
            
            # Insert trail
            cur.execute("""
                INSERT INTO trails (
                    trail_id, name, difficulty, distance, duration, elevation_gain,
                    trail_type, landscapes, popularity, safety_risks, accessibility,
                    closed_seasons, description, latitude, longitude, coordinates
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                complete_trail['trail_id'],
                complete_trail['name'],
                complete_trail['difficulty'],
                complete_trail.get('distance'),
                complete_trail['duration'],
                complete_trail.get('elevation_gain'),
                complete_trail['trail_type'],
                complete_trail['landscapes'],
                complete_trail['popularity'],
                complete_trail['safety_risks'],
                complete_trail['accessibility'],
                complete_trail['closed_seasons'],
                complete_trail['description'],
                complete_trail['latitude'],
                complete_trail['longitude'],
                complete_trail.get('coordinates')
            ))
            saved += 1
        except Exception as e:
            print(f"Error saving trail {trail.get('trail_id', 'unknown')}: {e}")
            import traceback
            traceback.print_exc()
    
    conn.commit()
    conn.close()
    print(f"Saved {saved} new trails to database")

if __name__ == "__main__":
    print("=" * 60)
    print("French Alps Trail Fetcher")
    print("=" * 60)
    
    # Try local Shapefile first (if downloaded from data.gouv.fr)
    print("\n1. Trying local Shapefile (if available)...")
    # French Alps bounding box: approximately 5.0°E-7.5°E, 44.0°N-46.5°N
    # Using Chamonix area as example: 6.8°E-7.0°E, 45.9°N-46.0°N
    trails = fetch_trails_from_shapefile(limit=20, bbox=(6.8, 45.9, 7.0, 46.0))
    
    # If Shapefile didn't work, try data.gouv.fr API
    if not trails:
        print("\n2. Trying data.gouv.fr API (French Open Data Portal)...")
        trails = fetch_trails_from_datagouv(limit=20, bbox=(6.8, 45.9, 7.0, 46.0))
    
    # If neither worked, try TrailHUB
    if not trails:
        print("\n3. Trying TrailHUB.org API...")
        
        # You can provide a trail system ID here, or find one at https://trailhub.org
        # To find a Trail System ID:
        # 1. Visit https://trailhub.org
        # 2. Browse to a trail system in French Alps
        # 3. The Trail System ID is usually in the URL or you can inspect the page source
        # Example: If URL is https://trailhub.org/ts/12345, then trail_system_id is "12345"
        
        # Uncomment and replace with an actual Trail System ID:
        # trail_system_id = "YOUR_TRAIL_SYSTEM_ID_HERE"
        trail_system_id = None
        
        if trail_system_id:
            trails = fetch_trails_from_trailhub(trail_system_id=trail_system_id, limit=20)
        else:
            print("No Trail System ID provided. Skipping TrailHUB.")
            print("To use TrailHUB, edit this script and set trail_system_id variable.")
    
    # If none worked, try Overpass as last resort
    if not trails:
        print("\n4. Trying OpenStreetMap Overpass API...")
        # Using smaller bounding box around Chamonix area to avoid timeout
        # Bounding box: Chamonix area (6.8°E-7.0°E, 45.9°N-46.0°N)
        trails = fetch_trails_from_overpass(bbox="6.8,45.9,7.0,46.0", limit=20)
    
    if trails:
        print(f"\nFound {len(trails)} trails:")
        for trail in trails[:5]:  # Show first 5
            print(f"  - {trail['name']} (ID: {trail['trail_id']})")
        
        # Auto-save trails (can be changed to ask for confirmation)
        print(f"\nAuto-saving {len(trails)} trails to database...")
        save_trails_to_db(trails)
    else:
        print("No trails found or error occurred")
        print("\nTo use TrailHUB:")
        print("1. Visit https://trailhub.org")
        print("2. Find a trail system in the French Alps region")
        print("3. Get the Trail System ID from the URL or API")
        print("4. Update the script to use: fetch_trails_from_trailhub(trail_system_id='YOUR_ID')")

