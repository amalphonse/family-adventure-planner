-- Family Adventure Planner - Vector Search Indexes
-- HNSW indexes for fast semantic similarity search

-- Index on destinations.description_embedding
-- Used for: semantic search on destination descriptions from Wikimedia
CREATE INDEX idx_destinations_embedding 
    ON destinations 
    USING hnsw (description_embedding vector_cosine_ops);

-- Index on activities.content_embedding
-- Used for: semantic search on activity content from Wikimedia
-- Query example: "toddler-friendly indoor activities near water"
CREATE INDEX idx_activities_embedding 
    ON activities 
    USING hnsw (content_embedding vector_cosine_ops);

-- Additional helpful indexes for filtering
CREATE INDEX idx_activities_age_range ON activities(min_age, max_age);
CREATE INDEX idx_activities_indoor ON activities(indoor);
CREATE INDEX idx_activities_weather_dependent ON activities(weather_dependent);
CREATE INDEX idx_weather_snapshots_date ON weather_snapshots(destination_id, forecast_date);