# Databricks notebook source
# DBTITLE 1,Install psycopg
# MAGIC %pip install -q psycopg[binary]

# COMMAND ----------

# DBTITLE 1,Load destinations from CSV into Lakebase
import psycopg
import csv

# Lakebase connection details (from app.yaml)
host = "ep-calm-river-d891evds.database.us-east-2.cloud.databricks.com"
database = "databricks_postgres"
user = "user"
password = "npg_ZlOMFTehK8J3"

print("📂 Reading CSV file...")
with open("/Workspace/Users/anju.chinniah@gmail.com/family-adventure-planner/destinations.csv", "r") as f:
    reader = csv.DictReader(f)
    destinations = list(reader)

print(f"✅ Found {len(destinations)} destinations\n")

print("🔌 Connecting to Lakebase...")
with psycopg.connect(
    host=host,
    port=5432,
    dbname=database,
    user=user,
    password=password,
    sslmode="require"
) as conn:
    with conn.cursor() as cur:
        print("✅ Connected!\n")
        
        # Check current count
        cur.execute("SELECT COUNT(*) FROM destinations")
        before_count = cur.fetchone()[0]
        print(f"📊 Current destinations in database: {before_count}")
        
        if before_count > 0:
            print("⚠️  Database already has data. Do you want to:")
            print("   1. Skip loading (data already exists)")
            print("   2. Clear and reload all destinations")
            print("\n👉 Stopping here to avoid duplicates.")
        else:
            print("\n💾 Inserting destinations...")
            inserted = 0
            for dest in destinations:
                cur.execute(
                    """
                    INSERT INTO destinations (name, country, latitude, longitude, description, best_season, family_friendly)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        dest['name'],
                        dest['country'],
                        float(dest['latitude']),
                        float(dest['longitude']),
                        dest['description'],
                        dest['best_season'],
                        dest['family_friendly'].lower() == 'true'
                    )
                )
                inserted += 1
            
            conn.commit()
            print(f"✅ Inserted {inserted} destinations!")
            
            # Verify
            cur.execute("SELECT COUNT(*) FROM destinations")
            after_count = cur.fetchone()[0]
            print(f"\n📊 Total destinations now: {after_count}")
            
            # Show sample
            cur.execute("SELECT name, country FROM destinations LIMIT 5")
            print("\n🌍 Sample destinations:")
            for row in cur.fetchall():
                print(f"   • {row[0]}, {row[1]}")

print("\n✨ Done! Your app can now query real destination data.")

# COMMAND ----------

