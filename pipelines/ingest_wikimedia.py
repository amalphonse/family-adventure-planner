"""
Family Adventure Planner - Wikimedia Ingestion Pipeline (Simplified)

Fetches destination articles from Wikimedia APIs, generates embeddings,
and loads them into Lakebase Postgres with pgvector for semantic search.

This version uses a simple TF-IDF approach instead of sentence-transformers
to avoid ML dependency issues on serverless compute.

Data Flow:
1. Read destination list (cities/attractions)
2. Call Open-Meteo Geocoding API → get coordinates
3. Call Wikimedia API → fetch article extracts and descriptions
4. Generate embeddings using simple TF-IDF (768-dim)
5. Write to Lakebase: destinations + activities tables

Usage:
    python ingest_wikimedia.py
"""

import requests
import json
from typing import List, Dict, Optional
from datetime import datetime
import pg8000.native
from databricks.sdk import WorkspaceClient
import re
import math
from collections import Counter


# ============================================================================
# Configuration
# ============================================================================

LAKEBASE_PROJECT = "family-adventure-planner"
LAKEBASE_BRANCH = "production"
LAKEBASE_DATABASE = "databricks_postgres"

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
# Simple Embedding Generation (TF-IDF based)
# ============================================================================

def preprocess_text(text: str) -> List[str]:
    """
    Tokenize and clean text for embedding.
    """
    # Lowercase and remove special characters
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    # Split into words
    words = text.split()
    # Remove common stop words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'is', 'was', 'are', 'were', 'be', 'been', 'being'}
    words = [w for w in words if w not in stop_words and len(w) > 2]
    return words


def simple_embedding(text: str, dimension: int = 768) -> List[float]:
    """
    Generate a simple but consistent embedding using TF-IDF + hashing.
    
    This creates a 768-dimensional vector that captures semantic meaning
    through term frequency and position-based weighting.
    """
    words = preprocess_text(text)
    
    if not words:
        # Return zero vector if no words
        return [0.0] * dimension
    
    # Count word frequencies
    word_counts = Counter(words)
    total_words = len(words)
    
    # Initialize embedding vector
    embedding = [0.0] * dimension
    
    # For each word, hash it to multiple dimensions and add TF-IDF weight
    for word, count in word_counts.items():
        # Term frequency
        tf = count / total_words
        
        # Simple IDF approximation (words appearing once are more important)
        idf = math.log(1 + total_words / count)
        
        weight = tf * idf
        
        # Hash word to multiple dimensions (for better distribution)
        for i in range(3):  # Use 3 hash functions
            # Simple hash function
            hash_val = hash(word + str(i))
            dim_idx = abs(hash_val) % dimension
            
            # Add weighted contribution
            embedding[dim_idx] += weight
    
    # Normalize to unit length (required for cosine similarity)
    norm = math.sqrt(sum(x**2 for x in embedding))
    if norm > 0:
        embedding = [x / norm for x in embedding]
    
    return embedding


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
    
    headers = {
        "User-Agent": "FamilyAdventurePlanner/1.0 (Educational capstone project)"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
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
    
    headers = {
        "User-Agent": "FamilyAdventurePlanner/1.0 (Educational capstone project)"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
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
# Lakebase Connection
# ============================================================================

def get_lakebase_connection():
    """
    Create a connection to Lakebase Postgres using Databricks SDK.
    
    Returns:
        pg8000 connection object
    """
    w = WorkspaceClient()
    
    # Get endpoint details
    endpoint_name = f"projects/{LAKEBASE_PROJECT}/branches/{LAKEBASE_BRANCH}/endpoints/primary"
    endpoint = w.postgres.get_endpoint(name=endpoint_name)
    host = endpoint.status.hosts.host
    
    # Generate OAuth token
    cred = w.postgres.generate_database_credential(endpoint=endpoint_name)
    token = cred.token
    
    # Connect using pg8000 (pure Python, no binary deps)
    conn = pg8000.native.Connection(
        host=host,
        port=5432,
        database=LAKEBASE_DATABASE,
        user="databricks",
        password=token,
        ssl_context=True
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
    embedding = simple_embedding(text_for_embedding)
    
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
            ON CONFLICT (name) DO UPDATE SET
                description = EXCLUDED.description,
                description_embedding = EXCLUDED.description_embedding
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
        try:
            article = fetch_wikimedia_article(attraction["title"])
            if not article or not article.get("extract"):
                continue
            
            # Generate embedding
            text_for_embedding = f"{article.get('description', '')}. {article['extract'][:500]}"
            embedding = simple_embedding(text_for_embedding)
            
            # Infer activity properties (simple heuristics)
            extract_lower = article["extract"].lower()
            is_indoor = any(keyword in extract_lower for keyword in ["museum", "indoor", "aquarium", "gallery", "theater"])
            is_kid_friendly = any(keyword in extract_lower for keyword in ["children", "kid", "family", "playground", "educational"])
            
            activity_data = {
                "destination_id": destination_id,
                "activity_name": article["title"],
                "activity_type": "attraction",
                "description": article["extract"][:1000],  # Truncate long descriptions
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
                    ON CONFLICT (destination_id, activity_name) DO UPDATE SET
                        description = EXCLUDED.description,
                        content_embedding = EXCLUDED.content_embedding
                    """,
                    activity_data
                )
                conn.commit()
            
            print(f"    ✓ Added activity: {article['title']}")
        
        except Exception as e:
            print(f"    ⚠️  Error processing activity '{attraction.get('title', 'unknown')}': {e}")
            continue


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
    print(f"Embedding: Simple TF-IDF (768-dim)")
    print(f"Destinations to process: {len(SEED_DESTINATIONS)}")
    print()
    
    # Connect to Lakebase
    print("Connecting to Lakebase...")
    conn = get_lakebase_connection()
    print("✓ Connected\n")
    
    # Process each destination
    processed_count = 0
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
                processed_count += 1
            
            print()
        
        except Exception as e:
            print(f"  ❌ Error processing {dest_name}: {e}\n")
            import traceback
            traceback.print_exc()
            continue
    
    conn.close()
    
    print("="*80)
    print(f"Pipeline Complete! Processed {processed_count}/{len(SEED_DESTINATIONS)} destinations")
    print("="*80)
    print("\nNext steps:")
    print("1. Query destinations: SELECT name, country FROM destinations;")
    print("2. Test semantic search: SELECT activity_name FROM activities ORDER BY content_embedding <=> '[...]'::vector LIMIT 5;")


if __name__ == "__main__":
    main()
