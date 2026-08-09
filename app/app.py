"""
Family Adventure Planner - Flask API

REST API for semantic search over family-friendly destinations and activities.
Uses Lakebase Postgres with pgvector for vector similarity search.

Endpoints:
- GET  /                          - Health check
- GET  /destinations              - List all destinations
- GET  /destinations/{id}         - Get destination details
- GET  /destinations/{id}/activities - Get activities for a destination
- GET  /activities/search         - Semantic search over activities

Query Parameters for /activities/search:
- query: Search query text (e.g., "indoor museum for toddlers")
- min_age: Minimum age filter (optional)
- max_age: Maximum age filter (optional)
- indoor: Filter by indoor (true/false, optional)
- limit: Number of results (default: 10)

Usage:
    python app.py
    # Or with gunicorn:
    gunicorn -w 4 -b 0.0.0.0:8000 app:app
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import psycopg
from psycopg.rows import dict_row
from databricks.sdk import WorkspaceClient
from typing import Optional, List, Dict
import os

# ============================================================================
# Configuration
# ============================================================================

LAKEBASE_PROJECT = "family-adventure-planner"
LAKEBASE_BRANCH = "production"
LAKEBASE_DATABASE = "databricks_postgres"

# ============================================================================
# Flask App Setup
# ============================================================================

app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app)  # Enable CORS for frontend access

# Global connection pool (will be lazy-initialized)
_connection_pool = None


def get_connection_pool():
    """
    Get or create a connection pool to Lakebase.
    """
    global _connection_pool
    
    if _connection_pool is None:
        w = WorkspaceClient()
        
        # Get endpoint details
        endpoint_name = f"projects/{LAKEBASE_PROJECT}/branches/{LAKEBASE_BRANCH}/endpoints/primary"
        endpoint = w.postgres.get_endpoint(name=endpoint_name)
        host = endpoint.status.hosts.host
        
        # Generate OAuth token
        cred = w.postgres.generate_database_credential(endpoint=endpoint_name)
        token = cred.token
        
        # Create connection string
        conninfo = f"host={host} port=5432 dbname={LAKEBASE_DATABASE} user=databricks password={token} sslmode=require"
        
        _connection_pool = psycopg.ConnectionPool(conninfo, min_size=2, max_size=10)
    
    return _connection_pool


def get_db_connection():
    """
    Get a connection from the pool.
    """
    pool = get_connection_pool()
    return pool.connection()


def generate_placeholder_query_embedding() -> List[float]:
    """
    Generate a placeholder query embedding for testing.
    
    TODO: Replace with real sentence-transformers embeddings once dependencies are installed.
    For now, returns a random normalized 768-dim vector.
    """
    import random
    embedding = [random.gauss(0, 0.001) for _ in range(768)]
    norm = sum(x**2 for x in embedding) ** 0.5
    return [x / norm for x in embedding]


# ============================================================================
# API Endpoints
# ============================================================================

@app.route('/', methods=['GET'])
def index():
    """
    Serve the frontend UI.
    """
    return send_from_directory('static', 'index.html')


@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.
    """
    return jsonify({
        "status": "healthy",
        "service": "family-adventure-planner-api",
        "version": "1.0.0"
    })


