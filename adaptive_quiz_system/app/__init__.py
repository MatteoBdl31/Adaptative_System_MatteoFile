from pathlib import Path
from datetime import date, datetime

from flask import Flask, render_template, request, redirect, url_for, jsonify

from backend.db import (
    get_all_users,
    get_user,
    get_trail,
    get_all_trails,
    record_trail_completion,
)
from adapt_trails import adapt_trails

BASE_DIR = Path(__file__).resolve().parent.parent


def get_season_from_date(target_date: str = None) -> str:
    """
    Determine the season based on a date.
    
    Args:
        target_date: Date in ISO format (YYYY-MM-DD). If None, uses today's date.
    
    Returns:
        Season string: "spring", "summer", "fall", or "winter"
    """
    if target_date:
        try:
            target = datetime.fromisoformat(target_date).date()
        except (ValueError, TypeError):
            target = date.today()
    else:
        target = date.today()
    
    month = target.month
    
    # Northern Hemisphere seasons (French Alps)
    # Note: Using "fall" to match the form options
    if month in [12, 1, 2]:  # December, January, February
        return "winter"
    elif month in [3, 4, 5]:  # March, April, May
        return "spring"
    elif month in [6, 7, 8]:  # June, July, August
        return "summer"
    else:  # September, October, November
        return "fall"  # Using "fall" to match form options


def detect_device_from_user_agent(user_agent: str = None) -> str:
    """
    Detect device type from user agent string.
    
    Args:
        user_agent: User agent string from request. If None, uses default.
    
    Returns:
        Device string: "mobile", "tablet", "desktop", or "laptop" (default)
    """
    if not user_agent:
        return "laptop"  # Default to laptop
    
    user_agent_lower = user_agent.lower()
    
    # Check for mobile devices
    mobile_keywords = ['mobile', 'android', 'iphone', 'ipod', 'blackberry', 'windows phone']
    if any(keyword in user_agent_lower for keyword in mobile_keywords):
        # Check if it's a tablet (iPad, Android tablets)
        tablet_keywords = ['ipad', 'tablet', 'playbook', 'kindle']
        if any(keyword in user_agent_lower for keyword in tablet_keywords):
            return "tablet"
        return "mobile"
    
    # Check for tablet devices
    tablet_keywords = ['ipad', 'tablet', 'playbook', 'kindle', 'android.*tablet']
    if any(keyword in user_agent_lower for keyword in tablet_keywords):
        return "tablet"
    
    # Check for desktop (Windows, Mac, Linux)
    desktop_keywords = ['windows', 'macintosh', 'mac os', 'linux', 'x11']
    if any(keyword in user_agent_lower for keyword in desktop_keywords):
        # Distinguish between desktop and laptop (simplified - assume desktop for desktop OS)
        # In practice, this is hard to distinguish, so we'll default to laptop for most cases
        return "desktop"
    
    # Default to laptop
    return "laptop"

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static"),
)


def format_duration(minutes):
    """Format duration in minutes to human-readable format (days/hours/minutes)"""
    if not minutes or minutes == 0:
        return "—"
    
    try:
        minutes = int(minutes)
    except (ValueError, TypeError):
        return "—"
    
    if minutes < 60:
        return f"{minutes} min"
    elif minutes < 1440:  # Less than 1 day
        hours = minutes // 60
        mins = minutes % 60
        if mins == 0:
            return f"{hours} hour{'s' if hours != 1 else ''}"
        else:
            return f"{hours} hour{'s' if hours != 1 else ''} {mins} min"
    else:  # 1 day or more
        days = minutes // 1440
        remaining_minutes = minutes % 1440
        hours = remaining_minutes // 60
        mins = remaining_minutes % 60
        
        parts = []
        if days > 0:
            parts.append(f"{days} day{'s' if days != 1 else ''}")
        if hours > 0:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if mins > 0 and days == 0:  # Only show minutes if less than a day total
            parts.append(f"{mins} min")
        
        return " ".join(parts) if parts else "—"


