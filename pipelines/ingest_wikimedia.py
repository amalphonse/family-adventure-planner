"""
Family Adventure Planner - Wikimedia Ingestion Pipeline

Fetches destination articles from Wikimedia APIs, generates embeddings,
and loads them into Lakebase Postgres with pgvector for semantic search.

Data Flow:
1. Read destination list (cities/attractions)
2. Call Open-Meteo Geocoding API → get coordinates
3. Call Wikimedia API → fetch article extracts and descriptions
4. Generate embeddings using sentence-transformers
5. Write to Lakebase: destinations + activities tables

Usage:
    spark-submit ingest_wikimedia.py
"""

import requests
import json
from typing import List, Dict, Optional
from datetime import datetime

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, lit, udf, explode, array
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, 
    IntegerType, BooleanType, ArrayType, TimestampType
)

from sentence_transformers import SentenceTransformer
import psycopg
from databricks.sdk import WorkspaceClient


# ============================================================================
# Configuration
# ============================================================================

LAKEBASE_PROJECT = "family-adventure-planner"
LAKEBASE_BRANCH = "production"
LAKEBASE_DATABASE = "databricks_postgres"

# Embedding model (768-dimensional)
EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"

# Sample destinations to seed the database
SEED_DESTINATIONS = [
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


# ============================================================================
# API Clients
# ============================================================================

def geocode_location(location_name: str) -> Optional[Dict]:
    """
    Get coordinates for a location using Open-Meteo Geocoding API.
    
    Returns:
        {"latitude": 37.7749, "longitude": -122.4194, "country": "United States"}
    """
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": location_name, "count": 1, "language": "en", "format": "json"}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("results"):
            result = data["results"][0]
            return {
                "latitude": result.get("latitude"),
                "longitude": result.get("longitude"),
                "country": result.get("country", "Unknown")
            }
    except Exception as e:
        print(f"Geocoding error for '{location_name}': {e}")
    
    return None


def fetch_wikimedia_article(title: str) -> Optional[Dict]:
    """
    Fetch article extract and metadata from Wikimedia API.
    
    Returns:
        {
            "title": "Golden Gate Park",
            "extract": "Golden Gate Park is an urban park...",
            "description": "Urban park in San Francisco",
            "url": "https://en.wikipedia.org/wiki/Golden_Gate_Park"
        }
    """
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "titles": title,
        "prop": "extracts|pageprops",
        "exintro": True,
        "explaintext": True,
        "redirects": 1
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        pages = data.get("query", {}).get("pages", {})
        if pages:
            page_id = list(pages.keys())[0]
            page = pages[page_id]
            
            if page_id != "-1":  # Valid page found
                return {
                    "title": page.get("title", title),
                    "extract": page.get("extract", ""),
                    "description": page.get("pageprops", {}).get("wikibase-shortdesc", ""),
                    "url": f"https://en.wikipedia.org/wiki/{page.get('title', '').replace(' ', '_')}"
                }
    except Exception as e:
        print(f"Wikimedia API error for '{title}': {e}")
    
    return None


def search_wikimedia_attractions(location: str, max_results: int = 5) -> List[Dict]:
    """
    Search for attractions and activities near a location.
    
    Returns list of article titles and descriptions.
    """
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srsearch": f"{location} attractions activities children family",
        "srlimit": max_results
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for item in data.get("query", {}).get("search", []):
            results.append({
                "title": item.get("title"),
                "snippet": item.get("snippet", "")
            })
        return results
    except Exception as e:
        print(f"Search error for '{location}': {e}")
        return []


# ============================================================================
# Embedding Generation
# ============================================================================

def generate_embeddings(texts: List[str], model_name: str = EMBEDDING_MODEL) -> List[List[float]]:
    """
    Generate embeddings for a list of texts using sentence-transformers.
    
    Returns:
        List of 768-dimensional embeddings
    """
    model = SentenceTransformer(model_name)
    embeddings = model.encode(texts, show_progress_bar=True)
    return embeddings.tolist()


# ============================================================================
# Lakebase Connection
# ============================================================================

def get_lakebase_connection():
    """
    Create a connection to Lakebase Postgres using Databricks SDK.
    
    Returns:
        psycopg connection object
    """
    w = WorkspaceClient()
    
    # Get endpoint details
    endpoint_name = f"projects/{LAKEBASE_PROJECT}/branches/{LAKEBASE_BRANCH}/endpoints/primary"
    endpoint = w.postgres.get_endpoint(name=endpoint_name)
    host = endpoint.status.hosts.host
    
    # Generate OAuth token
    cred = w.postgres.generate_database_credential(endpoint=endpoint_name)
    token = cred.token
    
    # Connect
    conn = psycopg.connect(
        host=host,
        port=5432,
        dbname=LAKEBASE_DATABASE,
        user="databricks",
        password=token,
        sslmode="require"
    )
    
    return conn


# ============================================================================
# Data Processing Pipeline
# ============================================================================

def process_destination(destination_name: str) -> Dict:
    """
    Full processing pipeline for a single destination:
    1. Geocode location
    2. Fetch Wikimedia article
    3. Generate embedding
    
    Returns:
        Dictionary with all destination data ready for DB insert
    """
    print(f"Processing: {destination_name}")
    
    # Step 1: Geocode
    geo = geocode_location(destination_name)
    if not geo:
        print(f"  ⚠️  Geocoding failed for {destination_name}")
        return None
    
    # Step 2: Fetch article
    article = fetch_wikimedia_article(destination_name)
    if not article:
        print(f"  ⚠️  No Wikimedia article found for {destination_name}")
        return None
    
    # Step 3: Generate embedding on description + extract
    text_for_embedding = f"{article['description']}. {article['extract'][:500]}"
    embedding = generate_embeddings([text_for_embedding])[0]
    
    print(f"  ✓ Processed {destination_name}")
    
    return {
        "name": article["title"],
        "latitude": geo["latitude"],
        "longitude": geo["longitude"],
        "description": article["extract"],
        "description_embedding": embedding,
        "country": geo["country"],
        "created_at": datetime.utcnow()
    }


def insert_destination_to_lakebase(conn, destination: Dict) -> int:
    """
    Insert a destination into Lakebase and return its ID.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO destinations (name, latitude, longitude, description, description_embedding, country, created_at)
            VALUES (%(name)s, %(latitude)s, %(longitude)s, %(description)s, %(description_embedding)s::vector, %(country)s, %(created_at)s)
            ON CONFLICT (name) DO NOTHING
            RETURNING destination_id
            """,
            destination
        )
        result = cur.fetchone()
        conn.commit()
        return result[0] if result else None


