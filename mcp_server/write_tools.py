"""
Write Tools for Family Adventure Planner MCP Server
Provides database write operations to Lakebase
"""

import psycopg2
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

class LakebaseWriter:
    """Handles write operations to Lakebase database"""
    
    def __init__(self):
        """Initialize database connection parameters"""
        self.host = os.getenv("LAKEBASE_HOST", "ep-calm-river-d891evds.database.us-east-2.cloud.databricks.com")
        self.database = os.getenv("LAKEBASE_DATABASE", "databricks_postgres")
        self.user = os.getenv("LAKEBASE_USER", "user")
        self.password = os.getenv("LAKEBASE_PASSWORD", "npg_ZlOMFTehK8J3")
    
    def _get_connection(self):
        """Create a database connection"""
        return psycopg2.connect(
            host=self.host,
            port=5432,
            dbname=self.database,
            user=self.user,
            password=self.password,
            sslmode="require"
        )
    
    def save_to_itinerary(self, 
                         user_id: str,
                         destination_id: int,
                         activity_id: int,
                         trip_date: str,
                         notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Save an activity to the user's itinerary.
        
        Args:
            user_id: User identifier
            destination_id: ID of the destination
            activity_id: ID of the activity to save
            trip_date: Date of the trip (YYYY-MM-DD format)
            notes: Optional notes about this itinerary item
            
        Returns:
            Dict with itinerary_id and confirmation
        """
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                # Insert into itinerary
                cur.execute("""
                    INSERT INTO user_itinerary 
                    (user_id, destination_id, activity_id, trip_date, notes, status)
                    VALUES (%s, %s, %s, %s, %s, 'planned')
                    RETURNING itinerary_id, created_at
                """, (user_id, destination_id, activity_id, trip_date, notes))
                
                result = cur.fetchone()
                itinerary_id, created_at = result
                
                # Get activity and destination names for confirmation
                cur.execute("""
                    SELECT d.name, a.activity_name
                    FROM destinations d
                    JOIN activities a ON a.destination_id = d.destination_id
                    WHERE d.destination_id = %s AND a.activity_id = %s
                """, (destination_id, activity_id))
                
                dest_name, activity_name = cur.fetchone()
                conn.commit()
                
                return {
                    "success": True,
                    "itinerary_id": itinerary_id,
                    "destination": dest_name,
                    "activity": activity_name,
                    "trip_date": trip_date,
                    "notes": notes,
                    "created_at": str(created_at),
                    "message": f"Added '{activity_name}' at {dest_name} to your itinerary for {trip_date}"
                }
        
        except psycopg2.IntegrityError as e:
            return {
                "success": False,
                "error": "Invalid destination or activity ID",
                "details": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to save to itinerary: {str(e)}"
            }
        finally:
            if 'conn' in locals():
                conn.close()
    
    def add_to_watchlist(self,
                        user_id: str,
                        destination_id: int,
                        priority: int = 1,
                        notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Add a destination to the user's watchlist.
        
        Args:
            user_id: User identifier
            destination_id: ID of the destination to add
            priority: Priority level (1=high, 2=medium, 3=low)
            notes: Optional notes about why they want to visit
            
        Returns:
            Dict with watchlist_id and confirmation
        """
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                # Check if already in watchlist
                cur.execute("""
                    SELECT watchlist_id FROM user_watchlist
                    WHERE user_id = %s AND destination_id = %s
                """, (user_id, destination_id))
                
                existing = cur.fetchone()
                if existing:
                    # Update existing entry
                    cur.execute("""
                        UPDATE user_watchlist
                        SET priority = %s, notes = %s
                        WHERE watchlist_id = %s
                        RETURNING watchlist_id
                    """, (priority, notes, existing[0]))
                    watchlist_id = cur.fetchone()[0]
                    action = "Updated"
                else:
                    # Insert new entry
                    cur.execute("""
                        INSERT INTO user_watchlist
                        (user_id, destination_id, priority, notes)
                        VALUES (%s, %s, %s, %s)
                        RETURNING watchlist_id, created_at
                    """, (user_id, destination_id, priority, notes))
                    result = cur.fetchone()
                    watchlist_id = result[0]
                    action = "Added"
                
                # Get destination name for confirmation
                cur.execute("""
                    SELECT name, country
                    FROM destinations
                    WHERE destination_id = %s
                """, (destination_id,))
                
                dest_info = cur.fetchone()
                if not dest_info:
                    conn.rollback()
                    return {
                        "success": False,
                        "error": f"Destination ID {destination_id} not found"
                    }
                
                dest_name, country = dest_info
                conn.commit()
                
                priority_text = {1: "high", 2: "medium", 3: "low"}.get(priority, "medium")
                
                return {
                    "success": True,
                    "watchlist_id": watchlist_id,
                    "destination": dest_name,
                    "country": country,
                    "priority": priority_text,
                    "notes": notes,
                    "message": f"{action} {dest_name}, {country} to your watchlist with {priority_text} priority"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to add to watchlist: {str(e)}"
            }
        finally:
            if 'conn' in locals():
                conn.close()
    
    def save_user_preferences(self,
                            user_id: str,
                            preferred_weather: Optional[str] = None,
                            min_temperature_f: Optional[int] = None,
                            max_temperature_f: Optional[int] = None,
                            avoid_rain: bool = True,
                            preferred_activity_types: Optional[List[str]] = None,
                            budget_range: Optional[str] = None,
                            accessibility_needs: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Save or update user travel preferences.
        
        Args:
            user_id: User identifier
            preferred_weather: Preferred weather type (e.g., "sunny", "mild")
            min_temperature_f: Minimum comfortable temperature
            max_temperature_f: Maximum comfortable temperature
            avoid_rain: Whether to avoid rainy destinations
            preferred_activity_types: List of preferred activity types
            budget_range: Budget range (e.g., "budget", "moderate", "luxury")
            accessibility_needs: List of accessibility requirements
            
        Returns:
            Dict with confirmation and saved preferences
        """
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                # Check if preferences exist
                cur.execute("""
                    SELECT preference_id FROM user_preferences
                    WHERE user_id = %s
                """, (user_id,))
                
                existing = cur.fetchone()
                
                if existing:
                    # Update existing preferences
                    cur.execute("""
                        UPDATE user_preferences
                        SET preferred_weather = COALESCE(%s, preferred_weather),
                            min_temperature_f = COALESCE(%s, min_temperature_f),
                            max_temperature_f = COALESCE(%s, max_temperature_f),
                            avoid_rain = %s,
                            preferred_activity_types = COALESCE(%s, preferred_activity_types),
                            budget_range = COALESCE(%s, budget_range),
                            accessibility_needs = COALESCE(%s, accessibility_needs),
                            updated_at = NOW()
                        WHERE user_id = %s
                        RETURNING preference_id
                    """, (preferred_weather, min_temperature_f, max_temperature_f,
                          avoid_rain, preferred_activity_types, budget_range,
                          accessibility_needs, user_id))
                    action = "Updated"
                else:
                    # Insert new preferences
                    cur.execute("""
                        INSERT INTO user_preferences
                        (user_id, preferred_weather, min_temperature_f, max_temperature_f,
                         avoid_rain, preferred_activity_types, budget_range, accessibility_needs)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING preference_id
                    """, (user_id, preferred_weather, min_temperature_f, max_temperature_f,
                          avoid_rain, preferred_activity_types, budget_range, accessibility_needs))
                    action = "Saved"
                
                preference_id = cur.fetchone()[0]
                conn.commit()
                
                return {
                    "success": True,
                    "preference_id": preference_id,
                    "user_id": user_id,
                    "preferences": {
                        "preferred_weather": preferred_weather,
                        "temperature_range_f": f"{min_temperature_f or 'any'}-{max_temperature_f or 'any'}",
                        "avoid_rain": avoid_rain,
                        "activity_types": preferred_activity_types or [],
                        "budget_range": budget_range,
                        "accessibility_needs": accessibility_needs or []
                    },
                    "message": f"{action} your travel preferences successfully"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to save preferences: {str(e)}"
            }
        finally:
            if 'conn' in locals():
                conn.close()
    
    def get_user_itinerary(self, user_id: str, trip_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve user's itinerary items (READ operation for verification).
        
        Args:
            user_id: User identifier
            trip_date: Optional specific date to filter by
            
        Returns:
            Dict with list of itinerary items
        """
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                if trip_date:
                    cur.execute("""
                        SELECT i.itinerary_id, d.name, a.activity_name, i.trip_date, 
                               i.notes, i.status, i.created_at
                        FROM user_itinerary i
                        JOIN destinations d ON i.destination_id = d.destination_id
                        JOIN activities a ON i.activity_id = a.activity_id
                        WHERE i.user_id = %s AND i.trip_date = %s
                        ORDER BY i.trip_date, i.created_at
                    """, (user_id, trip_date))
                else:
                    cur.execute("""
                        SELECT i.itinerary_id, d.name, a.activity_name, i.trip_date, 
                               i.notes, i.status, i.created_at
                        FROM user_itinerary i
                        JOIN destinations d ON i.destination_id = d.destination_id
                        JOIN activities a ON i.activity_id = a.activity_id
                        WHERE i.user_id = %s
                        ORDER BY i.trip_date, i.created_at
                    """, (user_id,))
                
                items = cur.fetchall()
                
                return {
                    "success": True,
                    "count": len(items),
                    "items": [
                        {
                            "itinerary_id": row[0],
                            "destination": row[1],
                            "activity": row[2],
                            "trip_date": str(row[3]),
                            "notes": row[4],
                            "status": row[5],
                            "added": str(row[6])
                        }
                        for row in items
                    ]
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to retrieve itinerary: {str(e)}"
            }
        finally:
            if 'conn' in locals():
                conn.close()
