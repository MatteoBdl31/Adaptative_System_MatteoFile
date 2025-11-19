# -*- coding: utf-8 -*-
import sqlite3
import os
<<<<<<< HEAD
import json
=======
>>>>>>> d04b8f65898e6e31c37e1228d779449922fdd635

BASE_DIR = os.path.dirname(__file__)
USERS_DB = os.path.join(BASE_DIR, "users.db")
RULES_DB = os.path.join(BASE_DIR, "rules.db")
<<<<<<< HEAD
TRAILS_DB = os.path.join(BASE_DIR, "trails.db")
TRAILS_DIR = os.path.join(BASE_DIR, "trails")
=======
>>>>>>> d04b8f65898e6e31c37e1228d779449922fdd635

# ----------------- Rules -----------------
conn = sqlite3.connect(RULES_DB)
cur = conn.cursor()
cur.execute("DROP TABLE IF EXISTS rules")
cur.execute("""
CREATE TABLE rules (
    rule_id INTEGER PRIMARY KEY,
    condition TEXT NOT NULL,
<<<<<<< HEAD
    adaptation TEXT NOT NULL,
    description TEXT
=======
    adaptation TEXT NOT NULL
>>>>>>> d04b8f65898e6e31c37e1228d779449922fdd635
)
""")

rules = [
<<<<<<< HEAD
    ("experience=Beginner AND time_available<=60",
     "max_difficulty=easy;max_distance=5;max_elevation=200",
     "Beginner with limited time: easy, short trails"),
    ("experience=Beginner AND weather=rainy",
     "max_difficulty=easy;landscape_preference=forest;avoid_risky=true",
     "Beginner in bad weather: safe forest trails"),
    ("experience=Advanced AND weather=sunny AND time_available>=120",
     "min_difficulty=hard;min_distance=10;prefer_peaks=true",
     "Advanced hiker, good weather, plenty of time: challenging peaks"),
    ("device=mobile",
     "display_mode=compact;max_trails=5",
     "Mobile device: compact display, fewer trails"),
    ("connection=weak",
     "display_mode=text_only;hide_images=true",
     "Weak connection: text-only, no images"),
    ("persistence_score<=0.5",
     "max_difficulty=medium;prefer_short=true;max_distance=8",
     "Low persistence: shorter, easier trails"),
    ("landscape_preference CONTAINS lake",
     "landscape_filter=lake",
     "User prefers lakes: filter for lake trails"),
    ("time_available<=45",
     "max_duration=45;max_distance=6",
     "Limited time: short trails under 45 min"),
    ("weather=storm_risk",
     "avoid_risky=true;max_elevation=500",
     "Storm risk: avoid dangerous high-elevation trails"),
    ("season=winter",
     "avoid_closed=true;prefer_safe=true",
     "Winter: avoid closed trails, prefer safe routes")
]

cur.executemany("INSERT INTO rules (condition, adaptation, description) VALUES (?, ?, ?)", rules)
conn.commit()
conn.close()
print("rules.db initialized with hiking rules")
=======
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
>>>>>>> d04b8f65898e6e31c37e1228d779449922fdd635

# ----------------- Users -----------------
conn = sqlite3.connect(USERS_DB)
cur = conn.cursor()
cur.execute("DROP TABLE IF EXISTS users")
cur.execute("DROP TABLE IF EXISTS preferences")
cur.execute("DROP TABLE IF EXISTS performance")
<<<<<<< HEAD
cur.execute("DROP TABLE IF EXISTS completed_trails")
cur.execute("DROP TABLE IF EXISTS trail_history")
=======
>>>>>>> d04b8f65898e6e31c37e1228d779449922fdd635