def process_activities_for_destination(destination_id: int, destination_name: str, conn):
    """
    Search for activities near a destination and insert them.
    """
    print(f"  Searching for activities near {destination_name}...")
    
    # Search for related attractions
    attractions = search_wikimedia_attractions(destination_name, max_results=5)
    
    for attraction in attractions:
        article = fetch_wikimedia_article(attraction["title"])
        if not article:
            continue
        
        # Generate embedding
        text_for_embedding = f"{article['description']}. {article['extract'][:500]}"
        embedding = generate_embeddings([text_for_embedding])[0]
        
        # Infer activity properties (simple heuristics)
        is_indoor = any(keyword in article["extract"].lower() for keyword in ["museum", "indoor", "aquarium", "gallery"])
        is_kid_friendly = any(keyword in article["extract"].lower() for keyword in ["children", "kid", "family", "playground"])
        
        activity_data = {
            "destination_id": destination_id,
            "activity_name": article["title"],
            "activity_type": "attraction",
            "description": article["extract"],
            "content_embedding": embedding,
            "min_age": 0 if is_kid_friendly else 5,
            "max_age": None,
            "indoor": is_indoor,
            "weather_dependent": not is_indoor,
            "duration_minutes": 120,
            "created_at": datetime.utcnow()
        }
        
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO activities 
                (destination_id, activity_name, activity_type, description, content_embedding, 
                 min_age, max_age, indoor, weather_dependent, duration_minutes, created_at)
                VALUES 
                (%(destination_id)s, %(activity_name)s, %(activity_type)s, %(description)s, 
                 %(content_embedding)s::vector, %(min_age)s, %(max_age)s, %(indoor)s, 
                 %(weather_dependent)s, %(duration_minutes)s, %(created_at)s)
                ON CONFLICT DO NOTHING
                """,
                activity_data
            )
            conn.commit()
        
        print(f"    ✓ Added activity: {article['title']}")


# ============================================================================
# Main Pipeline
# ============================================================================

def main():
    """
    Main pipeline execution:
    1. Process seed destinations
    2. Insert into Lakebase
    3. Process activities for each destination
    """
    print("="*80)
    print("Family Adventure Planner - Wikimedia Ingestion Pipeline")
    print("="*80)
    print(f"Embedding Model: {EMBEDDING_MODEL}")
    print(f"Destinations to process: {len(SEED_DESTINATIONS)}")
    print()
    
    # Connect to Lakebase
    print("Connecting to Lakebase...")
    conn = get_lakebase_connection()
    print("✓ Connected\n")
    
    # Process each destination
    for dest_name in SEED_DESTINATIONS:
        try:
            # Process destination
            dest_data = process_destination(dest_name)
            if not dest_data:
                continue
            
            # Insert into Lakebase
            dest_id = insert_destination_to_lakebase(conn, dest_data)
            if dest_id:
                print(f"  ✓ Inserted destination ID: {dest_id}")
                
                # Process activities
                process_activities_for_destination(dest_id, dest_name, conn)
            
            print()
        
        except Exception as e:
            print(f"  ❌ Error processing {dest_name}: {e}\n")
            continue
    
    conn.close()
    
    print("="*80)
    print("Pipeline Complete!")
    print("="*80)
    print("\nNext steps:")
    print("1. Query destinations: SELECT name, country FROM destinations;")
    print("2. Test semantic search: SELECT activity_name FROM activities ORDER BY content_embedding <=> '[...]'::vector LIMIT 5;")
    print("3. Build Flask API with /activities/search endpoint")


if __name__ == "__main__":
    main()