@app.route('/destinations', methods=['GET'])
def list_destinations():
    """
    List all destinations.
    
    Returns:
        [
            {
                "destination_id": 2,
                "name": "Golden Gate Park",
                "latitude": 37.7694,
                "longitude": -122.4862,
                "country": "United States",
                "description": "..."
            },
            ...
        ]
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute("""
                    SELECT 
                        destination_id,
                        name,
                        latitude,
                        longitude,
                        country,
                        description
                    FROM destinations
                    ORDER BY name
                """)
                destinations = cur.fetchall()
        
        return jsonify(destinations)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/destinations/<int:destination_id>', methods=['GET'])
def get_destination(destination_id: int):
    """
    Get a single destination by ID.
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute("""
                    SELECT 
                        destination_id,
                        name,
                        latitude,
                        longitude,
                        country,
                        description,
                        created_at
                    FROM destinations
                    WHERE destination_id = %s
                """, (destination_id,))
                destination = cur.fetchone()
        
        if destination:
            return jsonify(destination)
        else:
            return jsonify({"error": "Destination not found"}), 404
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/destinations/<int:destination_id>/activities', methods=['GET'])
def get_destination_activities(destination_id: int):
    """
    Get all activities for a specific destination.
    
    Returns:
        [
            {
                "activity_id": 1,
                "activity_name": "Koret Children's Quarter Playground",
                "activity_type": "playground",
                "description": "...",
                "min_age": 2,
                "max_age": 12,
                "indoor": false,
                "weather_dependent": true,
                "duration_minutes": 90
            },
            ...
        ]
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute("""
                    SELECT 
                        activity_id,
                        activity_name,
                        activity_type,
                        description,
                        min_age,
                        max_age,
                        indoor,
                        weather_dependent,
                        duration_minutes
                    FROM activities
                    WHERE destination_id = %s
                    ORDER BY activity_name
                """, (destination_id,))
                activities = cur.fetchall()
        
        return jsonify(activities)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/activities/search', methods=['GET'])
def search_activities():
    """
    Semantic search over activities using vector similarity.
    
    Query Parameters:
    - query: Search query text (required)
    - min_age: Minimum age filter (optional)
    - max_age: Maximum age filter (optional)
    - indoor: Filter by indoor activities (true/false, optional)
    - limit: Number of results to return (default: 10, max: 50)
    
    Returns:
        [
            {
                "activity_id": 3,
                "activity_name": "Exploratorium Indoor Exhibits",
                "activity_type": "museum",
                "description": "...",
                "destination_name": "Exploratorium",
                "min_age": 2,
                "max_age": null,
                "indoor": true,
                "weather_dependent": false,
                "duration_minutes": 120,
                "similarity_score": 0.85
            },
            ...
        ]
    """
    # Parse query parameters
    query_text = request.args.get('query')
    min_age = request.args.get('min_age', type=int)
    max_age = request.args.get('max_age', type=int)
    indoor_filter = request.args.get('indoor')
    limit = min(int(request.args.get('limit', 10)), 50)
    
    if not query_text:
        return jsonify({"error": "Query parameter 'query' is required"}), 400
    
    try:
        # Generate query embedding
        # TODO: Replace with real sentence-transformers embedding
        query_embedding = generate_placeholder_query_embedding()
        embedding_str = str(query_embedding)
        
        # Build dynamic WHERE clause for filters
        where_clauses = []
        params = [embedding_str, limit]
        
        if min_age is not None:
            where_clauses.append("a.min_age <= %s")
            params.insert(-1, min_age)
        
        if max_age is not None:
            where_clauses.append("(a.max_age IS NULL OR a.max_age >= %s)")
            params.insert(-1, max_age)
        
        if indoor_filter is not None:
            indoor_bool = indoor_filter.lower() == 'true'
            where_clauses.append("a.indoor = %s")
            params.insert(-1, indoor_bool)
        
        where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        # Execute semantic search
        with get_db_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                query_sql = f"""
                    SELECT 
                        a.activity_id,
                        a.activity_name,
                        a.activity_type,
                        a.description,
                        d.name as destination_name,
                        a.min_age,
                        a.max_age,
                        a.indoor,
                        a.weather_dependent,
                        a.duration_minutes,
                        1 - (a.content_embedding <=> %s::vector) as similarity_score
                    FROM activities a
                    JOIN destinations d ON a.destination_id = d.destination_id
                    {where_clause}
                    ORDER BY a.content_embedding <=> %s::vector
                    LIMIT %s
                """
                
                cur.execute(query_sql, params)
                results = cur.fetchall()
        
        return jsonify({
            "query": query_text,
            "filters": {
                "min_age": min_age,
                "max_age": max_age,
                "indoor": indoor_filter
            },
            "count": len(results),
            "results": results
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# Run Server
# ============================================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=True)