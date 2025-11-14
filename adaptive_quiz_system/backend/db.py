# -*- coding: utf-8 -*-

import sqlite3
import json
import os

BASE_DIR = os.path.dirname(__file__)
USERS_DB = os.path.join(BASE_DIR, "users.db")
RULES_DB = os.path.join(BASE_DIR, "rules.db")
QUIZZES_DIR = os.path.join(BASE_DIR, "quizzes")

# --- Users ---
def get_all_users():
    conn = sqlite3.connect(USERS_DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM users")
    users = [dict(row) for row in cur.fetchall()]
    # ajouter préférences et performance
    for user in users:
        cur.execute("SELECT preference FROM preferences WHERE user_id=?", (user["id"],))
        user["preferences"] = [row["preference"] for row in cur.fetchall()]
        cur.execute("SELECT * FROM performance WHERE user_id=?", (user["id"],))
        perf = cur.fetchone()
        user["performance"] = dict(perf) if perf else {}
    conn.close()
    return users

def get_user(user_id):
    conn = sqlite3.connect(USERS_DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id=?", (user_id,))
    row = cur.fetchone()
    if not row:
        return None
    user = dict(row)
    cur.execute("SELECT preference FROM preferences WHERE user_id=?", (user_id,))
    user["preferences"] = [row["preference"] for row in cur.fetchall()]
    cur.execute("SELECT * FROM performance WHERE user_id=?", (user_id,))
    perf = cur.fetchone()
    user["performance"] = dict(perf) if perf else {}
    conn.close()
    return user

# --- Rules ---
def get_rules():
    conn = sqlite3.connect(RULES_DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM rules")
    rules = [dict(row) for row in cur.fetchall()]
    conn.close()
    return rules

# --- Quiz files ---
def get_all_quizzes():
    return [f for f in os.listdir(QUIZZES_DIR) if f.endswith(".json")]

def load_quiz(quiz_file):
    path = os.path.join(QUIZZES_DIR, quiz_file)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
