# -*- coding: utf-8 -*-
"""
Utilities to extract real French hiking trails from the local shapefile.

The loader focuses exclusively on high-quality routes that:
  • fall inside specified French region bounding boxes
  • expose a meaningful name/title
  • include geometry samples that allow building an elevation profile

It can emit JSON snapshots for inspection or write the curated trails straight
into the SQLite database used by the adaptive recommender.
"""

from __future__ import annotations

import argparse
import json
import math
import sqlite3
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import requests  # type: ignore
import shapefile  # type: ignore


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "source"
SHAPEFILE_PATH = DATA_DIR / "hiking_foot_routes_lineLine.shp"
DEFAULT_OUTPUT = BASE_DIR / "data_pipeline" / "french_trails.json"
TRAILS_DB = BASE_DIR / "backend" / "trails.db"

# Geographic envelopes for various French regions (min_lon, min_lat, max_lon, max_lat)
FRENCH_REGIONS = {
    "french_alps": {
        "bbox": (5.0, 44.0, 7.9, 46.8),
        "description": "French Alps - High mountain terrain with peaks and glaciers"
    },
    "pyrenees": {
        "bbox": (-1.5, 42.2, 3.2, 43.3),
        "description": "Pyrenees - Mountain range with diverse landscapes"
    },
    "massif_central": {
        "bbox": (2.0, 44.5, 4.5, 46.0),
        "description": "Massif Central - Volcanic mountains and plateaus"
    },
    "jura": {
        "bbox": (5.5, 46.0, 7.5, 47.5),
        "description": "Jura Mountains - Forested mountains and valleys"
    },
    "vosges": {
        "bbox": (6.5, 47.5, 7.5, 48.5),
        "description": "Vosges Mountains - Forested peaks and lakes"
    },
    "provence": {
        "bbox": (4.5, 43.0, 7.0, 44.5),
        "description": "Provence - Mediterranean landscapes and hills"
    },
    "brittany": {
        "bbox": (-5.5, 47.0, -1.0, 48.8),
        "description": "Brittany - Coastal paths and inland trails"
    },
    "normandy": {
        "bbox": (-1.8, 48.2, 1.8, 49.7),
        "description": "Normandy - Coastal and countryside trails"
    }
}

# Default: French Alps (for backward compatibility)
FRENCH_ALPS_BBOX = FRENCH_REGIONS["french_alps"]["bbox"]
MAX_ELEVATION_SAMPLES = 180
MIN_NAMED_DISTANCE_KM = 2.0


def _verify_shapefile(path: Path) -> None:
    required = [path.with_suffix(suffix) for suffix in (".shp", ".dbf", ".shx")]
    missing = [str(candidate) for candidate in required if not candidate.exists()]
    if missing:
        raise FileNotFoundError(
            "Missing shapefile component(s):\n  - "
            + "\n  - ".join(missing)
            + "\nDownload the hiking dataset from data.gouv.fr and place all files "
            "inside the adaptive_quiz_system directory."
        )


def _mercator_to_wgs84(x: float, y: float) -> Tuple[float, float]:
    """Convert EPSG:3857 coordinates to latitude/longitude."""
    lon = x / 20037508.34 * 180.0
    lat = y / 20037508.34 * 180.0
    lat = 180.0 / math.pi * (2 * math.atan(math.exp(lat * math.pi / 180.0)) - math.pi / 2.0)
    return lon, lat


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _coerce_str(value) -> str:
    if isinstance(value, str):
        return value
    if value is None:
        return ""
    return str(value)


def _parse_difficulty(raw: str | None) -> float:
    mapping = {
        "hiking": 3.0,
        "easy": 3.0,
        "moderate": 5.0,
        "demanding_mountain_hiking": 6.5,
        "alpine_hiking": 8.0,
        "advanced_hiking": 7.0,
        "difficult": 8.5,
        "hard": 8.5,
        "extreme": 9.5,
    }
    if not raw:
        return 5.0
    return mapping.get(raw.lower(), 5.0)


