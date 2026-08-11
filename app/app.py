"""
Family Adventure Planner - Flask API

REST API for semantic search over family-friendly destinations and activities.
Uses Lakebase Postgres with pgvector for vector similarity search.

Endpoints:
- GET  /                          - Health check
- GET  /destinations              - List all destinations
- GET  /destinations/{id}         - Get destination details
- GET  /destinations/{id}/weather - Get 7-day weather forecast (Open-Meteo API)
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
import psycopg2
from databricks.sdk import WorkspaceClient
from typing import Optional, List, Dict
import os
from sentence_transformers import SentenceTransformer
import requests
from datetime import datetime, timedelta
import traceback

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

# Cache connection details (tokens expire, so we'll refresh as needed)
_connection_cache = {}

# Load embedding model for semantic search (768-dim)
print("Loading sentence-transformers model...")
_embedding_model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
print("Embedding model loaded!")


def get_db_connection():
    """
    Get a database connection to Lakebase.
    Uses environment variables from app.yaml or falls back to defaults.
    """
    # Use environment variables (from app.yaml) or fallback to defaults
    host = os.getenv("DATABASE_HOST", "ep-calm-river-d891evds.database.us-east-2.cloud.databricks.com")
    port = int(os.getenv("DATABASE_PORT", "5432"))
    database = os.getenv("DATABASE_NAME", "databricks_postgres")
    user = os.getenv("DATABASE_USER", "user")
    password = os.getenv("DATABASE_PASSWORD", "npg_ZlOMFTehK8J3")
    
    # Create connection
    conn = psycopg2.connect(
        host=host,
        port=port,
        dbname=database,
        user=user,
        password=password,
        sslmode="require"
    )
    
    return conn


def run_query(conn, query, params=None):
    """
    Execute a query with psycopg2 and return results as list of dicts.
    """
    with conn.cursor() as cur:
        if params:
            cur.execute(query, params)
        else:
            cur.execute(query)
        
        if cur.description is None:
            return []
        
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        return [dict(zip(columns, row)) for row in rows]


def generate_query_embedding(query_text: str) -> List[float]:
    """
    Generate a real semantic embedding for the query text using sentence-transformers.
    Uses all-mpnet-base-v2 model (768 dimensions) for accurate semantic search.
    """
    embedding = _embedding_model.encode(query_text, normalize_embeddings=True)
    return embedding.tolist()


def fetch_weather_forecast(latitude: float, longitude: float, days: int = 7) -> Optional[Dict]:
    """
    Fetch weather forecast from Open-Meteo API (FREE, no API key required).
    
    Args:
        latitude: Destination latitude
        longitude: Destination longitude
        days: Number of days to forecast (default 7)
    
    Returns:
        Dictionary with daily forecasts or None if error
    """
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weathercode,uv_index_max,windspeed_10m_max",
            "temperature_unit": "fahrenheit",
            "windspeed_unit": "mph",
            "forecast_days": days,
            "timezone": "auto"
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Weather code mapping (WMO codes)
        weather_conditions = {
            0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
            45: "Foggy", 48: "Depositing rime fog",
            51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
            61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
            71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
            80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
            95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"
        }
        
        daily = data.get("daily", {})
        forecasts = []
        
        for i in range(len(daily.get("time", []))):
            weather_code = daily["weathercode"][i]
            forecasts.append({
                "date": daily["time"][i],
                "temp_max_f": daily["temperature_2m_max"][i],
                "temp_min_f": daily["temperature_2m_min"][i],
                "precipitation_prob": daily["precipitation_probability_max"][i],
                "weather_condition": weather_conditions.get(weather_code, "Unknown"),
                "uv_index": daily["uv_index_max"][i],
                "wind_speed_mph": daily["windspeed_10m_max"][i]
            })
        
        return {
            "location": {"latitude": latitude, "longitude": longitude},
            "forecasts": forecasts
        }
    
    except Exception as e:
        print(f"Error fetching weather: {e}")
        return None


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
        conn = get_db_connection()
        destinations = run_query(conn, """
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
        conn.close()
        
        return jsonify(destinations)
    
    except Exception as e:
        print(f"ERROR in list_destinations: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/destinations/<int:destination_id>', methods=['GET'])
def get_destination(destination_id: int):
    """
    Get a single destination by ID.
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
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
            
            row = cur.fetchone()
            if not row:
                conn.close()
                return jsonify({"error": "Destination not found"}), 404
            
            columns = [desc[0] for desc in cur.description]
            destination = dict(zip(columns, row))
        
        conn.close()
        return jsonify(destination)
    
    except Exception as e:
        print(f"ERROR in get_destination: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/destinations/<int:destination_id>/weather', methods=['GET'])
def get_destination_weather(destination_id: int):
    """
    Get 7-day weather forecast for a destination.
    
    Query Parameters:
    - days: Number of days to forecast (default: 7)
    
    Returns:
        {
            "destination": {
                "destination_id": 2,
                "name": "Golden Gate Park",
                "country": "United States"
            },
            "forecasts": [
                {
                    "date": "2026-08-10",
                    "temp_max_f": 72,
                    "temp_min_f": 58,
                    "precipitation_prob": 10,
                    "weather_condition": "Partly cloudy",
                    "uv_index": 7,
                    "wind_speed_mph": 12
                },
                ...
            ]
        }
    """
    days = min(int(request.args.get('days', 7)), 14)
    
    try:
        # Get destination details first
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    destination_id,
                    name,
                    latitude,
                    longitude,
                    country
                FROM destinations
                WHERE destination_id = %s
            """, (destination_id,))
            
            row = cur.fetchone()
            if not row:
                conn.close()
                return jsonify({"error": "Destination not found"}), 404
            
            columns = [desc[0] for desc in cur.description]
            destination = dict(zip(columns, row))
        
        conn.close()
        
        # Fetch weather forecast
        weather_data = fetch_weather_forecast(
            latitude=destination['latitude'],
            longitude=destination['longitude'],
            days=days
        )
        
        if not weather_data:
            return jsonify({"error": "Failed to fetch weather data"}), 503
        
        # Format response
        return jsonify({
            "destination": {
                "destination_id": destination['destination_id'],
                "name": destination['name'],
                "country": destination['country']
            },
            "forecasts": weather_data['forecasts']
        })
    
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
        conn = get_db_connection()
        with conn.cursor() as cur:
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
            
            rows = cur.fetchall()
            if not rows:
                conn.close()
                return jsonify([])
            
            columns = [desc[0] for desc in cur.description]
            activities = [dict(zip(columns, row)) for row in rows]
        
        conn.close()
        return jsonify(activities)
    
    except Exception as e:
        print(f"ERROR in get_destination_activities: {e}")
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
    destination_id = request.args.get('destination_id', type=int)
    limit = min(int(request.args.get('limit', 10)), 50)
    
    if not query_text:
        return jsonify({"error": "Query parameter 'query' is required"}), 400
    
    try:
        # Generate query embedding using real sentence-transformers model
        query_embedding = generate_query_embedding(query_text)
        embedding_str = str(query_embedding)
        
        # Build dynamic WHERE clause for filters (using psycopg2 positional parameters)
        where_clauses = []
        params = []
        
        if min_age is not None:
            where_clauses.append("a.min_age <= %s")
            params.append(min_age)
        
        if max_age is not None:
            where_clauses.append("(a.max_age IS NULL OR a.max_age >= %s)")
            params.append(max_age)
        
        if indoor_filter is not None:
            indoor_bool = indoor_filter.lower() == 'true'
            where_clauses.append("a.indoor = %s")
            params.append(indoor_bool)
        
        if destination_id is not None:
            where_clauses.append("a.destination_id = %s")
            params.append(destination_id)
        
        where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        # Execute semantic search using psycopg2
        conn = get_db_connection()
        with conn.cursor() as cur:
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
            
            # Add embedding and limit to params (embedding used twice + limit at end)
            query_params = tuple(params + [embedding_str, embedding_str, limit])
            cur.execute(query_sql, query_params)
            
            rows = cur.fetchall()
            if not rows:
                results = []
            else:
                columns = [desc[0] for desc in cur.description]
                results = [dict(zip(columns, row)) for row in rows]
        
        conn.close()
        
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