# Register the filter for use in templates
app.jinja_env.filters['format_duration'] = format_duration

@app.template_filter('profile_name_en')
def profile_name_en_filter(profile_key):
    """Convert profile key to English display name."""
    if not profile_key:
        return None
    profile_names = {
        "elevation_lover": "Elevation Enthusiast",
        "performance_athlete": "Performance Athlete",
        "contemplative": "Contemplative Hiker",
        "casual": "Casual Hiker",
        "family": "Family / Group Hiker",
        "explorer": "Explorer / Adventurer",
        "photographer": "Photographer / Content Creator"
    }
    return profile_names.get(profile_key, profile_key)

@app.template_filter('profile_name_short')
def profile_name_short_filter(profile_key):
    """Convert profile key to short English display name for dropdowns."""
    if not profile_key:
        return None
    profile_names = {
        "elevation_lover": "Elevation Enthusiast",
        "performance_athlete": "Performance Athlete",
        "contemplative": "Contemplative Hiker",
        "casual": "Casual Hiker",
        "family": "Family Hiker",
        "explorer": "Explorer",
        "photographer": "Photographer"
    }
    return profile_names.get(profile_key, profile_key)

# DEMO_CONTEXTS removed - predefined scenarios no longer used

CONTEXT_FIELD_DEFS = [
    {"name": "hike_start_date", "label": "Start Date", "type": "date"},
    {"name": "hike_end_date", "label": "End Date", "type": "date"},
    # Days and hours are calculated in background, not shown in UI
    # Device and season are auto-detected in background, not shown in UI
    {"name": "weather", "label": "Weather", "type": "select", "options": ["sunny", "cloudy", "rainy", "storm_risk", "snowy"]},
    {"name": "connection", "label": "Connection", "type": "select", "options": ["strong", "medium", "weak"]},
]


# Helper functions for context extraction and result building
def extract_context_from_request(prefix, request_args):
    """Extract context parameters from request for a given prefix (a or b)"""
    context = {}
    form_values = {}
    
    # Get hike date range
    start_date_param = f"{prefix}_hike_start_date"
    end_date_param = f"{prefix}_hike_end_date"
    hike_start_date = request_args.get(start_date_param)
    hike_end_date = request_args.get(end_date_param)
    
    if hike_start_date:
        context["hike_start_date"] = hike_start_date
        form_values["hike_start_date"] = hike_start_date
        # Also set hike_date for backward compatibility
        context["hike_date"] = hike_start_date
    else:
        # Default to today if not provided
        from datetime import date
        today = date.today().isoformat()
        context["hike_start_date"] = today
        context["hike_date"] = today
        form_values["hike_start_date"] = today
    
    if hike_end_date:
        context["hike_end_date"] = hike_end_date
        form_values["hike_end_date"] = hike_end_date
    else:
        # If no end date, use start date
        context["hike_end_date"] = context["hike_start_date"]
        form_values["hike_end_date"] = context["hike_start_date"]
    
    # Get days and hours to calculate time_available
    days_param = f"{prefix}_time_available_days"
    hours_param = f"{prefix}_time_available_hours"
    days = int(request_args.get(days_param, 0))
    hours = int(request_args.get(hours_param, 0))
    
    # Calculate time_available from date range if days/hours are 0 or not provided
    if days == 0 and hours == 0 and hike_start_date and hike_end_date:
        from datetime import datetime
        try:
            start = datetime.fromisoformat(hike_start_date)
            end = datetime.fromisoformat(hike_end_date)
            time_delta = end - start
            days = time_delta.days
            # If same day, default to 8 hours (full day hike)
            if days == 0:
                hours = 8
            else:
                hours = 0  # Multi-day, hours don't matter
        except (ValueError, TypeError):
            # If date parsing fails, default to 8 hours for single day
            if hike_start_date == hike_end_date:
                hours = 8
            else:
                days = 1
                hours = 0
    
    # Ensure minimum time_available (at least 1 hour for single day)
    if days == 0 and hours == 0:
        hours = 8  # Default to 8 hours for single day hike
    
    context["time_available"] = days * 24 * 60 + hours * 60
    form_values["time_available_days"] = str(days)
    form_values["time_available_hours"] = str(hours)
    
    # Auto-detect device from user agent (in background, not shown in UI)
    # Note: request is available in Flask request context
    try:
        user_agent = request.headers.get('User-Agent', '')
    except RuntimeError:
        # If not in request context, default to laptop
        user_agent = ''
    device = detect_device_from_user_agent(user_agent)
    context["device"] = device
    # Don't add device to form_values since it's not shown in UI
    
    # Auto-determine season from hike date (in background, not shown in UI)
    season = get_season_from_date(context.get("hike_start_date"))
    context["season"] = season
    # Don't add season to form_values since it's not shown in UI
    
    # Process other fields (weather, connection)
    for field in CONTEXT_FIELD_DEFS:
        name = field["name"]
        if name in ["hike_start_date", "hike_end_date", "time_available_days", "time_available_hours"]:
            continue  # Already handled above
            
        param_name = f"{prefix}_{name}"
        raw = request_args.get(param_name)
        if raw not in (None, ""):
            value = raw
        else:
            defaults = {
                "weather": "sunny",
                "connection": "strong",
            }
            value = defaults.get(name, "")
        
        context[name] = value
        form_values[name] = str(value)
    
    return context, form_values


