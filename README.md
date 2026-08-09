# Family Adventure Planner

An AI-powered trip planning assistant that builds weather-aware, kid-friendly itineraries using semantic search over destination content.

## Overview

This capstone project combines:
- **Lakebase Postgres** with pgvector for semantic search
- **Spark data pipeline** for ingesting Wikimedia articles and weather data
- **Databricks App** with Flask REST API
- **AI Agent** with tools for itinerary generation and weather-based rescheduling
- **Change Data Feed (CDF)** from Lakebase to Delta for analytics

## Features

### Core Capabilities
- 🌤️ **Weather-Aware Planning**: Real-time weather checks with automatic rescheduling
- 👶 **Kid-Friendly Filtering**: Age-appropriate activities (e.g., "things to do with 2 and 4 year olds")
- 🔍 **Semantic Search**: Vector search over Wikimedia content for relevant attractions
- 🤖 **AI Agent**: Intelligent itinerary building with natural language explanations
- 🎒 **Smart Packing Lists**: Weather-based packing recommendations

### Example Use Case
**User**: "I'm planning a day out with my kids aged 2 and 4 in San Francisco tomorrow"

**Agent**:
1. Checks tomorrow's weather (Open-Meteo API)
2. Searches for toddler-friendly activities (semantic search on Wikimedia)
3. Generates 4-hour itinerary with nap windows
4. Warns: "52°F and windy near the waterfront — bring layers and a windbreaker"
5. Suggests backup indoor options if forecast worsens

## Architecture

### Data Pipeline (Spark)
```
Wikimedia API → Extract articles → Generate embeddings → Lakebase Postgres
Open-Meteo API → Weather forecasts → Lakebase Postgres
```

### Lakebase Schema
- `users` — User profiles
- `trips` — Trip metadata
- `destinations` — Destinations with embedded descriptions (vector search)
- `activities` — Activities with embedded content (vector search) + age/weather filters
- `itinerary_items` — Scheduled activities with weather rationale
- `weather_snapshots` — Hourly weather forecasts
- `packing_items` — Packing lists with weather reasons

### Flask REST API

**Endpoints:**
```
GET  /                          - Health check
GET  /destinations              - List all destinations
GET  /destinations/:id          - Get destination details
GET  /destinations/:id/activities - Get activities for a destination
GET  /activities/search         - Semantic search over activities
```

**Example: Semantic Search**
```bash
curl "http://localhost:8000/activities/search?query=indoor+museum&min_age=2&limit=5"
```

Returns activities ranked by vector similarity with optional filters:
- `min_age` / `max_age` — Age range
- `indoor` — Indoor only (true/false)
- `limit` — Number of results (default: 10, max: 50)

### AI Agent Tools
- `get_current_weather(destination)` — Query Open-Meteo API
- `search_activities(query, age_range, weather)` — Semantic search + filters
- `generate_itinerary(trip_id, date)` — Build day plan
- `reschedule_activity(item_id, new_date, reason)` — Weather-based rescheduling
- `build_packing_list(trip_id)` — Weather-aware packing suggestions

## Third-Party APIs

- **Open-Meteo Geocoding API** — Destination names → coordinates
- **Open-Meteo Weather API** — Hourly forecasts (7-day)
- **Open-Meteo Air Quality API** — AQI, UV index, pollen
- **Wikimedia APIs** — Destination descriptions and attractions (unstructured data source)

*All APIs are free for non-commercial use, no API key required.*

## Project Structure

```
family-adventure-planner/
├── database/
│   ├── schema.sql              # DDL for all tables
│   ├── indexes.sql             # Vector search indexes
│   └── migrations/             # Schema version control
├── pipelines/
│   ├── ingest_wikimedia.py     # Spark job: Wikimedia → Lakebase
│   └── ingest_weather.py       # Spark job: Open-Meteo → Lakebase
├── app/
│   ├── app.py                  # Flask REST API
│   ├── app.yaml                # Databricks App config
│   ├── agent.py                # AI agent with tools
│   └── requirements.txt
└── README.md
```

## Setup

### 1. Lakebase Project
Project name: `family-adventure-planner`
Database: `databricks_postgres`
Host: `ep-calm-river-d891evds.database.us-east-2.cloud.databricks.com`

### 2. Initialize Schema
```bash
psql -h <host> -U databricks -d databricks_postgres -f database/schema.sql
psql -h <host> -U databricks -d databricks_postgres -f database/indexes.sql
```

### 3. Run Data Pipeline
Execute Spark jobs to populate destinations and activities:
```bash
databricks bundle run pipelines/ingest_wikimedia
```

### 4. Deploy App
```bash
apps deploy family-adventure-planner
```

## Development Roadmap

- [x] Lakebase schema with pgvector
- [x] GitHub repository setup
- [x] Sample data loaded (3 destinations, 5 activities with embeddings)
- [x] Flask REST API with semantic search
- [x] Vector search working (pgvector HNSW indexes)
- [ ] Spark pipeline: Wikimedia ingestion (code ready, pending ML dependencies)
- [ ] Spark pipeline: Weather API integration
- [ ] Real embeddings (replace placeholders with sentence-transformers)
- [ ] AI agent tools
- [ ] CDF → Delta analytics
- [ ] Frontend UI

## Technologies

- **Databricks Lakebase Postgres 17** — Serverless Postgres with autoscaling
- **pgvector** — Vector similarity search
- **Apache Spark** — Data pipeline
- **Flask** — REST API
- **sentence-transformers** — Text embeddings
- **Open-Meteo** — Weather data
- **Wikimedia APIs** — Unstructured content

## License

Capstone project for educational purposes.