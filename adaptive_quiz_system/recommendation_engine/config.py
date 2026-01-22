# -*- coding: utf-8 -*-
"""
Configuration for recommendation system.
Configurable thresholds and settings for flexibility.
"""

import os

# Exact match threshold - minimum relevance percentage for exact matches
EXACT_MATCH_THRESHOLD = float(os.getenv("REC_EXACT_MATCH_THRESHOLD", "80.0"))

# Progressive threshold levels for fallback
THRESHOLD_LEVELS = [
    80.0,  # Level 1: Strict
    60.0,  # Level 2: Moderate
    40.0,  # Level 3: Lenient
    20.0   # Level 4: Very lenient
]

# Minimum candidates before triggering fallback
MIN_CANDIDATES_BEFORE_FALLBACK = int(os.getenv("REC_MIN_CANDIDATES", "0"))

# Maximum filter relaxation levels to try
MAX_FILTER_RELAXATION_LEVELS = int(os.getenv("REC_MAX_FALLBACK_LEVELS", "7"))

# Enable debug mode (set via environment variable)
DEBUG_ENABLED = os.getenv("REC_DEBUG", "true").lower() == "true"

# Soft filter mode - deprioritize instead of removing
SOFT_FILTER_MODE = os.getenv("REC_SOFT_FILTER", "false").lower() == "true"

# Always return results (even if low quality)
ALWAYS_RETURN_RESULTS = os.getenv("REC_ALWAYS_RETURN", "true").lower() == "true"

# Minimum results to return
MIN_RESULTS_TO_RETURN = int(os.getenv("REC_MIN_RESULTS", "1"))

# Maximum results per category
DEFAULT_MAX_TRAILS = int(os.getenv("REC_MAX_TRAILS", "10"))

# Maximum results per category (can be overridden)
DEFAULT_MAX_EXACT = int(os.getenv("REC_MAX_EXACT", "30"))
DEFAULT_MAX_SUGGESTIONS = int(os.getenv("REC_MAX_SUGGESTIONS", "20"))
DEFAULT_MAX_COLLABORATIVE = int(os.getenv("REC_MAX_COLLABORATIVE", "10"))