def build_demo_result(user, context, user_label=None):
    """Build a demo result dictionary from user and context"""
    exact_matches, suggestions, display_settings, active_rules = adapt_trails(user, context)
    return {
        "scenario": {
            "title": f"{user.get('name', 'User')} · {user.get('experience', '')} profile",
            "description": "User-defined context",
            "user_id": user.get("id")
        },
        "user_id": user.get("id"),
        "user_label": user_label or f"User {user.get('id')}",
        "context": context,
        "exact": exact_matches,
        "suggestions": suggestions,
        "display": display_settings,
        "active_rules": active_rules,
    }


@app.route("/", methods=["GET", "POST"])
def index():
    """Home page - redirects to demo mode or processes form submission"""
    if request.method == "POST":
        user_id = request.form.get("user_id")
        if not user_id:
            return redirect(url_for("demo"))
        
        # Get form data
        hike_start_date = request.form.get("hike_start_date")
        hike_end_date = request.form.get("hike_end_date")
        time_available_days = request.form.get("time_available_days", "0")
        time_available_hours = request.form.get("time_available_hours", "1")
        device = request.form.get("device", "laptop")
        weather = request.form.get("weather", "sunny")
        connection = request.form.get("connection", "strong")
        # Get season from form, or determine from hike date, or use current season
        season = request.form.get("season")
        if not season:
            season = get_season_from_date(hike_start_date)
        
        # Build query string
        params = {
            "time_available_days": time_available_days,
            "time_available_hours": time_available_hours,
            "device": device,
            "weather": weather,
            "connection": connection,
            "season": season,
        }
        if hike_start_date:
            params["hike_start_date"] = hike_start_date
        if hike_end_date:
            params["hike_end_date"] = hike_end_date
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return redirect(url_for("recommendations", user_id=user_id) + "?" + query_string)
    
    return redirect(url_for("demo"))


