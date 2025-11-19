from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, jsonify

from backend.db import (
    get_all_users,
    get_user,
    get_trail,
    get_all_trails,
    record_trail_view,
    record_trail_completion,
)
from adapt_trails import adapt_trails

BASE_DIR = Path(__file__).resolve().parent.parent

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static"),
)

DEMO_CONTEXTS = [
    {
        "id": "mobile_short_time",
        "title": "Mobile · 45 min · Rainy",
        "description": "Beginner user on a mobile phone, short timeframe and rainy weather. Perfect to showcase safer forest routes.",
        "context": {
            "time_available": 45,
            "device": "mobile",
            "weather": "rainy",
            "connection": "medium",
            "season": "spring",
            "time_of_day": "morning",
        },
    },
    {
        "id": "desktop_full_day",
        "title": "Desktop · 4h · Sunny Afternoon",
        "description": "Advanced profile planning a long hike with plenty of time and great weather.",
        "context": {
            "time_available": 240,
            "device": "desktop",
            "weather": "sunny",
            "connection": "strong",
            "season": "summer",
            "time_of_day": "afternoon",
        },
    },
    {
        "id": "weak_connection_winter",
        "title": "Tablet · 90 min · Winter & Weak signal",
        "description": "Intermediate user travelling with a tablet and weak network coverage during winter months.",
        "context": {
            "time_available": 90,
            "device": "tablet",
            "weather": "snowy",
            "connection": "weak",
            "season": "winter",
            "time_of_day": "morning",
        },
    },
    {
        "id": "evening_storm_risk",
        "title": "Mobile · Evening · Storm Risk",
        "description": "Demo of risk-aware filtering with evening start and potential storms.",
        "context": {
            "time_available": 120,
            "device": "mobile",
            "weather": "storm_risk",
            "connection": "medium",
            "season": "fall",
            "time_of_day": "evening",
        },
    },
]

CONTEXT_FIELD_DEFS = [
    {"name": "time_available", "label": "Time Available (min)", "type": "number", "min": 15, "step": 15},
    {"name": "device", "label": "Device", "type": "select", "options": ["desktop", "mobile", "tablet"]},
    {"name": "weather", "label": "Weather", "type": "select", "options": ["sunny", "cloudy", "rainy", "storm_risk", "snowy"]},
    {"name": "connection", "label": "Connection", "type": "select", "options": ["strong", "medium", "weak"]},
    {"name": "season", "label": "Season", "type": "select", "options": ["spring", "summer", "fall", "winter"]},
    {"name": "time_of_day", "label": "Time of Day", "type": "select", "options": ["morning", "afternoon", "evening"]},
]


def _get_demo_context(context_id):
    for scenario in DEMO_CONTEXTS:
        if scenario["id"] == context_id:
            return scenario
    return DEMO_CONTEXTS[0]


@app.route("/", methods=["GET", "POST"])
def index():
    """Home page - user selection and context input"""
    users = get_all_users()

    if request.method == "POST":
        user_id = int(request.form["user_id"])
        time_available = int(request.form.get("time_available", 60))
        device = request.form.get("device", "desktop")
        weather = request.form.get("weather", "sunny")
        connection = request.form.get("connection", "strong")
        season = request.form.get("season", "summer")
        time_of_day = request.form.get("time_of_day", "morning")

        return redirect(
            url_for(
                "recommendations",
                user_id=user_id,
                time_available=time_available,
                device=device,
                weather=weather,
                connection=connection,
                season=season,
                time_of_day=time_of_day,
            )
        )

    return render_template("index.html", users=users)


