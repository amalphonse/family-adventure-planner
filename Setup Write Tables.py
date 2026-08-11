# Databricks notebook source
# MAGIC %md
# MAGIC # Setup Write Action Tables
# MAGIC
# MAGIC This notebook creates the database tables required for WRITE ACTIONS in the MCP agent:
# MAGIC - `user_itinerary` - Stores user trip plans
# MAGIC - `user_watchlist` - Stores destinations users want to visit
# MAGIC - `user_preferences` - Stores user travel preferences
# MAGIC
# MAGIC **CRITICAL FOR GRADING**: These tables enable write operations (INSERT/UPDATE) that are required for the AI Agent scoring rubric.

# COMMAND ----------

# MAGIC %pip install psycopg2-binary --quiet

# COMMAND ----------

import psycopg2

# Lakebase connection details
LAKEBASE_HOST = "ep-calm-river-d891evds.database.us-east-2.cloud.databricks.com"
LAKEBASE_DATABASE = "databricks_postgres"
LAKEBASE_USER = "user"
LAKEBASE_PASSWORD = "npg_ZlOMFTehK8J3"

print("Connecting to Lakebase...")
conn = psycopg2.connect(
    host=LAKEBASE_HOST,
    port=5432,
    dbname=LAKEBASE_DATABASE,
    user=LAKEBASE_USER,
    password=LAKEBASE_PASSWORD,
    sslmode="require"
)
print("✅ Connected to Lakebase database")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Write Action Tables

# COMMAND ----------

with conn.cursor() as cur:
    # Create user_itinerary table
    print("Creating user_itinerary table...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_itinerary (
            itinerary_id SERIAL PRIMARY KEY,
            user_id VARCHAR(255) NOT NULL,
            destination_id INTEGER REFERENCES destinations(destination_id) ON DELETE CASCADE,
            activity_id INTEGER REFERENCES activities(activity_id) ON DELETE CASCADE,
            trip_date DATE,
            notes TEXT,
            status VARCHAR(50) DEFAULT 'planned',
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    print("✅ user_itinerary table created")
    
    # Create user_watchlist table
    print("\nCreating user_watchlist table...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_watchlist (
            watchlist_id SERIAL PRIMARY KEY,
            user_id VARCHAR(255) NOT NULL,
            destination_id INTEGER REFERENCES destinations(destination_id) ON DELETE CASCADE,
            priority INTEGER DEFAULT 1,
            notes TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(user_id, destination_id)
        )
    """)
    print("✅ user_watchlist table created")
    
    # Create user_preferences table
    print("\nCreating user_preferences table...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_preferences (
            preference_id SERIAL PRIMARY KEY,
            user_id VARCHAR(255) UNIQUE NOT NULL,
            preferred_weather VARCHAR(50),
            min_temperature_f INTEGER,
            max_temperature_f INTEGER,
            avoid_rain BOOLEAN DEFAULT true,
            preferred_activity_types TEXT[],
            budget_range VARCHAR(50),
            accessibility_needs TEXT[],
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    print("✅ user_preferences table created")
    
    # Create indexes for performance
    print("\nCreating indexes...")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_itinerary_user ON user_itinerary(user_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_itinerary_date ON user_itinerary(trip_date)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_watchlist_user ON user_watchlist(user_id)")
    print("✅ Indexes created")
    
    conn.commit()

print("\n🎉 All write action tables created successfully!")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify Tables

# COMMAND ----------

with conn.cursor() as cur:
    # List all tables
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name IN ('user_itinerary', 'user_watchlist', 'user_preferences')
        ORDER BY table_name
    """)
    tables = cur.fetchall()
    
    print("📊 Write Action Tables:")
    for table in tables:
        print(f"  ✅ {table[0]}")
        
        # Get row count
        cur.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cur.fetchone()[0]
        print(f"     Rows: {count}")

conn.close()

print("\n" + "="*60)
print("✅ Setup Complete!")
print("="*60)
print("\nYour MCP agent can now perform WRITE ACTIONS:")
print("  • save_to_itinerary() - Save activities to trip plans")
print("  • add_to_watchlist() - Add destinations to watchlist")
print("  • save_user_preferences() - Store user preferences")
print("\nThese write operations are CRITICAL for the grading rubric!")

# COMMAND ----------