@app.route("/recommendations/<int:user_id>")
def recommendations(user_id):
    """Adaptive trail recommendations page"""
    user = get_user(user_id)
    if not user:
        return "User not found", 404

    # Get hike date range
    hike_start_date = request.args.get("hike_start_date")
    hike_end_date = request.args.get("hike_end_date")
    if not hike_start_date:
        from datetime import date
        hike_start_date = date.today().isoformat()
    if not hike_end_date:
        hike_end_date = hike_start_date
    
    # Convert days and hours to minutes for internal processing
    days = int(request.args.get("time_available_days", 0))
    hours = int(request.args.get("time_available_hours", 1))
    time_available = days * 24 * 60 + hours * 60  # Convert to minutes
    
    device = request.args.get("device", "laptop")
    weather = request.args.get("weather", "sunny")
    connection = request.args.get("connection", "strong")
    # Get season from request, or determine from hike date, or use current season
    season = request.args.get("season")
    if not season:
        season = get_season_from_date(hike_start_date)

    context = {
        "hike_start_date": hike_start_date,
        "hike_end_date": hike_end_date,
        "hike_date": hike_start_date,  # For backward compatibility
        "time_available": time_available,
        "device": device,
        "weather": weather,
        "connection": connection,
        "season": season,
    }

    exact_matches, suggestions, display_settings, active_rules = adapt_trails(user, context)

    for trail in exact_matches:
        trail["view_type"] = "recommended"
    for trail in suggestions:
        trail["view_type"] = "suggested"

    combined_trails = exact_matches + suggestions
    
    # Get weather forecast summary for context display
    # Use the first trail's forecast as representative, or get a general forecast
    from backend.weather_service import get_weather_forecast
    context["forecast_weather"] = None
    if hike_start_date:
        # Try to get a representative forecast (using approximate French Alps center)
        # This gives a general idea of weather in the region
        try:
            representative_forecast = get_weather_forecast(45.5, 6.2, hike_start_date)
            context["forecast_weather"] = representative_forecast
        except:
            pass

    return render_template(
        "recommendations.html",
        user=user,
        context=context,
        exact_matches=exact_matches,
        suggestions=suggestions,
        display_settings=display_settings,
        active_rules=active_rules,
        combined_trails=combined_trails,
    )


@app.route("/trail/<int:user_id>/<trail_id>")
def trail_detail(user_id, trail_id):
    """Trail detail page"""
    user = get_user(user_id)
    if not user:
        return "User not found", 404

    trail = get_trail(trail_id)
    if not trail:
        return "Trail not found", 404

    # Get context from query params
    device = request.args.get("device", "laptop")
    connection = request.args.get("connection", "strong")
    weather = request.args.get("weather", "sunny")
    hike_start_date = request.args.get("hike_start_date")
    hike_end_date = request.args.get("hike_end_date")
    if not hike_start_date:
        from datetime import date
        hike_start_date = date.today().isoformat()
    if not hike_end_date:
        hike_end_date = hike_start_date
    # Convert days and hours to minutes for internal processing
    days = int(request.args.get("time_available_days", 0))
    hours = int(request.args.get("time_available_hours", 1))
    time_available = days * 24 * 60 + hours * 60  # Convert to minutes
    # Get season from request, or determine from hike date, or use current season
    season = request.args.get("season")
    if not season:
        season = get_season_from_date(hike_start_date)

    context = {
        "device": device,
        "connection": connection,
        "weather": weather,
        "hike_start_date": hike_start_date,
        "hike_end_date": hike_end_date,
        "hike_date": hike_start_date,  # For backward compatibility
        "time_available": time_available,
        "season": season,
    }

    # Check if user has completed this trail
    completed = any(ct["trail_id"] == trail_id for ct in user.get("completed_trails", []))

    return render_template(
        "trail_detail.html",
        user=user,
        trail=trail,
        context=context,
        completed=completed,
    )


@app.route("/trail/<int:user_id>/<trail_id>/complete", methods=["POST"])
def complete_trail(user_id, trail_id):
    """Record trail completion"""
    actual_duration = int(request.form.get("actual_duration", 0))
    rating = int(request.form.get("rating", 5))

    record_trail_completion(user_id, trail_id, actual_duration, rating)

    return redirect(url_for("trail_detail", user_id=user_id, trail_id=trail_id))


@app.route("/profile/<int:user_id>")
def profile(user_id):
    """User profile page"""
    user = get_user(user_id)
    if not user:
        return "User not found", 404

    return render_template("profile.html", user=user)


