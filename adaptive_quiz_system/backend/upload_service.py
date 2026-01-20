# -*- coding: utf-8 -*-
"""
Upload service for processing and storing trail performance data.
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from backend.db import USERS_DB, TRAILS_DB, get_all_trails, get_trail, _ensure_new_tables

_ensure_new_tables()


class UploadService:
    """Handles trail data uploads and processing."""
    
    def __init__(self):
        self.users_db = USERS_DB
        self.trails_db = TRAILS_DB
    
    def parse_uploaded_data(self, file_content: str, data_format: str = "json") -> Dict:
        """
        Parse uploaded trail data.
        
        Args:
            file_content: File content as string
            data_format: Format type ('json', 'gpx', etc.)
        
        Returns:
            {
                "success": bool,
                "data": Dict,
                "errors": List[str]
            }
        """
        errors = []
        
        if data_format == "json":
            try:
                data = json.loads(file_content)
                return {
                    "success": True,
                    "data": data,
                    "errors": []
                }
            except json.JSONDecodeError as e:
                errors.append(f"Invalid JSON format: {str(e)}")
                return {
                    "success": False,
                    "data": None,
                    "errors": errors
                }
        else:
            errors.append(f"Unsupported format: {data_format}")
            return {
                "success": False,
                "data": None,
                "errors": errors
            }
    
    def validate_trail_data(self, parsed_data: Dict) -> Tuple[bool, List[str]]:
        """
        Validate parsed trail data structure.
        
        Args:
            parsed_data: Parsed data dictionary
        
        Returns:
            (is_valid, errors)
        """
        errors = []
        
        # Check for required fields
        if not isinstance(parsed_data, dict):
            errors.append("Data must be a JSON object")
            return False, errors
        
        # Check for time-series data
        if "data_points" not in parsed_data and "points" not in parsed_data:
            errors.append("Missing time-series data points")
        
        # Check for basic trail info
        if "trail_id" not in parsed_data and "trail_name" not in parsed_data:
            errors.append("Missing trail identification")
        
        return len(errors) == 0, errors
    
    def match_to_trail(self, uploaded_data: Dict) -> Optional[str]:
        """
        Attempt to match uploaded trail data to an existing trail.
        
        Args:
            uploaded_data: Parsed trail data
        
        Returns:
            Trail ID if matched, None otherwise
        """
        # Try direct trail_id match first
        trail_id = uploaded_data.get("trail_id")
        if trail_id:
            trail = get_trail(trail_id)
            if trail:
                return trail_id
        
        # Try matching by name
        trail_name = uploaded_data.get("trail_name") or uploaded_data.get("name")
        if trail_name:
            all_trails = get_all_trails()
            for trail in all_trails:
                if trail.get("name", "").lower() == trail_name.lower():
                    return trail.get("trail_id")
        
        # Try matching by coordinates (if start/end points provided)
        start_coords = uploaded_data.get("start_coordinates") or uploaded_data.get("start")
        if start_coords:
            lat = start_coords.get("latitude") or start_coords.get("lat")
            lon = start_coords.get("longitude") or start_coords.get("lon")
            
            if lat and lon:
                all_trails = get_all_trails()
                best_match = None
                min_distance = float('inf')
                
                for trail in all_trails:
                    trail_lat = trail.get("latitude")
                    trail_lon = trail.get("longitude")
                    
                    if trail_lat and trail_lon:
                        # Simple distance calculation
                        distance = ((lat - trail_lat) ** 2 + (lon - trail_lon) ** 2) ** 0.5
                        if distance < min_distance and distance < 0.01:  # ~1km tolerance
                            min_distance = distance
                            best_match = trail.get("trail_id")
                
                if best_match:
                    return best_match
        
        return None
    
    def normalize_performance_data(self, parsed_data: Dict) -> Dict:
        """
        Normalize uploaded performance data to standard format.
        
        Args:
            parsed_data: Parsed trail data
        
        Returns:
            Normalized data dictionary
        """
        normalized = {
            "trail_id": parsed_data.get("trail_id"),
            "trail_name": parsed_data.get("trail_name") or parsed_data.get("name"),
            "start_time": parsed_data.get("start_time") or parsed_data.get("start"),
            "end_time": parsed_data.get("end_time") or parsed_data.get("end"),
            "data_points": []
        }
        
        # Extract data points
        data_points = parsed_data.get("data_points") or parsed_data.get("points") or []
        
        for point in data_points:
            normalized_point = {
                "timestamp": self._parse_timestamp(point.get("timestamp") or point.get("time") or point.get("t")),
                "heart_rate": point.get("heart_rate") or point.get("hr") or point.get("heartRate"),
                "speed": point.get("speed") or point.get("velocity"),
                "elevation": point.get("elevation") or point.get("altitude") or point.get("elev"),
                "latitude": point.get("latitude") or point.get("lat"),
                "longitude": point.get("longitude") or point.get("lon") or point.get("lng"),
                "calories": point.get("calories") or point.get("cal"),
                "cadence": point.get("cadence") or point.get("steps_per_minute")
            }
            normalized["data_points"].append(normalized_point)
        
        return normalized
    
    def store_performance_data(
        self,
        user_id: int,
        trail_id: str,
        normalized_data: Dict,
        uploaded_data_id: Optional[int] = None
    ) -> Tuple[bool, Optional[int]]:
        """
        Store normalized performance data in database.
        
        Args:
            user_id: User ID
            trail_id: Trail ID
            normalized_data: Normalized performance data
            uploaded_data_id: Optional uploaded_data record ID
        
        Returns:
            (success, completed_trail_id)
        """
        conn = sqlite3.connect(self.users_db)
        cur = conn.cursor()
        
        try:
            # Calculate aggregated metrics
            data_points = normalized_data.get("data_points", [])
            
            heart_rates = [p.get("heart_rate") for p in data_points if p.get("heart_rate")]
            speeds = [p.get("speed") for p in data_points if p.get("speed")]
            calories = [p.get("calories") for p in data_points if p.get("calories")]
            
            avg_heart_rate = int(sum(heart_rates) / len(heart_rates)) if heart_rates else None
            max_heart_rate = max(heart_rates) if heart_rates else None
            avg_speed = sum(speeds) / len(speeds) if speeds else None
            max_speed = max(speeds) if speeds else None
            total_calories = sum(calories) if calories else None
            
            # Calculate duration from timestamps
            timestamps = [p.get("timestamp") for p in data_points if p.get("timestamp")]
            if timestamps:
                duration_minutes = (max(timestamps) - min(timestamps)) // 60
            else:
                duration_minutes = None
            
            # Create or update completed_trail record
            cur.execute("""
                SELECT id FROM completed_trails
                WHERE user_id = ? AND trail_id = ?
                ORDER BY completion_date DESC
                LIMIT 1
            """, (user_id, trail_id))
            existing = cur.fetchone()
            
            if existing:
                completed_trail_id = existing[0]
                # Update existing record
                cur.execute("""
                    UPDATE completed_trails
                    SET actual_duration = COALESCE(?, actual_duration),
                        avg_heart_rate = ?,
                        max_heart_rate = ?,
                        avg_speed = ?,
                        max_speed = ?,
                        total_calories = ?,
                        uploaded_data_id = ?
                    WHERE id = ?
                """, (duration_minutes, avg_heart_rate, max_heart_rate, avg_speed, max_speed,
                      total_calories, uploaded_data_id, completed_trail_id))
            else:
                # Create new completed_trail record
                cur.execute("""
                    INSERT INTO completed_trails
                    (user_id, trail_id, completion_date, actual_duration, rating,
                     avg_heart_rate, max_heart_rate, avg_speed, max_speed,
                     total_calories, uploaded_data_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (user_id, trail_id, datetime.now().isoformat(), duration_minutes, 5,
                      avg_heart_rate, max_heart_rate, avg_speed, max_speed,
                      total_calories, uploaded_data_id))
                completed_trail_id = cur.lastrowid
            
            # Store time-series data
            if data_points:
                # Delete existing data for this completed trail
                cur.execute("""
                    DELETE FROM trail_performance_data
                    WHERE completed_trail_id = ?
                """, (completed_trail_id,))
                
                # Insert new data points
                for point in data_points:
                    cur.execute("""
                        INSERT INTO trail_performance_data
                        (completed_trail_id, timestamp, heart_rate, speed, elevation,
                         latitude, longitude, calories, cadence)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        completed_trail_id,
                        point.get("timestamp"),
                        point.get("heart_rate"),
                        point.get("speed"),
                        point.get("elevation"),
                        point.get("latitude"),
                        point.get("longitude"),
                        point.get("calories"),
                        point.get("cadence")
                    ))
            
            conn.commit()
            return True, completed_trail_id
            
        except Exception as e:
            conn.rollback()
            print(f"Error storing performance data: {e}")
            return False, None
        finally:
            conn.close()
    
    def save_uploaded_file(
        self,
        user_id: int,
        original_filename: str,
        file_content: str,
        data_format: str = "json"
    ) -> int:
        """
        Save uploaded file metadata to database.
        
        Args:
            user_id: User ID
            original_filename: Original filename
            file_content: File content
            data_format: Data format
        
        Returns:
            Upload ID
        """
        conn = sqlite3.connect(self.users_db)
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO uploaded_trail_data
            (user_id, upload_date, original_filename, data_format, raw_data, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, datetime.now().isoformat(), original_filename, data_format,
              file_content, "pending"))
        
        upload_id = cur.lastrowid
        conn.commit()
        conn.close()
        
        return upload_id
    
    def update_upload_status(
        self,
        upload_id: int,
        status: str,
        trail_id: Optional[str] = None,
        parsed_data: Optional[str] = None
    ) -> bool:
        """
        Update upload status and associated trail.
        
        Args:
            upload_id: Upload ID
            status: Status ('pending', 'processed', 'error')
            trail_id: Associated trail ID
            parsed_data: Parsed data JSON string
        
        Returns:
            True if updated successfully
        """
        conn = sqlite3.connect(self.users_db)
        cur = conn.cursor()
        
        updates = ["status = ?"]
        params = [status]
        
        if trail_id:
            updates.append("trail_id = ?")
            params.append(trail_id)
        
        if parsed_data:
            updates.append("parsed_data = ?")
            params.append(parsed_data)
        
        params.append(upload_id)
        
        cur.execute(f"""
            UPDATE uploaded_trail_data
            SET {', '.join(updates)}
            WHERE id = ?
        """, params)
        
        updated = cur.rowcount > 0
        conn.commit()
        conn.close()
        
        return updated
    
    def get_user_uploads(self, user_id: int) -> List[Dict]:
        """Get all uploads for a user."""
        conn = sqlite3.connect(self.users_db)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        cur.execute("""
            SELECT * FROM uploaded_trail_data
            WHERE user_id = ?
            ORDER BY upload_date DESC
        """, (user_id,))
        
        uploads = [dict(row) for row in cur.fetchall()]
        conn.close()
        
        return uploads
    
    def _parse_timestamp(self, timestamp) -> Optional[int]:
        """Parse timestamp to seconds since start."""
        if timestamp is None:
            return None
        
        if isinstance(timestamp, int):
            return timestamp
        
        if isinstance(timestamp, str):
            try:
                # Try ISO format
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                return int(dt.timestamp())
            except:
                try:
                    # Try Unix timestamp string
                    return int(timestamp)
                except:
                    return None
        
        return None
