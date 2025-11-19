# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, redirect, url_for, jsonify
from backend.db import (
    get_all_users, get_user, get_trail, get_all_trails,
    record_trail_view, record_trail_completion
)
from adapt_trails import adapt_trails
import json

app = Flask(__name__)

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

        return redirect(url_for("recommendations", 
            user_id=user_id, 
            time_available=time_available, 
            device=device,
            weather=weather,
            connection=connection,
            season=season,
            time_of_day=time_of_day
        ))

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
        "time_of_day": time_of_day
    }

    exact_matches, suggestions, display_settings, active_rules = adapt_trails(user, context)

    return render_template(
        "recommendations.html",
        user=user,
        context=context,
        exact_matches=exact_matches,
        suggestions=suggestions,
        display_settings=display_settings,
        active_rules=active_rules
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

    context = {
        "device": device,
        "connection": connection,
        "weather": weather
    }

    # Check if user has completed this trail
    completed = any(ct["trail_id"] == trail_id for ct in user.get("completed_trails", []))

    return render_template(
        "trail_detail.html",
        user=user,
        trail=trail,
        context=context,
        completed=completed
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
        landscape_counts=landscape_counts
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

if __name__ == "__main__":
    app.run(debug=True)
