# -*- coding: utf-8 -*-
"""
Collaborative recommendation service for getting trail recommendations from similar users.
"""

import sqlite3
from typing import List, Dict, Optional
from backend.db import USERS_DB, get_trail


class CollaborativeRecommendationService:
    """Service for getting trail recommendations from similar users."""
    
    def get_trails_from_similar_users(
        self,
        user_id: int,
        min_rating: float = 3.5,
        min_users: int = 2,
        exclude_trail_ids: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Get trails that similar users (same profile) have completed with high ratings.
        
        Args:
            user_id: Current user ID
            min_rating: Minimum rating threshold (default: 3.5)
            min_users: Minimum number of users who must have completed the trail (default: 2)
            exclude_trail_ids: Optional list of trail IDs to exclude (default: None, 
                             will exclude only trails completed by current user)
        
        Returns:
            List of trail dictionaries with collaborative metadata
        """
        conn = sqlite3.connect(USERS_DB)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        try:
            # Get current user's profile
            cur.execute("SELECT primary_profile FROM user_profiles WHERE user_id = ?", (user_id,))
            profile_row = cur.fetchone()
            if not profile_row or not profile_row["primary_profile"]:
                # User doesn't have a profile yet - return empty list
                return []
            
            user_profile = profile_row["primary_profile"]
            
            # Get trails completed by current user (to exclude)
            cur.execute("SELECT trail_id FROM completed_trails WHERE user_id = ?", (user_id,))
            user_completed_trails = {row["trail_id"] for row in cur.fetchall()}
            
            # Build exclusion list
            exclude_list = set(user_completed_trails)
            if exclude_trail_ids:
                exclude_list.update(exclude_trail_ids)
            
            # Get trails completed by users with same profile, excluding current user and specified trails
            query = """
                SELECT 
                    ct.trail_id,
                    AVG(ct.rating) as avg_rating,
                    COUNT(DISTINCT ct.user_id) as user_count,
                    MAX(ct.completion_date) as latest_completion
                FROM completed_trails ct
                JOIN user_profiles up ON ct.user_id = up.user_id
                WHERE up.primary_profile = ?
                  AND ct.user_id != ?
                  AND ct.rating >= ?
            """
            params = [user_profile, user_id, min_rating]
            
            if exclude_list:
                # SQLite has a limit on the number of parameters (999 by default)
                # If exclude_list is too large, we need to handle it differently
                if len(exclude_list) > 900:
                    # For very large exclusion lists, use a subquery instead
                    exclude_placeholders = ','.join(['?'] * min(len(exclude_list), 900))
                    query += f" AND ct.trail_id NOT IN ({exclude_placeholders})"
                    params.extend(list(exclude_list)[:900])
                else:
                    exclude_placeholders = ','.join(['?'] * len(exclude_list))
                    query += f" AND ct.trail_id NOT IN ({exclude_placeholders})"
                    params.extend(list(exclude_list))
            
            query += """
                GROUP BY ct.trail_id
                HAVING COUNT(DISTINCT ct.user_id) >= ?
                ORDER BY avg_rating DESC, user_count DESC, latest_completion DESC
            """
            params.append(min_users)
            
            cur.execute(query, params)
            results = cur.fetchall()
            
            # Enrich with trail details
            collaborative_trails = []
            for row in results:
                trail = get_trail(row["trail_id"])
                if trail:
                    trail["is_collaborative"] = True
                    trail["collaborative_avg_rating"] = round(row["avg_rating"], 2)
                    trail["collaborative_user_count"] = row["user_count"]
                    trail["collaborative_completion_count"] = row["user_count"]  # Same as user_count for now
                    collaborative_trails.append(trail)
            
            return collaborative_trails
            
        finally:
            conn.close()