@app.route('/admin/seed', methods=['GET', 'POST'])
def seed_database():
    """Admin endpoint to seed the database with sample destinations."""
    try:
        import requests, re, math
        from collections import Counter
        
        def preprocess_text(text):
            text = text.lower()
            text = re.sub(r'[^a-z0-9\s]', ' ', text)
            words = text.split()
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'is', 'was', 'are', 'were', 'be', 'been', 'being'}
            return [w for w in words if w not in stop_words and len(w) > 2]
        
        def simple_embedding(text, dimension=768):
            words = preprocess_text(text)
            if not words: return [0.0] * dimension
            word_counts = Counter(words)
            total_words = len(words)
            embedding = [0.0] * dimension
            for word, count in word_counts.items():
                tf = count / total_words
                idf = math.log(1 + total_words / count)
                weight = tf * idf
                for i in range(3):
                    hash_val = hash(word + str(i))
                    embedding[abs(hash_val) % dimension] += weight
            norm = math.sqrt(sum(x**2 for x in embedding))
            return [x / norm for x in embedding] if norm > 0 else embedding
        
        destinations_to_add = [
            "San Francisco",
            "Golden Gate Park",
            "Exploratorium San Francisco",
            "California Academy of Sciences",
            "Pier 39",
            "Aquarium of the Bay",
            "Children's Creativity Museum",
            "San Francisco Zoo",
            "Crissy Field",
            "Presidio Tunnel Tops"
        ]
        added = []
        
        for dest_name in destinations_to_add:
            geo_resp = requests.get("https://geocoding-api.open-meteo.com/v1/search", params={"name": dest_name, "count": 1}, timeout=10)
            geo_data = geo_resp.json()
            if not geo_data.get("results"): continue
            geo = geo_data["results"][0]
            
            wiki_resp = requests.get("https://en.wikipedia.org/w/api.php", params={
                "action": "query", "format": "json", "titles": dest_name,
                "prop": "extracts|pageprops", "exintro": True, "explaintext": True, "redirects": 1
            }, headers={"User-Agent": "FamilyAdventurePlanner/1.0"}, timeout=10)
            wiki_data = wiki_resp.json()
            pages = wiki_data.get("query", {}).get("pages", {})
            page_id = list(pages.keys())[0]
            if page_id == "-1": continue
            page = pages[page_id]
            
            extract = page.get('extract', '')[:500]
            text = f"{page.get('pageprops', {}).get('wikibase-shortdesc', '')}. {extract}"
            embedding = simple_embedding(text)
            
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO destinations (name, latitude, longitude, description, description_embedding, country, created_at)
                        VALUES (%s, %s, %s, %s, %s::vector, %s, NOW())
                        ON CONFLICT (name) DO UPDATE SET description = EXCLUDED.description, description_embedding = EXCLUDED.description_embedding
                        RETURNING destination_id""",
                        (page.get('title', dest_name), geo['latitude'], geo['longitude'], extract, embedding, geo.get('country', 'Unknown'))
                    )
                    added.append({"id": cur.fetchone()[0], "name": page.get('title', dest_name)})
                    conn.commit()
        
        return jsonify({"status": "success", "added": len(added), "destinations": added})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# Run Server
# ============================================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=True)