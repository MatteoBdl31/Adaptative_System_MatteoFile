#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Update existing trails with default values for missing fields"""

import sqlite3
import json
import sys
import os

# Add parent directory to path to import fetch_alps_trails
sys.path.insert(0, os.path.dirname(__file__))
from fetch_alps_trails import _ensure_trail_fields

BASE_DIR = os.path.dirname(__file__)
TRAILS_DB = os.path.join(BASE_DIR, "trails.db")

def update_trails():
    """Update existing trails to ensure all required fields have values"""
    conn = sqlite3.connect(TRAILS_DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Get all trails
    cur.execute("SELECT * FROM trails")
    trails = cur.fetchall()
    
    print(f"Found {len(trails)} trails in database")
    updated = 0
    
    for row in trails:
        # Convert row to dict
        trail = dict(row)
        
        # Ensure all fields are present
        complete_trail = _ensure_trail_fields(trail)
        
        # Check if update is needed
        needs_update = False
        for key in ['name', 'difficulty', 'duration', 'trail_type', 'landscapes', 
                    'popularity', 'safety_risks', 'accessibility', 'closed_seasons', 'description']:
            if trail.get(key) != complete_trail.get(key):
                needs_update = True
                break
        
        if needs_update:
            # Update the trail
            cur.execute("""
                UPDATE trails SET
                    name = ?, difficulty = ?, duration = ?, trail_type = ?,
                    landscapes = ?, popularity = ?, safety_risks = ?,
                    accessibility = ?, closed_seasons = ?, description = ?
                WHERE trail_id = ?
            """, (
                complete_trail['name'],
                complete_trail['difficulty'],
                complete_trail['duration'],
                complete_trail['trail_type'],
                complete_trail['landscapes'],
                complete_trail['popularity'],
                complete_trail['safety_risks'],
                complete_trail['accessibility'],
                complete_trail['closed_seasons'],
                complete_trail['description'],
                complete_trail['trail_id']
            ))
            updated += 1
            print(f"Updated trail {complete_trail['trail_id']}: {complete_trail['name']}")
    
    conn.commit()
    conn.close()
    print(f"\nUpdated {updated} trails with default values")

if __name__ == "__main__":
    update_trails()