def _estimate_difficulty_from_characteristics(
    distance_km: float,
    elevation_gain: int | None = None,
    elevation_gain_per_km: float | None = None,
) -> float:
    """
    Estimate difficulty based on trail characteristics when source data is missing.
    Uses elevation gain per km as the primary indicator.
    
    Returns a difficulty value between 1.0 (very easy) and 10.0 (extreme).
    """
    if elevation_gain_per_km is None:
        if elevation_gain is not None and distance_km > 0:
            elevation_gain_per_km = elevation_gain / distance_km
        else:
            # Default fallback: assume moderate terrain
            elevation_gain_per_km = 50.0
    
    # Classify based on elevation gain per km
    # More realistic thresholds based on typical hiking standards:
    # - < 30 m/km: Easy (flat/gentle)
    # - 30-60 m/km: Moderate (rolling hills)
    # - 60-100 m/km: Challenging (steep sections)
    # - 100-150 m/km: Very challenging (mountainous)
    # - > 150 m/km: Extreme (alpine/technical)
    if elevation_gain_per_km < 30:
        # Flat or gentle terrain
        base_difficulty = 2.5
    elif elevation_gain_per_km < 60:
        # Moderate terrain
        base_difficulty = 4.0
    elif elevation_gain_per_km < 100:
        # Challenging terrain
        base_difficulty = 5.5
    elif elevation_gain_per_km < 150:
        # Very challenging
        base_difficulty = 7.0
    else:
        # Extreme terrain
        base_difficulty = 8.5
    
    # Adjust for distance (longer trails are slightly harder, but not dramatically)
    if distance_km > 25:
        base_difficulty += 0.4
    elif distance_km > 20:
        base_difficulty += 0.3
    elif distance_km > 15:
        base_difficulty += 0.2
    elif distance_km < 5:
        base_difficulty -= 0.3
    
    # Clamp to valid range
    return max(1.0, min(10.0, base_difficulty))


def _estimate_duration_minutes(distance_km: float | None) -> int:
    if not distance_km or distance_km <= 0:
        return 120
    return int(max(30, (distance_km / 4.0) * 60))


def _parse_landscapes(props: Dict[str, str]) -> str:
    landscapes: List[str] = []
    name = props.get("name", "").lower()
    if "lac" in name or props.get("natural") == "water":
        landscapes.append("lake")
    if "glacier" in name:
        landscapes.append("glacier")
    if props.get("landuse") == "forest" or "forest" in name:
        landscapes.append("forest")
    if any(token in name for token in ["mont", "peak", "col", "dent"]):
        landscapes.append("peaks")
    if "river" in name or props.get("waterway"):
        landscapes.append("river")
    if not landscapes:
        landscapes.append("alpine")
    return ",".join(dict.fromkeys(landscapes))  # preserve order, remove duplicates


def _parse_safety(props: Dict[str, str]) -> str:
    risks: List[str] = []
    hazard = props.get("hazard")
    if hazard:
        risks.append(hazard)
    if props.get("slippery") == "yes":
        risks.append("slippery")
    if props.get("exposed") == "yes":
        risks.append("exposed")
    if props.get("avalanche") == "yes":
        risks.append("avalanche")
    return ",".join(risks) if risks else "none"


def _parse_accessibility(props: Dict[str, str]) -> str:
    tags: List[str] = []
    if props.get("dog") == "yes":
        tags.append("dog-friendly")
    if props.get("bicycle") == "yes":
        tags.append("bike-friendly")
    if props.get("wheelchair") == "yes":
        tags.append("wheelchair-accessible")
    return ",".join(tags)


def _build_geojson(coords: Sequence[Tuple[float, float]]) -> str:
    return json.dumps({"type": "LineString", "coordinates": [[lon, lat] for lon, lat in coords]})


def _calc_distances(coords: Sequence[Tuple[float, float]]) -> Tuple[float, List[float]]:
    cumulative = [0.0]
    total = 0.0
    for idx in range(1, len(coords)):
        lon1, lat1 = coords[idx - 1]
        lon2, lat2 = coords[idx]
        segment = _haversine_km(lat1, lon1, lat2, lon2)
        total += segment
        cumulative.append(total)
    return total, cumulative


def _sample_coordinates(coords: Sequence[Tuple[float, float]], max_points: int) -> List[Tuple[float, float]]:
    if len(coords) <= max_points:
        return list(coords)
    step = len(coords) / max_points
    sampled = [coords[int(i * step)] for i in range(max_points)]
    if sampled[-1] != coords[-1]:
        sampled[-1] = coords[-1]
    return sampled


