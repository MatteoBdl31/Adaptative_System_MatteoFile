# -*- coding: utf-8 -*-
import sqlite3
import os

BASE_DIR = os.path.dirname(__file__)
USERS_DB = os.path.join(BASE_DIR, "users.db")
RULES_DB = os.path.join(BASE_DIR, "rules.db")

# ----------------- Rules -----------------
conn = sqlite3.connect(RULES_DB)
cur = conn.cursor()
cur.execute("DROP TABLE IF EXISTS rules")
cur.execute("""
CREATE TABLE rules (
    rule_id INTEGER PRIMARY KEY,
    condition TEXT NOT NULL,
    adaptation TEXT NOT NULL
)
""")

rules = [
    ("level=Beginner AND time_available<=10",
     "difficulty=easy;questions=5;allowed_quizzes=math_basics,culture_general"),
    ("level=Master AND performance.avg_score>=70",
     "difficulty=hard;questions=15;timer=true;allowed_quizzes=math_advanced,culture_pop,history"),
    ("level=Intermediate",
     "difficulty=medium;questions=10;allowed_quizzes=science,languages")
]

cur.executemany("INSERT INTO rules (condition, adaptation) VALUES (?, ?)", rules)
conn.commit()
conn.close()
print("rules.db initialized")

# ----------------- Users -----------------
conn = sqlite3.connect(USERS_DB)
cur = conn.cursor()
cur.execute("DROP TABLE IF EXISTS users")
cur.execute("DROP TABLE IF EXISTS preferences")
cur.execute("DROP TABLE IF EXISTS performance")

cur.execute("""
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT,
    level TEXT
)
""")
cur.execute("""
CREATE TABLE preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    preference TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")
cur.execute("""
CREATE TABLE performance (
    user_id INTEGER PRIMARY KEY,
    avg_score REAL,
    attempts INTEGER,
    success_rate REAL,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")

users = [
    (101, "Alice", "Master"),
    (102, "Bob", "Beginner"),
    (103, "Carol", "Intermediate")
]
cur.executemany("INSERT INTO users (id, name, level) VALUES (?, ?, ?)", users)

preferences = [
    (101, "video"), (101, "quiz"),
    (102, "reading"),
    (103, "quiz"), (103, "audio")
]
cur.executemany("INSERT INTO preferences (user_id, preference) VALUES (?, ?)", preferences)

performance = [
    (101, 72, 3, 0.65),
    (102, 40, 5, 0.30),
    (103, 85, 10, 0.80)
]
cur.executemany("INSERT INTO performance (user_id, avg_score, attempts, success_rate) VALUES (?, ?, ?, ?)", performance)

conn.commit()
conn.close()
print("users.db initialized with sample users")
