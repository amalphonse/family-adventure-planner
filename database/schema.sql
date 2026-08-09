-- Family Adventure Planner - Lakebase Schema
-- PostgreSQL 17 with pgvector extension
-- Created: 2026-08-08

-- Enable pgvector extension for semantic search
CREATE EXTENSION IF NOT EXISTS vector;

-- Users table
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trips table
CREATE TABLE trips (
    trip_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    trip_name VARCHAR(255) NOT NULL,
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Destinations table with vector embedding for Wikimedia descriptions
CREATE TABLE destinations (
    destination_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    description TEXT,
    description_embedding vector(768),  -- Semantic search on destination descriptions
    country VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Activities table with vector embedding for Wikimedia content
CREATE TABLE activities (
    activity_id SERIAL PRIMARY KEY,
    destination_id INTEGER REFERENCES destinations(destination_id) ON DELETE CASCADE,
    activity_name VARCHAR(255) NOT NULL,
    activity_type VARCHAR(100),
    description TEXT,
    content_embedding vector(768),  -- Semantic search on activity content
    min_age INTEGER,  -- Minimum recommended age
    max_age INTEGER,  -- Maximum recommended age (NULL = no max)
    indoor BOOLEAN DEFAULT FALSE,  -- Indoor activity flag
    weather_dependent BOOLEAN DEFAULT TRUE,  -- Whether activity depends on weather
    duration_minutes INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Itinerary items table
CREATE TABLE itinerary_items (
    item_id SERIAL PRIMARY KEY,
    trip_id INTEGER REFERENCES trips(trip_id) ON DELETE CASCADE,
    activity_id INTEGER REFERENCES activities(activity_id) ON DELETE SET NULL,
    scheduled_date DATE NOT NULL,
    scheduled_time TIME,
    status VARCHAR(50) DEFAULT 'planned',  -- planned, rescheduled, completed, cancelled
    notes TEXT,
    weather_rationale TEXT,  -- Why this activity was scheduled/rescheduled based on weather
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Weather snapshots table (from Open-Meteo API)
CREATE TABLE weather_snapshots (
    snapshot_id SERIAL PRIMARY KEY,
    destination_id INTEGER REFERENCES destinations(destination_id) ON DELETE CASCADE,
    forecast_date DATE NOT NULL,
    temperature_f DECIMAL(5, 2),
    precipitation_probability INTEGER,  -- 0-100%
    weather_condition VARCHAR(100),
    aqi INTEGER,  -- Air Quality Index
    uv_index INTEGER,
    wind_speed_mph DECIMAL(5, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Packing items table
CREATE TABLE packing_items (
    packing_id SERIAL PRIMARY KEY,
    trip_id INTEGER REFERENCES trips(trip_id) ON DELETE CASCADE,
    item_name VARCHAR(255) NOT NULL,
    category VARCHAR(100),  -- clothing, gear, documents, etc.
    packed BOOLEAN DEFAULT FALSE,
    weather_reason TEXT,  -- Why this item is recommended based on weather
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);