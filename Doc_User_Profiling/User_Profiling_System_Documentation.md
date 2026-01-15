# User Profiling System Documentation

**Adaptive Trails - Hiking Recommendation System**

Version: 1.0  
Date: 2024  
Author: Adaptive Trails Development Team

---

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [User Profiles](#user-profiles)
4. [Profile Detection Algorithm](#profile-detection-algorithm)
5. [Scoring Methodology](#scoring-methodology)
6. [Database Schema](#database-schema)
7. [Implementation Details](#implementation-details)
8. [Usage Examples](#usage-examples)
9. [Limitations and Future Improvements](#limitations-and-future-improvements)

---

## 1. Overview

The User Profiling System is an intelligent component of the Adaptive Trails hiking recommendation platform that automatically detects user behavioral profiles based on their historical trail completion data. The system analyzes patterns in completed hikes to classify users into one of seven distinct profile categories, enabling personalized trail recommendations.

### Key Features

- **Automatic Profile Detection**: Profiles are calculated automatically from user trail history
- **Data-Driven**: Based on statistical analysis of completed trails
- **Non-Intrusive**: No explicit user input required for profile detection
- **Dynamic Updates**: Profiles are recalculated as users complete more trails
- **Deterministic**: Ensures a single profile per user, even with equal scores

### Requirements

- Minimum 3 completed trails required for profile detection
- Trail data must include: distance, elevation gain, difficulty, duration, landscapes, safety risks, trail type, and popularity

---

## 2. System Architecture

### Components

```
User Profiling System
├── UserProfiler Class
│   ├── calculate_statistics()
│   ├── detect_profile()
│   └── _score_profiles()
├── Database Layer
│   ├── user_profiles table
│   └── completed_trails table
└── Integration Points
    ├── record_trail_completion()
    └── get_user() / get_all_users()
```

### Data Flow

1. **Trail Completion** → User completes a trail
2. **Data Collection** → Trail completion is recorded in `completed_trails` table
3. **Statistics Calculation** → System calculates statistics from user's trail history
4. **Profile Scoring** → Each of the 7 profiles is scored based on statistics
5. **Profile Selection** → Highest scoring profile is selected (with tie-breaking)
6. **Storage** → Profile is stored in `user_profiles` table
7. **Display** → Profile is displayed in user interface

---

## 3. User Profiles

The system recognizes seven distinct user profiles, each representing different hiking behaviors and preferences.

### 3.1 Elevation Enthusiast (L'Amateur de dénivelé)

**Key Characteristics:**
- Seeks challenging elevation gains
- Prefers difficult trails with significant altitude changes
- Less concerned about trail distance
- Enjoys mountain climbing and high-altitude hiking

**Detection Criteria:**
- High median elevation gain (≥400m, optimal ≥600m)
- High difficulty level (mean ≥6.0)
- Distance is less important if elevation is high

**Typical Trail Features:**
- Elevation gain: 600-1000m+
- Difficulty: 6.5-8.5/10
- Distance: Variable (less important)

---

### 3.2 Performance Athlete (Le Sportif de performance)

**Key Characteristics:**
- Focuses on long-distance, endurance hiking
- Prefers consistent, challenging routes
- Values loop trails for training
- Seeks performance metrics and consistency

**Detection Criteria:**
- Long distance trails (mean ≥8.0 km)
- Long duration (mean ≥90 minutes)
- Low variance in difficulty (consistent training)
- Preference for loop trails

**Typical Trail Features:**
- Distance: 8-15+ km
- Duration: 90-180+ minutes
- Trail type: Loops preferred
- Difficulty: Moderate to high, consistent

---

### 3.3 Contemplative Hiker (Le Contemplatif)

**Key Characteristics:**
- Seeks scenic, picturesque landscapes
- Prefers popular, well-known trails
- Values visual beauty over physical challenge
- Enjoys lakes, peaks, and glaciers

**Detection Criteria:**
- Strong preference for scenic landscapes (lake, peaks, glacier)
- Moderate to high popularity (6.0-7.5 optimal)
- At least 50% of trails should have contemplative landscapes

**Typical Trail Features:**
- Landscapes: Lake, peaks, glacier (not just alpine)
- Popularity: 6.0-8.0
- Difficulty: Variable
- Focus on visual appeal

---

### 3.4 Casual Hiker (Le Randonneur occasionnel)

**Key Characteristics:**
- Prefers shorter, easier trails
- Values convenience and accessibility
- Less frequent hiking activity
- Safety-conscious

**Detection Criteria:**
- Short distance (mean ≤6.0 km, optimal ≤5.0 km)
- Low difficulty (mean ≤5.0, optimal ≤4.5)
- High safety (no risks preferred)

**Typical Trail Features:**
- Distance: 3-6 km
- Difficulty: 3.0-5.0/10
- Safety: No risks
- Duration: 30-60 minutes

---

### 3.5 Family / Group Hiker (La Famille / Groupe hétérogène)

**Key Characteristics:**
- Seeks trails suitable for groups with varying abilities
- Prioritizes safety and accessibility
- Values variety in landscapes
- Moderate difficulty preferred

**Detection Criteria:**
- Low to moderate difficulty (mean ≤5.0, optimal ≤4.0)
- High safety (≥70% trails with no risks)
- Variety in landscapes (multiple types)
- Moderate distance (≤8.0 km)

**Typical Trail Features:**
- Difficulty: 3.0-4.5/10
- Safety: No risks
- Distance: 4-8 km
- Landscapes: Varied

---

### 3.6 Explorer / Adventurer (L'Explorateur / Aventurier)

**Key Characteristics:**
- Seeks less popular, off-the-beaten-path trails
- Accepts higher risks
- Prefers rare landscapes (glaciers, alpine)
- Values adventure over comfort

**Detection Criteria:**
- Low popularity (below dataset average, <8.0)
- Presence of rare landscapes (glacier, alpine)
- Some risk acceptance (not all trails risk-free)
- Preference for less-known routes

**Typical Trail Features:**
- Popularity: <7.5 (below average)
- Landscapes: Glacier, alpine
- Safety: Some risks accepted
- Difficulty: Variable

---

### 3.7 Photographer / Content Creator (Le Photographe / Créateur de contenu)

**Key Characteristics:**
- Focuses on photogenic trails
- Prefers one-way routes for better photo opportunities
- Values scenic landscapes (lakes, peaks)
- Flexible duration (not too short, not too long)

**Detection Criteria:**
- Strong preference for target landscapes (lake, peaks)
- One-way trail preference
- Flexible duration (45-300 minutes optimal)
- At least 60% of trails should have target landscapes

**Typical Trail Features:**
- Landscapes: Lake, peaks (≥60%)
- Trail type: One-way preferred
- Duration: 45-300 minutes
- Focus on photo opportunities

---

## 4. Profile Detection Algorithm

### 4.1 Process Overview

The profile detection process follows these steps:

1. **Data Collection**: Retrieve all completed trails for the user
2. **Statistics Calculation**: Compute aggregate statistics from trail data
3. **Profile Scoring**: Score each of the 7 profiles based on statistics
4. **Profile Selection**: Select the profile with the highest score
5. **Tie-Breaking**: If multiple profiles have the same score, use priority order

### 4.2 Statistics Calculated

For each user, the system calculates:

- **Distance Statistics**: Mean, median, quartiles
- **Elevation Gain Statistics**: Mean, median, quartiles
- **Difficulty Statistics**: Mean, median, standard deviation, quartiles
- **Duration Statistics**: Mean, median, quartiles
- **Landscape Frequencies**: Percentage of each landscape type
- **Safety Risk Distribution**: Percentage of each risk level
- **Trail Type Distribution**: Percentage of loops vs one-way
- **Average Popularity**: Mean popularity score
- **Trail Count**: Total number of completed trails

### 4.3 Profile Selection Logic

```python
def detect_profile(user_id):
    # 1. Calculate statistics
    stats = calculate_statistics(user_id)
    
    # 2. Check minimum requirements
    if stats.trail_count < 3:
        return None
    
    # 3. Score all profiles
    scores = score_profiles(stats)
    
    # 4. Find maximum score
    max_score = max(scores.values())
    
    # 5. Get all profiles with max score
    profiles_with_max = [p for p, s in scores.items() if s == max_score]
    
    # 6. If tie, use priority order
    if len(profiles_with_max) > 1:
        return select_by_priority(profiles_with_max)
    else:
        return profiles_with_max[0]
```

### 4.4 Tie-Breaking Priority Order

When multiple profiles have the same score, the following priority order is used:

1. Elevation Enthusiast
2. Performance Athlete
3. Explorer
4. Photographer
5. Contemplative
6. Family
7. Casual

This ensures deterministic profile selection.

---

## 5. Scoring Methodology

### 5.1 General Scoring Approach

Each profile is scored on a scale from 0.0 to 1.0+ (scores can exceed 1.0 with boosts). The scoring uses weighted combinations of normalized statistics, with specific criteria for each profile type.

### 5.2 Elevation Enthusiast Scoring

```
elev_score = min(1.0, elev_median / 400.0)
diff_score = min(1.0, difficulty_mean / 10.0)
distance_penalty = 0 if elev_median > 400 else min(0.2, (distance_mean / 12.0) * 0.2)

if elev_median > 600 and difficulty_mean > 6.0:
    score = (elev_score * 0.6 + diff_score * 0.4 - distance_penalty) * 1.1
else:
    score = (elev_score * 0.5 + diff_score * 0.4 - distance_penalty)
```

**Weights:**
- Elevation: 50-60%
- Difficulty: 40%
- Distance: Penalty (0-20%)

---

### 5.3 Performance Athlete Scoring

```
distance_score = min(1.0, distance_mean / 10.0)
duration_score = min(1.0, duration_mean / 120.0)
variance_score = max(0.4, 1.0 - (difficulty_std / 5.0))
loop_bonus = loop_ratio * 0.2

if distance_mean > 8.0 and duration_mean > 90:
    score = (distance_score * 0.4 + duration_score * 0.4 + 
             variance_score * 0.15 + loop_bonus) * 1.1
else:
    score = (distance_score * 0.35 + duration_score * 0.35 + 
             variance_score * 0.2 + loop_bonus)
```

**Weights:**
- Distance: 35-40%
- Duration: 35-40%
- Consistency (low variance): 15-20%
- Loop preference: 0-20% bonus

---

### 5.4 Contemplative Hiker Scoring

```
contemplative_landscapes = ["lake", "peaks", "glacier"]
contemplative_score = sum(landscapes.get(l, 0) for l in contemplative_landscapes)
popularity_score = 1.0 if 6.0 <= popularity <= 7.5 else 
                   (0.6 if 5.0 <= popularity <= 8.5 else 0.3)

if contemplative_score >= 0.5:
    score = contemplative_score * 0.5 + popularity_score * 0.5
else:
    score = (contemplative_score * 0.5 + popularity_score * 0.5) * 0.7
```

**Weights:**
- Landscape preference: 50%
- Popularity: 50%
- Penalty if landscape score < 0.5

---

### 5.5 Casual Hiker Scoring

```
distance_score = max(0, 1.0 - (distance_mean / 7.0))
difficulty_score = max(0, 1.0 - (difficulty_mean / 6.0))

if distance_mean < 6.0 and difficulty_mean < 5.0:
    score = (distance_score * 0.45 + difficulty_score * 0.45 + 
             safety_none * 0.1) * 1.3
elif distance_mean < 7.0 and difficulty_mean < 6.0:
    score = (distance_score * 0.4 + difficulty_score * 0.4 + 
             safety_none * 0.2) * 1.15
else:
    score = distance_score * 0.4 + difficulty_score * 0.4 + safety_none * 0.2
```

**Weights:**
- Short distance preference: 40-45%
- Low difficulty preference: 40-45%
- Safety: 10-20%
- Boost for very short/easy trails

---

### 5.6 Family / Group Hiker Scoring

```
difficulty_score = max(0, 1.0 - (difficulty_mean / 5.0))
variety_score = min(1.0, landscapes_count / 2.5)

if difficulty_mean < 5.0 and safety_none > 0.7:
    score = (difficulty_score * 0.45 + safety_none * 0.45 + 
             variety_score * 0.1) * 1.25
elif difficulty_mean < 5.5 and safety_none > 0.6:
    score = (difficulty_score * 0.4 + safety_none * 0.4 + 
             variety_score * 0.2) * 1.15
else:
    score = difficulty_score * 0.4 + safety_none * 0.4 + variety_score * 0.2
```

**Weights:**
- Low difficulty: 40-45%
- High safety: 40-45%
- Landscape variety: 10-20%
- Boost for very safe/easy trails

---

### 5.7 Explorer / Adventurer Scoring

```
rare_landscapes = ["glacier", "alpine"]
rare_score = sum(landscapes.get(l, 0) for l in rare_landscapes)
risk_acceptance = 1.0 - safety_risks.get("none", 1.0)
popularity_score = max(0, 1.0 - ((popularity - 7.0) / 2.0))

if popularity < 8.0:
    score = (popularity_score * 0.5 + rare_score * 0.35 + 
             risk_acceptance * 0.15) * 1.2
else:
    score = popularity_score * 0.4 + rare_score * 0.35 + risk_acceptance * 0.25
```

**Weights:**
- Low popularity: 40-50%
- Rare landscapes: 35%
- Risk acceptance: 15-25%
- Boost for low popularity

---

### 5.8 Photographer / Content Creator Scoring

```
target_landscapes = ["lake", "peaks"]
target_score = sum(landscapes.get(l, 0) for l in target_landscapes)
duration_flexibility = 1.0 if 45 <= duration_mean <= 300 else 
                      (0.7 if 30 <= duration_mean <= 360 else 0.4)

if target_score > 0.6:
    score = target_score * 0.5 + one_way_ratio * 0.3 + duration_flexibility * 0.2
else:
    score = (target_score * 0.4 + one_way_ratio * 0.3 + 
             duration_flexibility * 0.3) * 0.8
```

**Weights:**
- Target landscapes: 40-50%
- One-way preference: 30%
- Duration flexibility: 20-30%
- Penalty if target score < 0.6

---

## 6. Database Schema

### 6.1 user_profiles Table

```sql
CREATE TABLE user_profiles (
    user_id INTEGER PRIMARY KEY,
    primary_profile TEXT,
    profile_scores TEXT,
    last_updated TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
```

**Fields:**
- `user_id`: Primary key, references users table
- `primary_profile`: The detected profile key (e.g., "elevation_lover")
- `profile_scores`: JSON string containing all profile scores
- `last_updated`: ISO timestamp of last profile calculation

**Constraints:**
- One profile per user (enforced by PRIMARY KEY)
- Profile is recalculated on each trail completion

### 6.2 completed_trails Table

```sql
CREATE TABLE completed_trails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    trail_id TEXT,
    completion_date TEXT,
    actual_duration INTEGER,
    rating INTEGER,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
```

**Fields:**
- `user_id`: References the user
- `trail_id`: References the trail
- `completion_date`: ISO date string
- `actual_duration`: Duration in minutes
- `rating`: User rating (1-5)

### 6.3 Data Relationships

```
users (1) ──< (many) completed_trails
users (1) ──< (1) user_profiles
trails (1) ──< (many) completed_trails
```

---

## 7. Implementation Details

### 7.1 Class Structure

**UserProfiler Class**

```python
class UserProfiler:
    def calculate_statistics(user_id: int) -> Dict
    def detect_profile(user_id: int) -> Tuple[Optional[str], Dict]
    def _score_profiles(stats: Dict) -> Dict[str, float]
    def _calc_stats(values: List[float]) -> Dict
    def _calc_landscape_freq(trails: List[Dict]) -> Dict
    def _calc_safety_distribution(trails: List[Dict]) -> Dict
    def _calc_trail_type_distribution(trails: List[Dict]) -> Dict
```

### 7.2 Integration Points

**Automatic Profile Updates**

Profiles are automatically recalculated when:
- A user completes a trail (`record_trail_completion()`)
- A user profile is requested (`get_user()` or `get_all_users()`)

**Manual Profile Calculation**

```python
from backend.user_profiling import UserProfiler
from backend.db import update_user_profile

profiler = UserProfiler()
primary_profile, scores = profiler.detect_profile(user_id)
if primary_profile:
    update_user_profile(user_id, primary_profile, scores)
```

### 7.3 Performance Considerations

- **Caching**: Profiles are stored in database to avoid recalculation
- **Lazy Calculation**: Profiles calculated on-demand if not in database
- **Minimum Threshold**: Only calculates if user has ≥3 completed trails
- **Direct Database Access**: Avoids circular imports by querying database directly

---

## 8. Usage Examples

### 8.1 Getting User Profile

```python
from backend.db import get_user

user = get_user(user_id=101)
print(f"Profile: {user['detected_profile']}")
print(f"Scores: {user['profile_scores']}")
```

### 8.2 Recalculating All Profiles

```python
from backend.user_profiling import UserProfiler
from backend.db import get_all_users, update_user_profile

profiler = UserProfiler()
users = get_all_users()

for user in users:
    if len(user.get("completed_trails", [])) >= 3:
        primary, scores = profiler.detect_profile(user["id"])
        if primary:
            update_user_profile(user["id"], primary, scores)
```

### 8.3 Checking Profile Statistics

```python
from backend.user_profiling import UserProfiler

profiler = UserProfiler()
stats = profiler.calculate_statistics(user_id=101)

print(f"Trail count: {stats['trail_count']}")
print(f"Average distance: {stats['distance']['mean']:.2f} km")
print(f"Average elevation: {stats['elevation_gain']['mean']:.0f} m")
print(f"Landscapes: {stats['landscapes']}")
```

### 8.4 Profile Distribution Analysis

```python
from backend.db import get_all_users

users = get_all_users()
profile_distribution = {}

for user in users:
    profile = user.get("detected_profile")
    if profile:
        profile_distribution[profile] = profile_distribution.get(profile, 0) + 1

for profile, count in sorted(profile_distribution.items(), key=lambda x: x[1], reverse=True):
    print(f"{profile}: {count} users")
```

---

## 9. Limitations and Future Improvements

### 9.1 Current Limitations

1. **Minimum Trail Requirement**: Requires at least 3 completed trails
   - Users with fewer trails cannot be profiled
   - Solution: Could use explicit preferences or quiz data

2. **Data Quality Dependency**: Profile accuracy depends on trail data quality
   - Missing or incorrect trail attributes affect scoring
   - Solution: Data validation and quality checks

3. **Static Scoring Weights**: Weights are fixed and not adaptive
   - May not work well for all user populations
   - Solution: Machine learning-based weight optimization

4. **Single Profile Limitation**: Users can only have one profile
   - Some users may exhibit mixed behaviors
   - Solution: Multi-profile support with confidence scores

5. **No Temporal Analysis**: Doesn't consider profile evolution over time
   - User preferences may change
   - Solution: Time-weighted statistics and profile history

### 9.2 Future Improvements

1. **Hybrid Profiling**: Combine implicit (trail history) with explicit (preferences)
2. **Confidence Scores**: Provide confidence levels for profile detection
3. **Profile Evolution**: Track how profiles change over time
4. **Machine Learning**: Use ML to optimize scoring weights
5. **Multi-Profile Support**: Allow users to have multiple profiles with weights
6. **Contextual Profiles**: Different profiles for different seasons/contexts
7. **Collaborative Filtering**: Use similar users' profiles to improve detection
8. **A/B Testing**: Test different scoring algorithms to improve accuracy

---

## Appendix A: Profile Name Mappings

### English Display Names

- `elevation_lover` → "Elevation Enthusiast"
- `performance_athlete` → "Performance Athlete"
- `contemplative` → "Contemplative Hiker"
- `casual` → "Casual Hiker"
- `family` → "Family / Group Hiker"
- `explorer` → "Explorer / Adventurer"
- `photographer` → "Photographer / Content Creator"

### French Display Names

- `elevation_lover` → "L'Amateur de dénivelé"
- `performance_athlete` → "Le Sportif de performance"
- `contemplative` → "Le Contemplatif"
- `casual` → "Le Randonneur occasionnel"
- `family` → "La Famille / Groupe hétérogène"
- `explorer` → "L'Explorateur / Aventurier"
- `photographer` → "Le Photographe / Créateur de contenu"

---

## Appendix B: Statistical Formulas

### Mean Calculation
```
mean = sum(values) / len(values)
```

### Median Calculation
```
sorted_vals = sorted(values)
n = len(sorted_vals)
median = sorted_vals[n // 2]
```

### Quartile Calculation
```
Q1 = sorted_vals[n // 4]
Q3 = sorted_vals[3 * n // 4]
```

### Standard Deviation
```
mean = sum(values) / len(values)
variance = sum((x - mean)² for x in values) / (len(values) - 1)
std = sqrt(variance)
```

### Frequency Distribution
```
frequency[value] = count(value) / total_count
```

---

## Appendix C: Score Normalization

All scores are normalized to ensure fair comparison:

- **Distance**: Normalized by dividing by typical maximum (10-15 km)
- **Elevation**: Normalized by dividing by typical maximum (400-1000 m)
- **Difficulty**: Normalized by dividing by maximum (10.0)
- **Duration**: Normalized by dividing by typical maximum (120-180 min)
- **Frequencies**: Already normalized (0.0 to 1.0)

Scores can exceed 1.0 when boost multipliers are applied for strong profile matches.

---

## Document Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024 | Initial documentation |

---

**End of Document**
