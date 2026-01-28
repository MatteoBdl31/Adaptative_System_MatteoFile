#!/usr/bin/env python3
"""
Find which trail(s) from the trails DB, when added as completed for a user,
would change that user's detected profile category.

Run from repo root or adaptive_quiz_system with:
  python -m scripts.find_profile_change_trails
or from adaptive_quiz_system:
  python scripts/find_profile_change_trails.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Allow importing backend when run as script
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.db import get_all_users, get_all_trails, get_trail, get_user_profile
from backend.user_profiling import UserProfiler


def main() -> None:
    profiler = UserProfiler()
    users = get_all_users()
    all_trails = get_all_trails()
    name_for = {t.get("trail_id"): t.get("name", t.get("trail_id", "?")) for t in all_trails}

    # Use trail_ids from dummy_smartwatch JSONs (if you want “dummy trails” only)
    import json as _json
    dummy_dir = ROOT / "data" / "dummy_smartwatch"
    dummy_trail_ids = None
    if dummy_dir.exists():
        dummy_trail_ids = set()
        for f in dummy_dir.glob("*.json"):
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    data = _json.load(fp)
                tid = data.get("trail_id")
                if tid:
                    dummy_trail_ids.add(tid)
            except Exception:
                pass
        if not dummy_trail_ids:
            dummy_trail_ids = None

    print("Profile-change trail finder")
    print("=" * 80)
    print("Looking for: user + trail such that completing that trail changes the user's profile.\n")

    results = []
    for user in users:
        uid = user["id"]
        uname = user.get("name", f"user_{uid}")
        profile = get_user_profile(uid)
        current = (profile.get("primary_profile") if profile else None) or "-"
        completed_ids = {c["trail_id"] for c in user.get("completed_trails", [])}
        completed_dicts = []
        for cid in completed_ids:
            t = get_trail(cid)
            if t:
                completed_dicts.append(t)

        # Need at least 2 completed so that adding 1 reaches 3 (minimum for profile)
        if len(completed_dicts) < 2:
            continue

        candidate_trails = [t for t in all_trails if t.get("trail_id") not in completed_ids]
        if dummy_trail_ids is not None:
            candidate_trails = [t for t in candidate_trails if t.get("trail_id") in dummy_trail_ids]

        for trail in candidate_trails:
            trail_id = trail.get("trail_id")
            extended = completed_dicts + [trail]
            new_profile, _ = profiler.detect_profile_from_trail_list(extended)
            if new_profile and new_profile != current:
                results.append({
                    "user_id": uid,
                    "user_name": uname,
                    "current_profile": current,
                    "new_profile": new_profile,
                    "trail_id": trail_id,
                    "trail_name": trail.get("name", trail_id),
                    "distance": trail.get("distance"),
                    "elevation_gain": trail.get("elevation_gain"),
                    "difficulty": trail.get("difficulty"),
                    "duration": trail.get("duration"),
                })

    # Report
    if not results:
        print("No (user, trail) pairs found that change profile.")
        if dummy_trail_ids is not None:
            print("(Search was limited to trails that appear in data/dummy_smartwatch.)")
        return

    # Group by user for readability
    by_user: dict[tuple[int, str, str], list[dict]] = {}
    for r in results:
        key = (r["user_id"], r["user_name"], r["current_profile"])
        by_user.setdefault(key, []).append(r)

    for (uid, uname, current), rows in sorted(by_user.items(), key=lambda x: (x[0][1], x[0][2])):
        print(f"User: {uname} (id={uid}) - current profile: {current}")
        for r in rows:
            print(f"  -> Add trail: \"{r['trail_name']}\" (id={r['trail_id']})")
            print(f"    New profile: {r['new_profile']}")
            print(f"    Trail: dist={r['distance']} km, elev={r['elevation_gain']} m, diff={r['difficulty']}, dur={r['duration']} min")
        print()

    print("=" * 80)
    # One example per user (first trail that changes profile)
    print("\nQuick reference (one trail per user that causes a change):")
    print("-" * 80)
    for (uid, uname, current), rows in sorted(by_user.items(), key=lambda x: (x[0][1], x[0][2])):
        r = rows[0]
        print(f"  {uname} (id={uid}) [{current}] -> add \"{r['trail_name']}\" -> {r['new_profile']}")
    print("-" * 80)
    print("How to use: Start that trail for the user, then complete it (e.g. from Profile > Complete).")
    print("The app will show the profile-change celebration when the category changes.")


if __name__ == "__main__":
    main()
