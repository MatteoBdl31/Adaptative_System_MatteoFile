#!/usr/bin/env python3
"""
Script to generate dummy fitness data for all users.
Run this after initializing the database to populate fitness metrics.
"""

import sys
from pathlib import Path

# Add parent directory to path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.generate_dummy_fitness_data import generate_fitness_data_for_all_users
from backend.db import _ensure_new_tables

if __name__ == "__main__":
    print("=" * 60)
    print("Generating Dummy Fitness Data")
    print("=" * 60)
    print()
    
    _ensure_new_tables()
    generate_fitness_data_for_all_users()
