# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# DBTITLE 1,Install Dependencies
# MAGIC %pip install psycopg2-binary requests databricks-sdk --quiet

# COMMAND ----------

# DBTITLE 1,Connect to Lakebase Database
import psycopg2

# Lakebase connection details (static credentials)
LAKEBASE_HOST = "ep-calm-river-d891evds.database.us-east-2.cloud.databricks.com"
LAKEBASE_DATABASE = "databricks_postgres"
LAKEBASE_USER = "user"
LAKEBASE_PASSWORD = "npg_ZlOMFTehK8J3"

# Connect using psycopg2
conn = psycopg2.connect(
    host=LAKEBASE_HOST,
    port=5432,
    dbname=LAKEBASE_DATABASE,
    user=LAKEBASE_USER,
    password=LAKEBASE_PASSWORD,
    sslmode="require"
)

print("✅ Connected to Lakebase database")
print(f"   Host: {LAKEBASE_HOST}")
print(f"   Database: {LAKEBASE_DATABASE}")

# COMMAND ----------

# DBTITLE 1,Create Database Tables
# Create destinations table
print("Creating destinations table...")
with conn.cursor() as cur:
    cur.execute("""
        CREATE TABLE IF NOT EXISTS destinations (
            destination_id SERIAL PRIMARY KEY,
            name VARCHAR(255) UNIQUE NOT NULL,
            latitude FLOAT NOT NULL,
            longitude FLOAT NOT NULL,
            country VARCHAR(100),
            description TEXT,
            description_embedding vector(768),
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    print("✅ Destinations table created")
    
    # Create activities table
    print("Creating activities table...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS activities (
            activity_id SERIAL PRIMARY KEY,
            destination_id INTEGER REFERENCES destinations(destination_id) ON DELETE CASCADE,
            activity_name VARCHAR(255) NOT NULL,
            activity_type VARCHAR(100),
            description TEXT,
            content_embedding vector(768),
            min_age INTEGER,
            max_age INTEGER,
            indoor BOOLEAN,
            weather_dependent BOOLEAN,
            duration_minutes INTEGER,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    print("✅ Activities table created")
    
    conn.commit()

print("\n🎉 Database schema created successfully!")

# COMMAND ----------

# DBTITLE 1,Verify Database Contents
with conn.cursor() as cur:
    # Check destinations count
    cur.execute("SELECT COUNT(*) FROM destinations")
    dest_count = cur.fetchone()[0]
    print(f"📊 Total destinations in database: {dest_count}")
    
    # Check activities count
    cur.execute("SELECT COUNT(*) FROM activities")
    activity_count = cur.fetchone()[0]
    print(f"🎯 Total activities in database: {activity_count}")
    
    # Show first few destinations
    cur.execute("""
        SELECT destination_id, name, latitude, longitude, country 
        FROM destinations 
        ORDER BY destination_id 
        LIMIT 5
    """)
    
    results = cur.fetchall()
    if results:
        print(f"\n📍 Sample destinations ({len(results)} shown):")
        for row in results:
            dest_id, name, lat, lon, country = row
            print(f"  - {name} ({country}) - ID: {dest_id}")
    else:
        print("\n📍 No destinations to display")

conn.close()
print("\n✅ Database verified! You can now use the Family Adventure Planner app.")

# COMMAND ----------

