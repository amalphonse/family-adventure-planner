# Family Adventure Planner

An AI-powered trip planning assistant that builds weather-aware, kid-friendly itineraries using semantic search over destination content.

## Capstone Requirements Status

### ✅ 1. Spark Data Pipeline
**Status:** COMPLETE
- **File:** `pipelines/ingest_wikimedia.py`
- **Description:** Python pipeline that runs on Databricks compute
- **What it does:**
  - Fetches data from third-party APIs
  - Processes unstructured text from Wikipedia
  - Generates embeddings using TF-IDF
  - Loads into Lakebase Postgres
- **Tested:** API calls and embedding generation verified working

### ✅ 2. Third-Party API Integration  
**Status:** COMPLETE
- **APIs Used:**
  - **Open-Meteo Geocoding API** - Converts location names to coordinates
  - **Wikimedia API** - Fetches article content and descriptions
  - **Wikimedia Search API** - Discovers attractions and activities
- **Verification:** All API endpoints tested and working successfully

### ✅ 3. Unstructured Data Processing
**Status:** COMPLETE
- **Source:** Wikipedia article text (extracts, descriptions)
- **Processing:** TF-IDF-based embedding generation (768-dimensional vectors)
- **Output:** Normalized vectors suitable for pgvector similarity search
- **Verification:** Embeddings generated successfully, cosine similarity computed

### ⚠️ 4. Databricks App with Frontend
**Status:** IN PROGRESS - Need to convert
- **Current:** Flask app with HTML/JS frontend (runs locally)
- **Files:** `app/app.py`, `app/static/*`
- **Next Step:** Create `app.yaml` and deploy with `databricks apps deploy`

### ❌ 5. AI Agent with Tools
**Status:** NOT STARTED
- **Plan:** Build agent with tools for:
  - `search_activities()` - Semantic search with filters
  - `create_itinerary()` - Generate trip plans
  - `get_weather()` - Check forecast
  - `reschedule_activity()` - Weather-based rescheduling

### ❌ 6. Change Data Feed (CDF) from Lakebase → Delta
**Status:** NOT STARTED
- **Plan:**
  - Enable CDF on Lakebase tables
  - Sync changes to Delta table
  - Build analytics on usage/agent actions

## Current Architecture

### Data Layer (Lakebase Postgres)
```
destinations (pgvector)
  ├── destination_id (PK)
  ├── name, description
  ├── description_embedding::vector(768)
  └── latitude, longitude, country

activities (pgvector)
  ├── activity_id (PK)
  ├── destination_id (FK)
  ├── activity_name, description
  ├── content_embedding::vector(768)
  └── min_age, max_age, indoor, duration_minutes
```

### API Layer (Flask)
**Endpoints:**
- `GET /` - Serves frontend UI
- `GET /health` - Health check
- `GET /destinations` - List all destinations
- `GET /activities/search` - Semantic search with filters

**Query Example:**
```bash
curl "http://localhost:8000/activities/search?query=indoor+museum&min_age=2&limit=5"
```

### Frontend (HTML/JS)
- **Files:** `app/static/index.html`, `styles.css`, `app.js`
- **Features:**
  - Search interface with natural language queries
  - Age range and indoor/outdoor filters
  - Destination browsing cards
  - Real-time API integration

## Running the Project

### 1. Run Data Pipeline
```bash
# Install dependencies
pip install requests psycopg[binary]

# Execute pipeline
python pipelines/ingest_wikimedia.py
```

### 2. Start Flask API + Frontend
```bash
cd app/
python app.py

# Visit http://localhost:8000
```

### 3. Test API
```bash
cd app/
python test_api.py
```

## Project Structure

```
family-adventure-planner/
├── database/
│   └── schema.sql              # Lakebase table definitions
├── pipelines/
│   ├── ingest_wikimedia.py     # ✅ Working API + embedding pipeline
│   └── load_sample_data.py     # Initial sample data
├── app/
│   ├── app.py                  # Flask REST API
│   ├── test_api.py             # API tests
│   ├── DEPLOYMENT.md           # Deployment guide
│   └── static/
│       ├── index.html          # Frontend UI
│       ├── styles.css          # Styling
│       ├── app.js              # Frontend logic
│       └── README.md           # Frontend docs
└── README.md                   # This file
```

## Technologies

- **Lakebase Postgres 17** - Serverless Postgres with autoscaling
- **pgvector** - Vector similarity search
- **Apache Spark** - Data pipeline (Python-based)
- **Flask** - REST API
- **HTML/CSS/JavaScript** - Frontend
- **Open-Meteo** - Weather & geocoding data
- **Wikimedia APIs** - Unstructured content source

## Next Steps

1. **Convert to Databricks App**
   - Create `app/app.yaml`
   - Deploy with `databricks apps deploy`

2. **Build AI Agent**
   - Create `app/agent.py`
   - Implement tools for search, itinerary generation, rescheduling
   - Add tool execution logging

3. **Set up CDF → Delta**
   - Enable CDF on Lakebase tables
   - Create sync job to Delta
   - Build usage analytics dashboard

## Sample Data

The database currently contains:
- **3 destinations** (San Francisco area)
- **5 activities** (museums, parks, aquariums)
- All with **768-dim embeddings** for semantic search
- Metadata: age ranges, indoor/outdoor, duration

## Demo Queries

**Search for toddler-friendly indoor activities:**
```sql
SELECT 
    activity_name,
    description,
    1 - (content_embedding <=> '[0.1, 0.2, ...]'::vector) as similarity
FROM activities
WHERE min_age <= 2 AND indoor = true
ORDER BY similarity DESC
LIMIT 5;
```

**Find destinations near coordinates:**
```sql
SELECT name, country,
    ST_Distance(
        ST_MakePoint(longitude, latitude)::geography,
        ST_MakePoint(-122.4194, 37.7749)::geography
    ) / 1000.0 as distance_km
FROM destinations
ORDER BY distance_km
LIMIT 5;
```

## License

Capstone project for educational purposes.
