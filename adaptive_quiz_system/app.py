# -*- coding: utf-8 -*-

<<<<<<< HEAD
from flask import Flask, render_template, request, redirect, url_for, jsonify
from backend.db import (
    get_all_users, get_user, get_trail, get_all_trails,
    record_trail_view, record_trail_completion
)
from adapt_trails import adapt_trails
import json
=======
from flask import Flask, render_template, request, redirect, url_for
from backend.db import get_all_users, get_user, load_quiz
from adapt_quiz import adapt_quiz
>>>>>>> d04b8f65898e6e31c37e1228d779449922fdd635

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
<<<<<<< HEAD
    """Home page - user selection and context input"""
=======
>>>>>>> d04b8f65898e6e31c37e1228d779449922fdd635
    users = get_all_users()

    if request.method == "POST":
        user_id = int(request.form["user_id"])
<<<<<<< HEAD
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
=======
        time_available = int(request.form.get("time_available", 15))
        device = request.form.get("device", "desktop")

        return redirect(url_for("show_quiz", user_id=user_id, time_available=time_available, device=device))

    return render_template("index.html", users=users)

@app.route("/quiz/<int:user_id>")
def show_quiz(user_id):
>>>>>>> d04b8f65898e6e31c37e1228d779449922fdd635
    user = get_user(user_id)
    if not user:
        return "User not found", 404

<<<<<<< HEAD
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
=======
    time_available = int(request.args.get("time_available", 15))
    device = request.args.get("device", "desktop")

    context = {"time_available": time_available, "device": device}
    quiz_settings, allowed_quizzes = adapt_quiz(user, context)

    quizzes = []
    for q in allowed_quizzes:
        quizzes.append({"file": q + ".json", "title": q.replace("_", " ").title()})

    return render_template(
        "quiz.html",
        user=user,
        context=context,
        quiz_settings=quiz_settings,
        quizzes=quizzes
    )

@app.route("/quiz/<int:user_id>/<quiz_file>")
def play_quiz(user_id, quiz_file):
>>>>>>> d04b8f65898e6e31c37e1228d779449922fdd635
    user = get_user(user_id)
    if not user:
        return "User not found", 404

<<<<<<< HEAD
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
=======
    questions = load_quiz(quiz_file)
    return render_template("play_quiz.html", user=user, questions=questions)
>>>>>>> d04b8f65898e6e31c37e1228d779449922fdd635

if __name__ == "__main__":
    app.run(debug=True)
