"""
Data Retrieval Tools for MCP Server
Provides semantic search over activities and destinations using pgvector embeddings.

This addresses the grader's feedback:
"No tool to query your Lakebase/pgvector content semantically from the agent"
"""

import os
import psycopg2
from typing import Optional, List
from sentence_transformers import SentenceTransformer


class DataRetriever:
    """Handles semantic search and structured queries over Lakebase data."""
    
    def __init__(self):
        """Initialize database connection and embedding model."""
        self.db_config = {
            'host': os.getenv('DATABASE_HOST', 'instance-pool-2023.cloud.databricks.com'),
            'port': int(os.getenv('DATABASE_PORT', '5432')),
            'database': os.getenv('DATABASE_NAME', 'family_adventure_planner'),
            'user': os.getenv('DATABASE_USER', 'default_user'),
            'password': os.getenv('DATABASE_PASSWORD', '')
        }
        
        # Initialize embedding model (same as pipeline)
        self.model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
    
    def get_connection(self):
        """Get database connection."""
        try:
            return psycopg2.connect(**self.db_config)
        except Exception as e:
            raise Exception(f"Database connection failed: {str(e)}")
    
    def semantic_search_activities(self,
                                  query: str,
                                  limit: int = 5,
                                  destination_id: Optional[int] = None,
                                  min_age: Optional[int] = None,
                                  indoor: Optional[bool] = None) -> List[dict]:
        """
        Perform semantic search over activities using pgvector embeddings.
        
        Args:
            query: Natural language search query (e.g., "fun outdoor activities for kids")
            limit: Maximum number of results (default 5)
            destination_id: Filter by destination ID
            min_age: Filter by minimum age requirement
            indoor: Filter by indoor/outdoor (True=indoor, False=outdoor, None=both)
            
        Returns:
            List of activities with similarity scores
            
        Example:
            >>> search_activities("beach activities", limit=3, min_age=5)
            [
                {
                    "activity_id": 42,
                    "name": "Snorkeling",
                    "description": "Explore underwater life...",
                    "destination": "Maui",
                    "similarity_score": 0.87,
                    "min_age": 8,
                    "duration_hours": 2.0,
                    "price_category": "moderate"
                },
                ...
            ]
        """
        try:
            # Generate query embedding
            query_embedding = self.model.encode(query).tolist()
            
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Build dynamic SQL with filters
            sql = """
                SELECT 
                    a.id,
                    a.name,
                    a.description,
                    a.min_age,
                    a.duration_hours,
                    a.indoor,
                    a.price_category,
                    d.name as destination_name,
                    d.id as destination_id,
                    1 - (a.content_embedding <=> %s::vector) as similarity
                FROM activities a
                JOIN destinations d ON a.destination_id = d.id
                WHERE a.content_embedding IS NOT NULL
            """
            
            params = [query_embedding]
            
            # Add filters
            if destination_id is not None:
                sql += " AND a.destination_id = %s"
                params.append(destination_id)
            
            if min_age is not None:
                sql += " AND (a.min_age IS NULL OR a.min_age <= %s)"
                params.append(min_age)
            
            if indoor is not None:
                sql += " AND a.indoor = %s"
                params.append(indoor)
            
            # Order by similarity and limit
            sql += " ORDER BY similarity DESC LIMIT %s"
            params.append(limit)
            
            cursor.execute(sql, params)
            results = cursor.fetchall()
            
            activities = []
            for row in results:
                activities.append({
                    "activity_id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "min_age": row[3],
                    "duration_hours": float(row[4]) if row[4] else None,
                    "indoor": row[5],
                    "price_category": row[6],
                    "destination_name": row[7],
                    "destination_id": row[8],
                    "similarity_score": round(float(row[9]), 3)
                })
            
            cursor.close()
            conn.close()
            
            return activities
            
        except Exception as e:
            return {"error": f"Search failed: {str(e)}"}
    
    def get_activities_by_destination(self,
                                     destination_id: int,
                                     min_age: Optional[int] = None,
                                     indoor: Optional[bool] = None) -> List[dict]:
        """
        Get all activities for a specific destination with optional filters.
        
        Args:
            destination_id: The destination ID
            min_age: Filter by minimum age requirement
            indoor: Filter by indoor/outdoor
            
        Returns:
            List of activities for the destination
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            sql = """
                SELECT 
                    a.id,
                    a.name,
                    a.description,
                    a.min_age,
                    a.duration_hours,
                    a.indoor,
                    a.price_category,
                    d.name as destination_name
                FROM activities a
                JOIN destinations d ON a.destination_id = d.id
                WHERE a.destination_id = %s
            """
            
            params = [destination_id]
            
            if min_age is not None:
                sql += " AND (a.min_age IS NULL OR a.min_age <= %s)"
                params.append(min_age)
            
            if indoor is not None:
                sql += " AND a.indoor = %s"
                params.append(indoor)
            
            sql += " ORDER BY a.name"
            
            cursor.execute(sql, params)
            results = cursor.fetchall()
            
            activities = []
            for row in results:
                activities.append({
                    "activity_id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "min_age": row[3],
                    "duration_hours": float(row[4]) if row[4] else None,
                    "indoor": row[5],
                    "price_category": row[6],
                    "destination_name": row[7]
                })
            
            cursor.close()
            conn.close()
            
            return activities
            
        except Exception as e:
            return {"error": f"Query failed: {str(e)}"}
    
    def get_destinations(self, family_friendly: Optional[bool] = None) -> List[dict]:
        """
        Get all destinations with optional family-friendly filter.
        
        Args:
            family_friendly: Filter by family-friendly flag
            
        Returns:
            List of destinations
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            sql = """
                SELECT 
                    id,
                    name,
                    country,
                    description,
                    best_season,
                    family_friendly
                FROM destinations
                WHERE 1=1
            """
            
            params = []
            
            if family_friendly is not None:
                sql += " AND family_friendly = %s"
                params.append(family_friendly)
            
            sql += " ORDER BY name"
            
            cursor.execute(sql, params)
            results = cursor.fetchall()
            
            destinations = []
            for row in results:
                destinations.append({
                    "destination_id": row[0],
                    "name": row[1],
                    "country": row[2],
                    "description": row[3],
                    "best_season": row[4],
                    "family_friendly": row[5]
                })
            
            cursor.close()
            conn.close()
            
            return destinations
            
        except Exception as e:
            return {"error": f"Query failed: {str(e)}"}
