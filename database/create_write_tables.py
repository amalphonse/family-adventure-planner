#!/usr/bin/env python3
"""
Create Write Action Tables for Family Adventure Planner
Adds tables for user_itinerary, user_watchlist, and user_preferences
These tables enable the MCP agent to perform write operations.
"""

import psycopg2
import sys

# Lakebase connection details (same as main app)
LAKEBASE_HOST = "ep-calm-river-d891evds.database.us-east-2.cloud.databricks.com"
LAKEBASE_DATABASE = "databricks_postgres"
LAKEBASE_USER = "user"
LAKEBASE_PASSWORD = "npg_ZlOMFTehK8J3"

def create_write_tables():
    """Create tables for write operations"""
    try:
        # Connect to Lakebase
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
        
        with conn.cursor() as cur:
            # Create user_itinerary table
            print("\nCreating user_itinerary table...")
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
            print("Creating user_watchlist table...")
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
            print("Creating user_preferences table...")
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
            
            # Create indexes for better query performance
            print("\nCreating indexes...")
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_itinerary_user 
                ON user_itinerary(user_id)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_itinerary_date 
                ON user_itinerary(trip_date)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_watchlist_user 
                ON user_watchlist(user_id)
            """)
            print("✅ Indexes created")
            
            conn.commit()
        
        # Verify tables
        print("\n📊 Verifying tables...")
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('user_itinerary', 'user_watchlist', 'user_preferences')
                ORDER BY table_name
            """)
            tables = cur.fetchall()
            for table in tables:
                print(f"  ✅ {table[0]}")
        
        conn.close()
        print("\n🎉 Write action tables created successfully!")
        print("\nThese tables enable:")
        print("  - save_to_itinerary() - Save activities to user's trip plan")
        print("  - add_to_watchlist() - Add destinations to user's watchlist")
        print("  - save_user_preferences() - Store user preferences for recommendations")
        return True
        
    except Exception as e:
        print(f"\n❌ Error creating tables: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_write_tables()
    sys.exit(0 if success else 1)
