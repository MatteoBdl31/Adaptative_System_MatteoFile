# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, redirect, url_for
from backend.db import get_all_users, get_user, load_quiz
from adapt_quiz import adapt_quiz

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    users = get_all_users()

    if request.method == "POST":
        user_id = int(request.form["user_id"])
        time_available = int(request.form.get("time_available", 15))
        device = request.form.get("device", "desktop")

        return redirect(url_for("show_quiz", user_id=user_id, time_available=time_available, device=device))

    return render_template("index.html", users=users)

@app.route("/quiz/<int:user_id>")
def show_quiz(user_id):
    user = get_user(user_id)
    if not user:
        return "User not found", 404

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
    user = get_user(user_id)
    if not user:
        return "User not found", 404

    questions = load_quiz(quiz_file)
    return render_template("play_quiz.html", user=user, questions=questions)

if __name__ == "__main__":
    app.run(debug=True)