def _fetch_elevation_profile(coords: Sequence[Tuple[float, float]]) -> Tuple[List[Dict[str, float]], int]:
    if not coords:
        return [], 0
    sampled = _sample_coordinates(coords, MAX_ELEVATION_SAMPLES)
    payload = [
        {"latitude": lat, "longitude": lon}
        for lon, lat in sampled  # API expects lat/lon ordering
    ]
    response = requests.post(
        "https://api.open-elevation.com/api/v1/lookup",
        json={"locations": payload},
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()
    results = data.get("results", [])
    if len(results) != len(sampled):
        return [], 0

    _, cumulative = _calc_distances(sampled)
    profile: List[Dict[str, float]] = []
    gain = 0.0
    for idx, point in enumerate(results):
        elevation = float(point.get("elevation", 0.0))
        profile.append({"distance_m": round(cumulative[idx] * 1000, 1), "elevation_m": elevation})
        if idx > 0:
            diff = elevation - profile[idx - 1]["elevation_m"]
            if diff > 0:
                gain += diff

    return profile, int(round(gain))


def _trail_name(props: Dict[str, str], centroid: Tuple[float, float]) -> str:
    for key in ("name", "ref", "short_name"):
        value = _coerce_str(props.get(key)).strip()
        if value:
            return value
    return ""  # Require explicit name – unnamed features will be discarded


def _is_in_bbox(coords: Sequence[Tuple[float, float]], bbox: Tuple[float, float, float, float]) -> bool:
    min_lon, min_lat, max_lon, max_lat = bbox
    return any(min_lon <= lon <= max_lon and min_lat <= lat <= max_lat for lon, lat in coords)


def _trail_type_from_coords(coords: Sequence[Tuple[float, float]]) -> str:
    if len(coords) < 2:
        return "one_way"
    start = coords[0]
    end = coords[-1]
    close_enough = _haversine_km(start[1], start[0], end[1], end[0]) < 0.2
    return "loop" if close_enough else "one_way"


def load_french_trails(
    shapefile_path: Path = SHAPEFILE_PATH,
    *,
    regions: List[str] | None = None,
    bbox: Tuple[float, float, float, float] | None = None,
    limit_per_region: int | None = None,
    total_limit: int | None = None,
) -> List[Dict]:
    """
    Parse the shapefile and return curated French trails from specified regions.
    
    Args:
        shapefile_path: Path to the shapefile
        regions: List of region names to load (e.g., ["french_alps", "pyrenees"]). 
                 If None and bbox is None, loads all regions.
        bbox: Optional single bounding box (for backward compatibility)
        limit_per_region: Maximum trails per region
        total_limit: Maximum total trails across all regions
    
    Returns:
        List of trail dictionaries
    """
    _verify_shapefile(shapefile_path)
    reader = shapefile.Reader(str(shapefile_path), encoding="latin1")
    fields = [field[0] for field in reader.fields[1:]]

    # Determine which regions to load
    if bbox:
        # Backward compatibility: single bbox
        regions_to_load = [{"bbox": bbox, "name": "french_alps", "description": "French Alps"}]
    elif regions:
        # Load specified regions
        regions_to_load = [
            {"bbox": FRENCH_REGIONS[r]["bbox"], "name": r, "description": FRENCH_REGIONS[r]["description"]}
            for r in regions if r in FRENCH_REGIONS
        ]
    else:
        # Load all regions
        regions_to_load = [
            {"bbox": info["bbox"], "name": name, "description": info["description"]}
            for name, info in FRENCH_REGIONS.items()
        ]

    if not regions_to_load:
        return []

    all_trails: List[Dict] = []
    region_counts: Dict[str, int] = {r["name"]: 0 for r in regions_to_load}

    # Process shapes in a deterministic order for reproducibility
    # Convert to list and sort by a stable identifier (osm_id) for deterministic order
    shapes_and_records = list(zip(reader.shapes(), reader.records()))
    # Sort by osm_id if available, otherwise by first coordinate for stability
    shapes_and_records.sort(key=lambda x: (
        dict(zip([field[0] for field in reader.fields[1:]], x[1])).get("osm_id") or 0,
        x[0].points[0][0] if x[0].points else 0,  # First X coordinate as tiebreaker
        x[0].points[0][1] if x[0].points else 0  # First Y coordinate as second tiebreaker
    ))

    for shape, record in shapes_and_records:
        if total_limit and len(all_trails) >= total_limit:
            break
        if shape.shapeType != shapefile.POLYLINE:
            continue

        coords_mercator = shape.points
        coords_wgs84 = [_mercator_to_wgs84(x, y) for x, y in coords_mercator]
        if not coords_wgs84 or len(coords_wgs84) < 2:
            continue

        # Find which region this trail belongs to
        matching_region = None
        for region_info in regions_to_load:
            if _is_in_bbox(coords_wgs84, region_info["bbox"]):
                # Check if we've reached the limit for this region
                if limit_per_region and region_counts[region_info["name"]] >= limit_per_region:
                    continue
                matching_region = region_info
                break

        if not matching_region:
            continue

        props = dict(zip(fields, record))
        route_type = _coerce_str(props.get("route"))
        if route_type not in {"hiking", "foot"}:
            continue

        centroid_lat = sum(lat for _, lat in coords_wgs84) / len(coords_wgs84)
        centroid_lon = sum(lon for lon, _ in coords_wgs84) / len(coords_wgs84)
        name = _trail_name(props, (centroid_lat, centroid_lon))
        if not name:
            continue

        total_distance_km, cumulative = _calc_distances(coords_wgs84)
        declared_distance = _coerce_str(props.get("distance", "")).strip()
        if declared_distance:
            try:
                if "km" in declared_distance.lower():
                    total_distance_km = float(declared_distance.lower().replace("km", "").strip())
                elif "m" in declared_distance.lower():
                    total_distance_km = float(declared_distance.lower().replace("m", "").strip()) / 1000.0
                else:
                    total_distance_km = float(declared_distance)
            except ValueError:
                pass

        if total_distance_km < MIN_NAMED_DISTANCE_KM:
            continue

        sac_scale = _coerce_str(props.get("sac_scale"))
        raw_difficulty_value = sac_scale or props.get("difficulty")
        raw_difficulty = _parse_difficulty(raw_difficulty_value)
        duration = _estimate_duration_minutes(total_distance_km)
        landscapes = _parse_landscapes({k: _coerce_str(v) for k, v in props.items()})
        safety = _parse_safety({k: _coerce_str(v) for k, v in props.items()})
        accessibility = _parse_accessibility({k: _coerce_str(v) for k, v in props.items()})
        trail_type = _trail_type_from_coords(coords_wgs84)

        try:
            elevation_profile, elevation_gain = _fetch_elevation_profile(coords_wgs84)
        except Exception as exc:  # noqa: BLE001 - keep the pipeline resilient
            print(f"[WARN] Elevation profile failed for {name}: {exc}")
            elevation_profile = []
            elevation_gain = int(total_distance_km * 75)
        
        # If difficulty defaulted to 5.0 (medium) because the field was missing or didn't match,
        # try to estimate from trail characteristics (elevation gain, distance)
        if raw_difficulty == 5.0 and not raw_difficulty_value:
            # No difficulty field found in source - estimate from characteristics
            difficulty = _estimate_difficulty_from_characteristics(
                total_distance_km, elevation_gain
            )
        else:
            # Use the parsed difficulty from source data (even if it's 5.0 from a match)
            difficulty = raw_difficulty

        region_name = matching_region["name"]
        trail_id = f"{region_name}_{props.get('osm_id') or props.get('id') or len(all_trails)}"
        description = _coerce_str(props.get("note") or props.get("description"))
        if not description:
            description = f"Authentic {matching_region['description']} itinerary along {name}."
        popularity = round(min(9.8, 6.0 + total_distance_km / 5.0 + difficulty / 10.0), 1)

        # Ensure all fields are non-null with default values
        all_trails.append(
            {
                "trail_id": trail_id or f"trail_{len(all_trails)}",
                "name": name or "Unnamed Trail",
                "description": description or f"Hiking trail in {region_name}",
                "difficulty": float(difficulty) if difficulty is not None else 5.0,
                "distance": round(float(total_distance_km), 2) if total_distance_km is not None else 5.0,
                "duration": int(duration) if duration is not None else 120,
                "elevation_gain": int(elevation_gain) if elevation_gain is not None else 0,
                "elevation_profile": elevation_profile if elevation_profile is not None else [],
                "trail_type": trail_type or "one_way",
                "landscapes": landscapes or "alpine",
                "popularity": float(popularity) if popularity is not None else 6.0,
                "safety_risks": safety or "none",
                "accessibility": accessibility or "",
                "closed_seasons": "",
                "latitude": float(centroid_lat) if centroid_lat is not None else 0.0,
                "longitude": float(centroid_lon) if centroid_lon is not None else 0.0,
                "coordinates": _build_geojson(coords_wgs84) if coords_wgs84 else json.dumps({"type": "LineString", "coordinates": []}),
                "region": region_name or "unknown",
                "source": "french_osm_shapefile",
                "is_real": 1,
            }
        )
        region_counts[region_name] += 1

    return all_trails


# Backward compatibility alias
def load_french_alps_trails(
    shapefile_path: Path = SHAPEFILE_PATH,
    *,
    bbox: Tuple[float, float, float, float] = FRENCH_ALPS_BBOX,
    limit: int | None = None,
) -> List[Dict]:
    """Backward compatibility: Load only French Alps trails."""
    return load_french_trails(
        shapefile_path=shapefile_path,
        bbox=bbox,
        total_limit=limit
    )


def save_trails_to_json(trails: Sequence[Dict], output_path: Path = DEFAULT_OUTPUT) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(trails, indent=2), encoding="utf-8")
    return output_path