@app.route("/dashboard/<int:user_id>")
def dashboard(user_id):
    """User dashboard with statistics"""
    user = get_user(user_id)
    if not user:
        return "User not found", 404

    # Get all trails for statistics
    all_trails = get_all_trails()

    # Calculate statistics
    completed_trails = user.get("completed_trails", [])
    performance = user.get("performance", {})

    # Get trail details for completed trails
    completed_trail_details = []
    for ct in completed_trails:
        trail = get_trail(ct["trail_id"])
        if trail:
            trail_info = dict(trail)
            trail_info["completion_date"] = ct.get("completion_date")
            trail_info["rating"] = ct.get("rating")
            completed_trail_details.append(trail_info)

    # Get landscape preferences
    landscape_counts = {}
    for trail_id in [ct["trail_id"] for ct in completed_trails]:
        trail = get_trail(trail_id)
        if trail:
            landscapes = trail.get("landscapes", "").split(",")
            for landscape in landscapes:
                landscape_counts[landscape.strip()] = landscape_counts.get(landscape.strip(), 0) + 1

    return render_template(
        "dashboard.html",
        user=user,
        performance=performance,
        completed_trails=completed_trails,
        completed_trail_details=completed_trail_details,
        landscape_counts=landscape_counts,
    )


@app.route("/admin/rules")
def admin_rules():
    """Admin page to view all rules"""
    from backend.db import get_rules

    rules = get_rules()
    return render_template("admin_rules.html", rules=rules)


@app.route("/trails")
def all_trails():
    """Page showing all available trails in list and map views"""
    from datetime import date
    
    trails = get_all_trails()
    
    # Get optional date parameters for weather forecast
    hike_start_date = request.args.get("hike_start_date")
    hike_end_date = request.args.get("hike_end_date")
    
    # If no date specified, use today's date
    if not hike_start_date:
        hike_start_date = date.today().isoformat()
    if not hike_end_date:
        hike_end_date = hike_start_date
    
    # PERFORMANCE FIX: Don't fetch weather on initial page load
    # Weather will be loaded asynchronously via AJAX when user requests it
    # This makes the page load instantly instead of waiting for 50+ API calls
    for trail in trails:
        trail["forecast_weather"] = None
    
    return render_template(
        "all_trails.html", 
        trails=trails,
        hike_start_date=hike_start_date,
        hike_end_date=hike_end_date
    )


@app.route("/api/trails")
def api_trails():
    """Return all curated trails as JSON for the demo UI."""
    trails = get_all_trails()
    return jsonify({"trails": trails})


