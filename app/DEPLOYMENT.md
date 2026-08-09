# Flask API Deployment Guide

Quick guide to run and test the Family Adventure Planner Flask API.

## Prerequisites

✓ **Lakebase Database Ready**
- Project: `family-adventure-planner`
- Branch: `production`
- Database: `databricks_postgres`
- Sample data loaded: 3 destinations, 5 activities

✓ **Dependencies**
```bash
pip install flask flask-cors psycopg databricks-sdk
```

## Quick Start

### 1. Run Flask Development Server

```bash
cd app/
python app.py
```

The API will start on `http://localhost:8000`

### 2. Test Endpoints

**Health Check:**
```bash
curl http://localhost:8000/
```

**List Destinations:**
```bash
curl http://localhost:8000/destinations
```

**Search Activities:**
```bash
curl "http://localhost:8000/activities/search?query=indoor+museum&min_age=2&limit=5"
```

### 3. Run Full Test Suite

```bash
python test_api.py
```

Expected output:
```
# Family Adventure Planner - API Test Suite
============================================================
Test 1: Health Check
✓ Health check passed

Test 2: List Destinations
Found 3 destinations:
  - Golden Gate Park (United States)
  - Exploratorium (United States)
  - California Academy of Sciences (United States)
✓ List destinations passed
...
✓ ALL TESTS PASSED!
```

## API Endpoints Reference

### GET `/`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "family-adventure-planner-api",
  "version": "1.0.0"
}
```

### GET `/destinations`
List all destinations.

**Response:**
```json
[
  {
    "destination_id": 2,
    "name": "Golden Gate Park",
    "latitude": 37.7694,
    "longitude": -122.4862,
    "country": "United States",
    "description": "Golden Gate Park is an urban park..."
  }
]
```

### GET `/destinations/:id`
Get single destination details.

**Example:** `GET /destinations/2`

**Response:**
```json
{
  "destination_id": 2,
  "name": "Golden Gate Park",
  "latitude": 37.7694,
  "longitude": -122.4862,
  "country": "United States",
  "description": "...",
  "created_at": "2025-04-03T10:30:00"
}
```

### GET `/destinations/:id/activities`
Get all activities for a destination.

**Example:** `GET /destinations/2/activities`

**Response:**
```json
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
  }
]
```

### GET `/activities/search`
Semantic search over activities using vector similarity.

**Query Parameters:**
- `query` (required) — Search text (e.g., "indoor museum for toddlers")
- `min_age` (optional) — Minimum age filter
- `max_age` (optional) — Maximum age filter
- `indoor` (optional) — Filter by indoor activities (true/false)
- `limit` (optional) — Number of results (default: 10, max: 50)

**Example:**
```bash
curl "http://localhost:8000/activities/search?query=playground&min_age=2&max_age=10&indoor=false&limit=3"
```

**Response:**
```json
{
  "query": "playground",
  "filters": {
    "min_age": 2,
    "max_age": 10,
    "indoor": "false"
  },
  "count": 2,
  "results": [
    {
      "activity_id": 1,
      "activity_name": "Koret Children's Quarter Playground",
      "activity_type": "playground",
      "description": "...",
      "destination_name": "Golden Gate Park",
      "min_age": 2,
      "max_age": 12,
      "indoor": false,
      "weather_dependent": true,
      "duration_minutes": 90,
      "similarity_score": 0.95
    }
  ]
}
```

## Production Deployment

### Using Gunicorn (Recommended)

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

**Options:**
- `-w 4` — 4 worker processes
- `-b 0.0.0.0:8000` — Bind to all interfaces on port 8000
- `--timeout 120` — Request timeout (useful for slow queries)

### Environment Variables

```bash
export PORT=8000  # Override default port
export FLASK_ENV=production
```

## Databricks App Deployment

To deploy as a Databricks App:

1. Create `app.yaml`:
```yaml
command: ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"]
env:
  - name: PORT
    value: "8000"
resources:
  memory: 2Gi
  cpu: 1
```

2. Deploy:
```bash
databricks apps deploy family-adventure-planner --source-code-path ./app
```

## Troubleshooting

### Connection Error
**Problem:** `Connection refused` when testing API

**Solution:** Ensure Flask app is running:
```bash
python app.py
# Should see: "Running on http://0.0.0.0:8000"
```

### Lakebase Authentication Error
**Problem:** `psycopg.OperationalError: authentication failed`

**Solution:** Check Databricks authentication:
```bash
databricks auth login
```

### No Results from Search
**Problem:** `/activities/search` returns empty results

**Solution:** 
1. Verify data exists:
```bash
curl http://localhost:8000/destinations
```

2. Check embeddings were created:
```sql
SELECT COUNT(*) FROM activities WHERE content_embedding IS NOT NULL;
```

## Current Limitations

⚠️ **Placeholder Embeddings**
- Currently using random vectors for testing
- Search results are not semantically meaningful yet
- TODO: Replace with real `sentence-transformers` embeddings

⚠️ **No Authentication**
- API is open — add auth middleware for production

⚠️ **Single-threaded Dev Server**
- Use gunicorn for production workloads

## Next Steps

1. **Real Embeddings**: Run `pipelines/ingest_wikimedia.py` to generate real embeddings
2. **Weather Integration**: Add weather API endpoints
3. **AI Agent**: Implement itinerary generation tools
4. **Frontend**: Build React/Vue UI that calls these endpoints
5. **Authentication**: Add OAuth or API key authentication