@app.route("/recommendations/<int:user_id>")
def recommendations(user_id):
    """Adaptive trail recommendations page"""
    user = get_user(user_id)
    if not user:
        return "User not found", 404

    time_available = int(request.args.get("time_available", 60))
    device = request.args.get("device", "desktop")
    weather = request.args.get("weather", "sunny")
    connection = request.args.get("connection", "strong")
    season = request.args.get("season", "summer")
    time_of_day = request.args.get("time_of_day", "morning")

    context = {
        "time_available": time_available,
        "device": device,
        "weather": weather,
        "connection": connection,
        "season": season,
        "time_of_day": time_of_day,
    }

    exact_matches, suggestions, display_settings, active_rules = adapt_trails(user, context)

    for trail in exact_matches:
        trail["view_type"] = "recommended"
    for trail in suggestions:
        trail["view_type"] = "suggested"

    combined_trails = exact_matches + suggestions

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

    # Record trail view
    record_trail_view(user_id, trail_id)

    # Get context from query params
    device = request.args.get("device", "desktop")
    connection = request.args.get("connection", "strong")
    weather = request.args.get("weather", "sunny")
    time_available = int(request.args.get("time_available", 60))
    season = request.args.get("season", "summer")
    time_of_day = request.args.get("time_of_day", "morning")

    context = {
        "device": device,
        "connection": connection,
        "weather": weather,
        "time_available": time_available,
        "season": season,
        "time_of_day": time_of_day,
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
    trails = get_all_trails()
    return render_template("all_trails.html", trails=trails)


@app.route("/api/trails")
def api_trails():
    """Return all curated trails as JSON for the demo UI."""
    trails = get_all_trails()
    return jsonify({"trails": trails})


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
    user_id_param = request.args.get("user_id")
    if user_id_param is not None:
        user_id = int(user_id_param)
    elif default_user_id is not None:
        user_id = int(default_user_id)
    else:
        user_id = None

    user = get_user(user_id) if user_id is not None else None

    if not user:
        return "No user data available to run demo", 500

    compare_mode = request.args.get("compare", "0") == "1"
    preset_a = request.args.get("scenario_preset_a", DEMO_CONTEXTS[0]["id"])
    preset_b_default = DEMO_CONTEXTS[1]["id"] if len(DEMO_CONTEXTS) > 1 else DEMO_CONTEXTS[0]["id"]
    preset_b = request.args.get("scenario_preset_b", preset_b_default)

    primary_scenario = _get_demo_context(preset_a)
    secondary_scenario = _get_demo_context(preset_b)

    def extract_context(prefix, base_context):
        context = {}
        form_values = {}
        for field in CONTEXT_FIELD_DEFS:
            name = field["name"]
            param_name = f"{prefix}_{name}"
            raw = request.args.get(param_name)
            value = raw if raw not in (None, "") else base_context.get(name)
            if name == "time_available":
                value = int(value)
            context[name] = value
            form_values[name] = str(value)
        return context, form_values

    context_a, form_a = extract_context("a", primary_scenario["context"])
    context_b, form_b = extract_context("b", secondary_scenario["context"])

    def build_result(scenario_meta, context):
        exact_matches, suggestions, display_settings, active_rules = adapt_trails(user, context)
        return {
            "scenario": scenario_meta,
            "context": context,
            "exact": exact_matches,
            "suggestions": suggestions,
            "display": display_settings,
            "active_rules": active_rules,
        }

    primary_result = build_result(primary_scenario, context_a)
    secondary_result = build_result(secondary_scenario, context_b) if compare_mode else None

    comparison_summary = None
    if compare_mode and secondary_result:
        set_primary = {trail["trail_id"] for trail in primary_result["exact"]}
        set_secondary = {trail["trail_id"] for trail in secondary_result["exact"]}
        overlap = set_primary & set_secondary
        comparison_summary = {
            "primary_unique": len(set_primary - set_secondary),
            "secondary_unique": len(set_secondary - set_primary),
            "overlap": len(overlap),
        }

    return render_template(
        "demo.html",
        users=users,
        selected_user_id=user_id,
        scenarios=DEMO_CONTEXTS,
        primary_result=primary_result,
        secondary_result=secondary_result,
        compare_mode=compare_mode,
        comparison_summary=comparison_summary,
        context_fields=CONTEXT_FIELD_DEFS,
        context_form_values={"a": form_a, "b": form_b},
        preset_a=preset_a,
        preset_b=preset_b,
    )


def create_app():
    return app


__all__ = ["app", "create_app"]