@app.route("/api/weather/batch")
def api_weather_batch():
    """
    Fetch weather forecasts for multiple trails in parallel.
    Much faster than sequential requests.
    
    Query params:
        - trail_ids: Comma-separated trail IDs
        - date: Target date (YYYY-MM-DD)
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from backend.weather_service import get_weather_forecast
    from datetime import date
    import time
    
    # Get parameters
    trail_ids_param = request.args.get("trail_ids", "")
    target_date = request.args.get("date")
    
    if not target_date:
        target_date = date.today().isoformat()
    
    # Parse trail IDs
    trail_ids = [tid.strip() for tid in trail_ids_param.split(",") if tid.strip()]
    
    if not trail_ids:
        return jsonify({"error": "No trail IDs provided"}), 400
    
    # Get trail data
    trails = get_all_trails()
    trail_dict = {str(t.get("trail_id")): t for t in trails}
    
    # Function to fetch weather for a single trail
    def fetch_trail_weather(trail_id):
        trail = trail_dict.get(trail_id)
        if not trail:
            return trail_id, None
        
        lat = trail.get("latitude")
        lon = trail.get("longitude")
        
        if not lat or not lon:
            return trail_id, None
        
        try:
            forecast = get_weather_forecast(float(lat), float(lon), target_date)
            return trail_id, forecast
        except Exception as e:
            print(f"Error fetching weather for trail {trail_id}: {e}")
            return trail_id, None
    
    # Fetch weather in parallel using thread pool
    # Max 20 concurrent requests to avoid overwhelming the API
    weather_results = {}
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        future_to_trail = {executor.submit(fetch_trail_weather, tid): tid for tid in trail_ids}
        
        for future in as_completed(future_to_trail):
            trail_id, forecast = future.result()
            weather_results[trail_id] = forecast
    
    elapsed = time.time() - start_time
    print(f"Fetched weather for {len(trail_ids)} trails in {elapsed:.2f}s")
    
    return jsonify({
        "weather": weather_results,
        "date": target_date,
        "elapsed_seconds": round(elapsed, 2)
    })


@app.route("/api/trail/<trail_id>")
def api_trail_detail(trail_id):
    """Return a single trail payload with elevation profile and geometry."""
    trail = get_trail(trail_id)
    if not trail:
        return jsonify({"error": "Trail not found"}), 404
    return jsonify(trail)


@app.route("/demo")
def demo():
    """Interactive demo page showing different context adaptations."""
    users = get_all_users()
    default_user_id = users[0]["id"] if users else None
    
    # Get user IDs for each scenario
    user_id_a_param = request.args.get("user_id_a")
    user_id_b_param = request.args.get("user_id_b")
    
    if user_id_a_param is not None:
        user_id_a = int(user_id_a_param)
    elif default_user_id is not None:
        user_id_a = int(default_user_id)
    else:
        user_id_a = None
    
    # Only set user_id_b if explicitly provided in the request
    # Don't use default - second user should only appear when explicitly added
    if user_id_b_param is not None:
        user_id_b = int(user_id_b_param)
    else:
        user_id_b = None

    user_a = get_user(user_id_a) if user_id_a is not None else None
    user_b = get_user(user_id_b) if user_id_b is not None else None

    if not user_a:
        return "No user data available to run demo", 500

    # Compare mode is determined by whether user_id_b is present
    compare_mode = user_id_b is not None

    # Check if there are any actual search parameters (context fields with prefix a_ or b_)
    # If there are no search parameters, don't perform a search - just show the form
    has_search_params = any(key.startswith("a_") or key.startswith("b_") for key in request.args.keys())
    
    context_a, form_a = extract_context_from_request("a", request.args)
    context_b, form_b = extract_context_from_request("b", request.args)

    # Only build results if search parameters are present
    primary_result = build_demo_result(user_a, context_a, user_label="User A") if has_search_params else None
    secondary_result = build_demo_result(user_b, context_b, user_label="User B") if has_search_params and compare_mode and user_b else None

    return render_template(
        "demo.html",
        users=users,
        selected_user_id_a=user_id_a,
        selected_user_id_b=user_id_b,
        selected_user_a=user_a,
        selected_user_b=user_b,
        primary_result=primary_result,
        secondary_result=secondary_result,
        compare_mode=compare_mode,
        context_fields=CONTEXT_FIELD_DEFS,
        context_form_values={"a": form_a, "b": form_b},
    )


@app.route("/api/demo/results", methods=["GET"])
def api_demo_results():
    """API endpoint to get demo results as JSON"""
    
    users = get_all_users()
    default_user_id = users[0]["id"] if users else None
    
    user_id_a_param = request.args.get("user_id_a")
    user_id_b_param = request.args.get("user_id_b")
    
    if user_id_a_param is not None:
        user_id_a = int(user_id_a_param)
    elif default_user_id is not None:
        user_id_a = int(default_user_id)
    else:
        return jsonify({"error": "No user data available"}), 500
    
    if user_id_b_param is not None:
        user_id_b = int(user_id_b_param)
    else:
        user_id_b = None
    
    user_a = get_user(user_id_a) if user_id_a is not None else None
    user_b = get_user(user_id_b) if user_id_b is not None else None
    
    if not user_a:
        return jsonify({"error": "No user data available"}), 500
    
    compare_mode = user_id_b is not None
    
    context_a, _ = extract_context_from_request("a", request.args)
    context_b, _ = extract_context_from_request("b", request.args)
    
    primary_result = build_demo_result(user_a, context_a, user_label="User A")
    secondary_result = build_demo_result(user_b, context_b, user_label="User B") if compare_mode and user_b else None

    return jsonify({
        "primary_result": primary_result,
        "secondary_result": secondary_result,
        "compare_mode": compare_mode
    })


def create_app():
    return app


__all__ = ["app", "create_app"]