def write_trails_to_db(trails: Sequence[Dict], db_path: Path = TRAILS_DB) -> None:
    if not trails:
        print("No trails to persist.")
        return
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    columns = [
        "trail_id",
        "name",
        "difficulty",
        "distance",
        "duration",
        "elevation_gain",
        "trail_type",
        "landscapes",
        "popularity",
        "safety_risks",
        "accessibility",
        "closed_seasons",
        "description",
        "latitude",
        "longitude",
        "coordinates",
        "region",
        "source",
        "is_real",
        "elevation_profile",
    ]
    placeholders = ",".join("?" for _ in columns)
    for trail in trails:
        cur.execute(
            f"""
            INSERT OR REPLACE INTO trails ({','.join(columns)})
            VALUES ({placeholders})
            """,
            [
                trail.get("trail_id"),
                trail.get("name"),
                trail.get("difficulty"),
                trail.get("distance"),
                trail.get("duration"),
                trail.get("elevation_gain"),
                trail.get("trail_type"),
                trail.get("landscapes"),
                trail.get("popularity"),
                trail.get("safety_risks"),
                trail.get("accessibility"),
                trail.get("closed_seasons"),
                trail.get("description"),
                trail.get("latitude"),
                trail.get("longitude"),
                trail.get("coordinates"),
                trail.get("region"),
                trail.get("source"),
                trail.get("is_real"),
                json.dumps(trail.get("elevation_profile", [])),
            ],
        )
    conn.commit()
    conn.close()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract real French trails from the local shapefile.")
    parser.add_argument("--limit", type=int, default=None, help="Optional limit for the total number of trails to load.")
    parser.add_argument(
        "--regions",
        type=str,
        nargs="+",
        choices=list(FRENCH_REGIONS.keys()),
        help="Regions to load (e.g., french_alps pyrenees). If not specified, loads all regions.",
    )
    parser.add_argument(
        "--bbox",
        type=float,
        nargs=4,
        metavar=("MIN_LON", "MIN_LAT", "MAX_LON", "MAX_LAT"),
        help="Restrict extraction to a custom bounding box (overrides --regions).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Path to the JSON file that will store the curated trails.",
    )
    parser.add_argument(
        "--write-db",
        action="store_true",
        help="Also persist the trails inside backend/trails.db (requires matching schema).",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    if args.bbox:
        # Backward compatibility: single bbox
        bbox = tuple(args.bbox)
        trails = load_french_trails(bbox=bbox, total_limit=args.limit)
    elif args.regions:
        # Load specified regions
        trails = load_french_trails(regions=args.regions, total_limit=args.limit)
    else:
        # Load all regions by default
        trails = load_french_trails(regions=None, total_limit=args.limit)
    
    if not trails:
        print("No matching trails found. Check the bounding box or shapefile path.")
        return

    output_path = save_trails_to_json(trails, args.output)
    print(f"Saved {len(trails)} real trails to {output_path}")
    
    # Print region breakdown
    region_counts: Dict[str, int] = {}
    for trail in trails:
        region = trail.get("region", "unknown")
        region_counts[region] = region_counts.get(region, 0) + 1
    print("Region breakdown:")
    for region, count in sorted(region_counts.items()):
        print(f"  {region}: {count} trails")

    if args.write_db:
        write_trails_to_db(trails)
        print(f"Persisted {len(trails)} trails into {TRAILS_DB}")


if __name__ == "__main__":
    main()