cur.execute("""
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT,
<<<<<<< HEAD
    experience TEXT,
    fitness_level TEXT,
    fear_of_heights INTEGER,
    health_constraints TEXT
=======
    level TEXT
>>>>>>> d04b8f65898e6e31c37e1228d779449922fdd635
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
<<<<<<< HEAD
    trails_completed INTEGER,
    avg_difficulty_completed REAL,
    persistence_score REAL,
    exploration_level REAL,
    avg_completion_time REAL,
    activity_frequency INTEGER,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")
cur.execute("""
CREATE TABLE completed_trails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    trail_id TEXT,
    completion_date TEXT,
    actual_duration INTEGER,
    rating INTEGER,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")
cur.execute("""
CREATE TABLE trail_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    trail_id TEXT,
    viewed_at TEXT,
    abandoned INTEGER,
=======
    avg_score REAL,
    attempts INTEGER,
    success_rate REAL,
>>>>>>> d04b8f65898e6e31c37e1228d779449922fdd635
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")

users = [
<<<<<<< HEAD
    (101, "Alice", "Advanced", "High", 0, None),
    (102, "Bob", "Beginner", "Medium", 1, None),
    (103, "Carol", "Intermediate", "High", 0, "Knee issues"),
    (104, "David", "Beginner", "Low", 1, "Back pain"),
    (105, "Emma", "Advanced", "High", 0, None),
    (106, "Frank", "Intermediate", "Medium", 0, "Asthma"),
    (107, "Grace", "Beginner", "Low", 0, None),
    (108, "Henry", "Advanced", "Medium", 1, None),
    (109, "Iris", "Intermediate", "Low", 0, "Knee issues"),
    (110, "Jack", "Beginner", "High", 1, None),
    (111, "Kate", "Advanced", "High", 0, None),
    (112, "Liam", "Intermediate", "Medium", 0, None),
    (113, "Mia", "Beginner", "Medium", 0, "Heart condition"),
    (114, "Noah", "Advanced", "High", 0, None),
    (115, "Olivia", "Intermediate", "High", 1, None)
]
cur.executemany("INSERT INTO users (id, name, experience, fitness_level, fear_of_heights, health_constraints) VALUES (?, ?, ?, ?, ?, ?)", users)

preferences = [
    (101, "lake"), (101, "peaks"),
    (102, "forest"), (102, "river"),
    (103, "lake"), (103, "mountain"),
    (104, "forest"), (104, "urban"),
    (105, "peaks"), (105, "alpine"), (105, "mountain"),
    (106, "lake"), (106, "forest"),
    (107, "river"), (107, "forest"),
    (108, "peaks"), (108, "mountain"),
    (109, "lake"), (109, "meadow"),
    (110, "forest"), (110, "river"),
    (111, "peaks"), (111, "alpine"), (111, "glacier"),
    (112, "lake"), (112, "mountain"),
    (113, "urban"), (113, "forest"),
    (114, "peaks"), (114, "alpine"), (114, "mountain"),
    (115, "lake"), (115, "peaks")
=======
    (101, "Alice", "Master"),
    (102, "Bob", "Beginner"),
    (103, "Carol", "Intermediate")
]
cur.executemany("INSERT INTO users (id, name, level) VALUES (?, ?, ?)", users)

preferences = [
    (101, "video"), (101, "quiz"),
    (102, "reading"),
    (103, "quiz"), (103, "audio")
>>>>>>> d04b8f65898e6e31c37e1228d779449922fdd635
]
cur.executemany("INSERT INTO preferences (user_id, preference) VALUES (?, ?)", preferences)

performance = [
<<<<<<< HEAD
    (101, 15, 7.5, 0.9, 0.8, 120, 8),
    (102, 3, 3.0, 0.4, 0.6, 45, 2),
    (103, 8, 5.5, 0.7, 0.7, 90, 5),
    (104, 2, 2.0, 0.3, 0.4, 30, 1),
    (105, 20, 8.5, 0.95, 0.9, 150, 10),
    (106, 6, 4.5, 0.6, 0.65, 75, 4),
    (107, 1, 2.5, 0.35, 0.5, 35, 1),
    (108, 12, 7.0, 0.85, 0.75, 110, 7),
    (109, 4, 3.5, 0.45, 0.55, 50, 3),
    (110, 2, 3.5, 0.5, 0.6, 40, 2),
    (111, 18, 8.0, 0.92, 0.85, 140, 9),
    (112, 7, 5.0, 0.65, 0.7, 85, 5),
    (113, 1, 2.0, 0.3, 0.45, 25, 1),
    (114, 22, 9.0, 0.98, 0.95, 160, 12),
    (115, 9, 6.0, 0.75, 0.75, 95, 6)
]
cur.executemany("INSERT INTO performance (user_id, trails_completed, avg_difficulty_completed, persistence_score, exploration_level, avg_completion_time, activity_frequency) VALUES (?, ?, ?, ?, ?, ?, ?)", performance)

completed_trails = [
    (101, "lake_serenity", "2024-01-15", 110, 5),
    (101, "mountain_peak_challenge", "2024-01-20", 180, 5),
    (102, "forest_walk_easy", "2024-01-10", 40, 4),
    (103, "lake_serenity", "2024-01-12", 95, 4),
    (104, "urban_park_loop", "2024-01-08", 25, 3),
    (105, "tour_du_mont_blanc", "2024-01-25", 150, 5),
    (105, "aiguilles_rouges", "2024-01-18", 140, 5),
    (106, "vallee_du_fier", "2024-01-11", 70, 4),
    (107, "forest_walk_easy", "2024-01-09", 32, 4),
    (108, "col_du_glandon", "2024-01-16", 105, 4),
    (109, "lac_de_serre_poncon", "2024-01-13", 48, 4),
    (110, "river_trail_moderate", "2024-01-14", 38, 4),
    (111, "lac_blanc_chamonix", "2024-01-22", 145, 5),
    (112, "alpine_lake_trek", "2024-01-17", 88, 4),
    (113, "urban_park_loop", "2024-01-07", 28, 3),
    (114, "mer_de_glace", "2024-01-24", 155, 5),
    (115, "waterfall_hike", "2024-01-19", 92, 4)
]
cur.executemany("INSERT INTO completed_trails (user_id, trail_id, completion_date, actual_duration, rating) VALUES (?, ?, ?, ?, ?)", completed_trails)

conn.commit()
conn.close()
print("users.db initialized with hiking user profiles")

# ----------------- Trails Database -----------------
conn = sqlite3.connect(TRAILS_DB)
cur = conn.cursor()
# Check if table exists and has data
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trails'")
table_exists = cur.fetchone()
if table_exists:
    cur.execute("SELECT COUNT(*) FROM trails")
    existing_count = cur.fetchone()[0]
    if existing_count > 0:
        print(f"Trails table already exists with {existing_count} trails. Skipping reinitialization.")
        print("To reinitialize, delete trails.db or run with --force flag")
        conn.close()
    else:
        cur.execute("DROP TABLE IF EXISTS trails")
else:
    cur.execute("DROP TABLE IF EXISTS trails")

cur.execute("""
CREATE TABLE trails (
    trail_id TEXT PRIMARY KEY,
    name TEXT,
    difficulty REAL,
    distance REAL,
    duration INTEGER,
    elevation_gain INTEGER,
    trail_type TEXT,
    landscapes TEXT,
    popularity REAL,
    safety_risks TEXT,
    accessibility TEXT,
    closed_seasons TEXT,
    description TEXT,
    latitude REAL,
    longitude REAL,
    coordinates TEXT
)
""")

# Sample trails data with enhanced coordinate paths (more points for realistic trail visualization)
trails_data = [
    ("tour_du_mont_blanc", "Tour du Mont Blanc", 8.5, 170.0, 12000, 10000, "loop", "peaks,mountain,alpine", 9.5, "rockfalls,steep,weather-dependent", "none", "winter", "Iconic 170km circuit around Mont Blanc, passing through France, Italy, and Switzerland. One of the world's most famous long-distance hikes.", 45.8326, 6.8652, '{"type":"LineString","coordinates":[[6.8652,45.8326],[6.8750,45.8380],[6.8900,45.8450],[6.9050,45.8520],[6.9200,45.8600],[6.9350,45.8680],[6.9500,45.8750],[6.9650,45.8820],[6.9800,45.8880],[6.9950,45.8930],[7.0100,45.8970],[7.0250,45.9000],[7.0400,45.9020],[7.0000,45.8800],[6.9800,45.8700],[6.9600,45.8600],[6.9400,45.8500],[6.9200,45.8400],[6.9000,45.8350],[6.8800,45.8330],[6.8652,45.8326]]}'),
    ("lac_blanc_chamonix", "Lac Blanc via Chamonix", 6.5, 12.0, 360, 1200, "one_way", "lake,peaks,alpine", 9.0, "steep,rocky", "none", "winter", "Stunning alpine lake hike starting from Chamonix. Breathtaking views of Mont Blanc massif and crystal-clear mountain lake.", 45.9237, 6.8694, '{"type":"LineString","coordinates":[[6.8694,45.9237],[6.8720,45.9280],[6.8750,45.9320],[6.8780,45.9360],[6.8800,45.9400],[6.8820,45.9440],[6.8840,45.9480],[6.8860,45.9520],[6.8880,45.9560],[6.8900,45.9600]]}'),
    ("aiguilles_rouges", "Aiguilles Rouges Nature Reserve", 7.0, 15.0, 480, 800, "loop", "peaks,alpine,meadow", 8.5, "steep,exposed", "none", "winter", "Challenging loop in the Aiguilles Rouges nature reserve with panoramic views of the Mont Blanc range.", 45.9500, 6.9000, '{"type":"LineString","coordinates":[[6.9000,45.9500],[6.9050,45.9520],[6.9100,45.9540],[6.9150,45.9560],[6.9200,45.9580],[6.9250,45.9600],[6.9300,45.9620],[6.9350,45.9640],[6.9400,45.9660],[6.9450,45.9680],[6.9400,45.9700],[6.9350,45.9680],[6.9300,45.9660],[6.9250,45.9640],[6.9200,45.9620],[6.9150,45.9600],[6.9100,45.9580],[6.9050,45.9560],[6.9000,45.9540],[6.9000,45.9500]]}'),
    ("mer_de_glace", "Mer de Glace Glacier Trail", 5.5, 8.0, 240, 600, "one_way", "glacier,alpine,mountain", 8.0, "slippery,glacier", "none", "winter", "Accessible trail to France's largest glacier. Includes ice cave visit and stunning glacier views.", 45.9333, 6.9167, '{"type":"LineString","coordinates":[[6.9167,45.9333],[6.9180,45.9350],[6.9200,45.9365],[6.9220,45.9380],[6.9240,45.9395],[6.9260,45.9410],[6.9280,45.9425],[6.9300,45.9440]]}'),
    ("lac_d_annecy", "Lac d'Annecy Circuit", 4.0, 40.0, 1200, 500, "loop", "lake,forest,urban", 8.5, "none", "dog-friendly,child-friendly", "", "Beautiful 40km circuit around Lake Annecy, one of France's most beautiful lakes. Mix of lakeside paths and forest trails.", 45.8992, 6.1294, '{"type":"LineString","coordinates":[[6.1294,45.8992],[6.1350,45.8995],[6.1400,45.8998],[6.1450,45.9000],[6.1500,45.9002],[6.1550,45.9004],[6.1600,45.9006],[6.1650,45.9008],[6.1700,45.9010],[6.1750,45.9012],[6.1800,45.9014],[6.1850,45.9016],[6.1900,45.9018],[6.1950,45.9020],[6.2000,45.9022],[6.2050,45.9020],[6.2100,45.9018],[6.2150,45.9016],[6.2200,45.9014],[6.2250,45.9012],[6.2300,45.9010],[6.2350,45.9008],[6.2400,45.9006],[6.2450,45.9004],[6.2500,45.9002],[6.2550,45.9000],[6.2600,45.8998],[6.2650,45.8996],[6.2700,45.8994],[6.1294,45.8992]]}'),
    ("vallee_du_fier", "Vallée du Fier", 3.5, 6.0, 180, 200, "loop", "river,forest", 7.5, "none", "dog-friendly,child-friendly", "", "Gentle walk along the Fier river gorge with suspension bridges and forest paths. Perfect for families.", 45.9000, 6.1000, '{"type":"LineString","coordinates":[[6.1000,45.9000],[6.1020,45.9010],[6.1040,45.9020],[6.1060,45.9030],[6.1080,45.9040],[6.1100,45.9050],[6.1120,45.9040],[6.1140,45.9030],[6.1160,45.9020],[6.1180,45.9010],[6.1200,45.9000],[6.1180,45.8990],[6.1160,45.8980],[6.1140,45.8970],[6.1120,45.8960],[6.1100,45.8950],[6.1080,45.8960],[6.1060,45.8970],[6.1040,45.8980],[6.1020,45.8990],[6.1000,45.9000]]}'),
    ("col_du_glandon", "Col du Glandon", 6.0, 14.0, 420, 1100, "one_way", "mountain,alpine,peaks", 8.0, "steep,exposed", "none", "winter", "Challenging mountain pass trail with spectacular alpine views. Popular with both hikers and cyclists.", 45.2500, 6.2000, '{"type":"LineString","coordinates":[[6.2000,45.2500],[6.2050,45.2520],[6.2100,45.2540],[6.2150,45.2560],[6.2200,45.2580],[6.2250,45.2600],[6.2300,45.2620],[6.2350,45.2640],[6.2400,45.2660],[6.2450,45.2680],[6.2500,45.2700]]}'),
    ("lac_de_serre_poncon", "Lac de Serre-Ponçon", 3.0, 5.0, 120, 150, "loop", "lake,forest", 7.0, "none", "dog-friendly,child-friendly", "", "Easy lakeside trail around one of France's largest artificial lakes. Great for swimming and picnics.", 44.5167, 6.3167, '{"type":"LineString","coordinates":[[6.3167,44.5167],[6.3200,44.5170],[6.3230,44.5175],[6.3260,44.5180],[6.3290,44.5185],[6.3320,44.5190],[6.3350,44.5195],[6.3380,44.5200],[6.3410,44.5195],[6.3440,44.5190],[6.3470,44.5185],[6.3500,44.5180],[6.3530,44.5175],[6.3560,44.5170],[6.3167,44.5167]]}'),
    ("forest_walk_easy", "Easy Forest Walk", 2.0, 3.0, 60, 50, "loop", "forest", 7.0, "none", "dog-friendly,child-friendly", "", "Gentle walk through peaceful forest", 45.8000, 6.0000, '{"type":"LineString","coordinates":[[6.0000,45.8000],[6.0020,45.8005],[6.0040,45.8010],[6.0060,45.8015],[6.0080,45.8020],[6.0100,45.8025],[6.0120,45.8020],[6.0140,45.8015],[6.0160,45.8010],[6.0180,45.8005],[6.0200,45.8000],[6.0180,45.7995],[6.0160,45.7990],[6.0140,45.7985],[6.0120,45.7980],[6.0100,45.7975],[6.0080,45.7980],[6.0060,45.7985],[6.0040,45.7990],[6.0020,45.7995],[6.0000,45.8000]]}'),
    ("mountain_peak_challenge", "Mountain Peak Challenge", 8.5, 12.0, 240, 1200, "one_way", "peaks,mountain", 9.0, "rockfalls,steep", "none", "", "Challenging ascent to mountain peak", 45.9000, 6.1000, '{"type":"LineString","coordinates":[[6.1000,45.9000],[6.1050,45.9050],[6.1100,45.9100],[6.1150,45.9150],[6.1200,45.9200],[6.1250,45.9250],[6.1300,45.9300],[6.1350,45.9350],[6.1400,45.9400]]}'),
    ("river_trail_moderate", "River Trail", 5.0, 6.5, 120, 300, "loop", "river,forest", 7.5, "slippery", "dog-friendly", "", "Scenic trail along river with forest views", 45.8500, 6.0800, '{"type":"LineString","coordinates":[[6.0800,45.8500],[6.0820,45.8520],[6.0840,45.8540],[6.0860,45.8560],[6.0880,45.8580],[6.0900,45.8600],[6.0920,45.8580],[6.0940,45.8560],[6.0960,45.8540],[6.0980,45.8520],[6.1000,45.8500],[6.0980,45.8480],[6.0960,45.8460],[6.0940,45.8440],[6.0920,45.8420],[6.0900,45.8400],[6.0880,45.8420],[6.0860,45.8440],[6.0840,45.8460],[6.0820,45.8480],[6.0800,45.8500]]}'),
    ("urban_park_loop", "City Park Loop", 2.5, 2.0, 30, 20, "loop", "urban", 6.5, "none", "dog-friendly,child-friendly,wheelchair-accessible", "", "Easy urban trail perfect for families", 45.7500, 6.0000, '{"type":"LineString","coordinates":[[6.0000,45.7500],[6.0010,45.7505],[6.0020,45.7510],[6.0030,45.7515],[6.0040,45.7520],[6.0050,45.7525],[6.0060,45.7520],[6.0070,45.7515],[6.0080,45.7510],[6.0090,45.7505],[6.0100,45.7500],[6.0090,45.7495],[6.0080,45.7490],[6.0070,45.7485],[6.0060,45.7480],[6.0050,45.7475],[6.0040,45.7480],[6.0030,45.7485],[6.0020,45.7490],[6.0010,45.7495],[6.0000,45.7500]]}'),
    ("alpine_lake_trek", "Alpine Lake Trek", 7.0, 10.0, 200, 800, "loop", "lake,peaks", 8.0, "weather-dependent", "none", "winter", "High-altitude lake with mountain views", 45.9200, 6.8500, '{"type":"LineString","coordinates":[[6.8500,45.9200],[6.8550,45.9250],[6.8600,45.9300],[6.8650,45.9350],[6.8700,45.9400],[6.8750,45.9350],[6.8800,45.9300],[6.8850,45.9250],[6.8900,45.9200],[6.8850,45.9150],[6.8800,45.9100],[6.8750,45.9050],[6.8700,45.9000],[6.8650,45.9050],[6.8600,45.9100],[6.8550,45.9150],[6.8500,45.9200]]}'),
    ("waterfall_hike", "Waterfall Hike", 4.5, 5.0, 100, 250, "one_way", "river,forest", 8.5, "slippery", "dog-friendly", "", "Popular trail leading to beautiful waterfall", 45.8500, 6.0500, '{"type":"LineString","coordinates":[[6.0500,45.8500],[6.0520,45.8520],[6.0540,45.8540],[6.0560,45.8560],[6.0580,45.8580],[6.0600,45.8600],[6.0620,45.8620],[6.0640,45.8640],[6.0660,45.8660],[6.0680,45.8680]]}')
]

cur.executemany("""
INSERT INTO trails (trail_id, name, difficulty, distance, duration, elevation_gain, trail_type, landscapes, popularity, safety_risks, accessibility, closed_seasons, description, latitude, longitude, coordinates)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", trails_data)

conn.commit()
conn.close()
print("trails.db initialized with sample trails")
=======
    (101, 72, 3, 0.65),
    (102, 40, 5, 0.30),
    (103, 85, 10, 0.80)
]
cur.executemany("INSERT INTO performance (user_id, avg_score, attempts, success_rate) VALUES (?, ?, ?, ?)", performance)

conn.commit()
conn.close()
print("users.db initialized with sample users")
>>>>>>> d04b8f65898e6e31c37e1228d779449922fdd635
