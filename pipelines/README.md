# Spark Data Pipelines

Data ingestion pipelines for the Family Adventure Planner.

## Pipelines

### `ingest_wikimedia.py`

Fetches destination articles from Wikimedia APIs, generates embeddings, and loads them into Lakebase Postgres.

**What it does:**
1. Takes a list of seed destinations (San Francisco attractions)
2. Calls Open-Meteo Geocoding API to get coordinates
3. Fetches Wikimedia article extracts and descriptions
4. Generates 768-dimensional embeddings using `sentence-transformers/all-mpnet-base-v2`
5. Inserts into Lakebase `destinations` and `activities` tables
6. Creates HNSW indexes for fast semantic search

**Seed Destinations:**
- San Francisco (city)
- Golden Gate Park
- Exploratorium
- California Academy of Sciences
- Pier 39
- Aquarium of the Bay
- Children's Creativity Museum
- San Francisco Zoo
- Crissy Field
- Presidio Tunnel Tops

**Dependencies:**
```bash
pip install sentence-transformers torch requests psycopg[binary] databricks-sdk
```

**Run:**
```python
python ingest_wikimedia.py
```

**Expected Output:**
```
===============================================================
Family Adventure Planner - Wikimedia Ingestion Pipeline
===============================================================
Embedding Model: sentence-transformers/all-mpnet-base-v2
Destinations to process: 10

Connecting to Lakebase...
✓ Connected

Processing: San Francisco
  ✓ Processed San Francisco
  ✓ Inserted destination ID: 1
  Searching for activities near San Francisco...
    ✓ Added activity: Fisherman's Wharf
    ✓ Added activity: Alcatraz Island
    ...
```

**After Running:**
- Query destinations: `SELECT name, country FROM destinations;`
- Test semantic search: `SELECT activity_name FROM activities ORDER BY content_embedding <=> '[...]'::vector LIMIT 5;`

## Future Pipelines

### `ingest_weather.py` (TODO)
Scheduled job to refresh weather forecasts from Open-Meteo API.

### `sync_to_delta.py` (TODO)
CDF (Change Data Feed) from Lakebase → Delta table for analytics.