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

# Cache connection details (tokens expire, so we'll refresh as needed)
_connection_cache = {}


def get_db_connection():
    """
    Get a fresh database connection to Lakebase using pg8000 (pure Python).
    Uses Databricks REST API to get endpoint details and generate credentials.
    """
    import os
    import requests
    
    # Create WorkspaceClient - it handles auth automatically in Databricks Apps
    w = WorkspaceClient()
    
    # Get workspace URL
    workspace_url = w.config.host
    if not workspace_url:
        workspace_url = os.environ.get('DATABRICKS_HOST', '')
    
    # Get auth token - try multiple sources
    token_source = None
    
    # Method 1: Environment variable (Databricks Apps set this)
    token_source = os.environ.get('DATABRICKS_TOKEN')
    
    # Method 2: From SDK config
    if not token_source:
        try:
            # The SDK's config.authenticate() returns auth headers
            w.config.authenticate()
            if hasattr(w.config, 'token') and callable(w.config.token):
                token_source = w.config.token()
            elif hasattr(w.config, 'token'):
                token_source = w.config.token
        except:
            pass
    
    # Method 3: Use SDK's internal API client to make the calls
    # (it handles auth automatically)
    if not token_source:
        # Fall back to using the SDK's API client which handles auth
        try:
            # Use the SDK's internal HTTP client
            api_client = w.api_client
            token_source = "SDK_INTERNAL"  # Signal to use SDK client below
        except:
            raise Exception("Cannot get Databricks authentication token. Tried: env var, SDK config, SDK API client.")
    
    # Use REST API to get Lakebase endpoint details
    endpoint_path = f"projects/{LAKEBASE_PROJECT}/branches/{LAKEBASE_BRANCH}/endpoints/primary"
    
    # Get endpoint info
    if token_source == "SDK_INTERNAL":
        # Use SDK's internal API client (handles auth automatically)
        endpoint_data = api_client.do(
            'GET',
            f"/api/2.0/lakebase/postgres/endpoints/{endpoint_path}"
        )
    else:
        resp = requests.get(
            f"{workspace_url}/api/2.0/lakebase/postgres/endpoints/{endpoint_path}",
            headers={"Authorization": f"Bearer {token_source}"},
            timeout=10
        )
        if resp.status_code != 200:
            raise Exception(f"Cannot get Lakebase endpoint: {resp.status_code} - {resp.text}")
        endpoint_data = resp.json()
    
    host = endpoint_data.get('status', {}).get('hosts', {}).get('host')
    
    if not host:
        raise Exception("Lakebase endpoint host not found in response")
    
    # Generate database credential
    if token_source == "SDK_INTERNAL":
        cred_data = api_client.do(
            'POST',
            "/api/2.0/lakebase/postgres/credentials/generate",
            data={"endpoint": endpoint_path}
        )
    else:
        cred_resp = requests.post(
            f"{workspace_url}/api/2.0/lakebase/postgres/credentials/generate",
            headers={"Authorization": f"Bearer {token_source}"},
            json={"endpoint": endpoint_path},
            timeout=10
        )
        if cred_resp.status_code != 200:
            raise Exception(f"Cannot generate Lakebase credential: {cred_resp.status_code} - {cred_resp.text}")
        cred_data = cred_resp.json()
    
    db_token = cred_data.get('token')
    
    if not db_token:
        raise Exception("Database token not found in credential response")
    
    # Create connection using pg8000 (pure Python, no binary deps)
    conn = pg8000.native.Connection(
        host=host,
        port=5432,
        database=LAKEBASE_DATABASE,
        user="databricks",
        password=db_token,
        ssl_context=True
    )
    
    return conn


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
    destination_id = request.args.get('destination_id', type=int)
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
        
        if destination_id is not None:
            where_clauses.append("a.destination_id = %s")
            params.insert(-1, destination_id)
        
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
            
            conn = get_db_connection()
            try:
                result = conn.run(
                    """INSERT INTO destinations (name, latitude, longitude, description, description_embedding, country, created_at)
                    VALUES (:name, :lat, :lon, :desc, :emb::vector, :country, NOW())
                    ON CONFLICT (name) DO UPDATE SET description = EXCLUDED.description, description_embedding = EXCLUDED.description_embedding
                    RETURNING destination_id""",
                    name=page.get('title', dest_name),
                    lat=geo['latitude'],
                    lon=geo['longitude'],
                    desc=extract,
                    emb=str(embedding),
                    country=geo.get('country', 'Unknown')
                )
                dest_id = result[1][0] if len(result) > 1 else None
                added.append({"id": dest_id, "name": page.get('title', dest_name)})
            finally:
                conn.close()
        
        return jsonify({"status": "success", "added": len(added), "destinations": added})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# Run Server
# ============================================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=True)