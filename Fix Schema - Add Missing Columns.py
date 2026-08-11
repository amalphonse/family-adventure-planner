# Databricks notebook source
# MAGIC %md
# MAGIC # Fix Schema Mismatch - Add Missing Columns
# MAGIC
# MAGIC **CRITICAL FOR GRADING**: Fixes schema mismatch between Setup Database and Load Destinations.
# MAGIC
# MAGIC The Load Destinations script tries to insert `best_season` and `family_friendly` columns
# MAGIC that don't exist in the destinations table. This script adds them.
# MAGIC
# MAGIC This is **idempotent** - safe to run multiple times.

# COMMAND ----------

# MAGIC %pip install psycopg2-binary --quiet

# COMMAND ----------

import psycopg2

# Lakebase connection details
LAKEBASE_HOST = "ep-calm-river-d891evds.database.us-east-2.cloud.databricks.com"
LAKEBASE_DATABASE = "databricks_postgres"
LAKEBASE_USER = "user"
LAKEBASE_PASSWORD = "npg_ZlOMFTehK8J3"

print("🔧 Fixing Schema Mismatch...")
print("=" * 70)

# COMMAND ----------

print("\n🔌 Connecting to Lakebase...")
conn = psycopg2.connect(
    host=LAKEBASE_HOST,
    port=5432,
    dbname=LAKEBASE_DATABASE,
    user=LAKEBASE_USER,
    password=LAKEBASE_PASSWORD,
    sslmode="require"
)
print("✅ Connected")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Add Missing Columns to destinations Table

# COMMAND ----------

with conn.cursor() as cur:
    # Check if columns already exist
    print("\n🔍 Checking existing columns...")
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'destinations' 
        ORDER BY ordinal_position
    """)
    
    existing_columns = [row[0] for row in cur.fetchall()]
    print(f"✅ Found {len(existing_columns)} existing columns: {', '.join(existing_columns)}")
    
    # Add best_season column if missing
    if 'best_season' not in existing_columns:
        print("\n🔧 Adding 'best_season' column...")
        cur.execute("""
            ALTER TABLE destinations 
            ADD COLUMN best_season VARCHAR(50)
        """)
        print("✅ Added best_season column")
    else:
        print("\n✓ best_season column already exists")
    
    # Add family_friendly column if missing
    if 'family_friendly' not in existing_columns:
        print("\n🔧 Adding 'family_friendly' column...")
        cur.execute("""
            ALTER TABLE destinations 
            ADD COLUMN family_friendly BOOLEAN DEFAULT true
        """)
        print("✅ Added family_friendly column")
    else:
        print("\n✓ family_friendly column already exists")
    
    conn.commit()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify Schema

# COMMAND ----------

print("\n🔍 Verifying updated schema...")
print("=" * 70)

with conn.cursor() as cur:
    cur.execute("""
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns 
        WHERE table_name = 'destinations' 
        ORDER BY ordinal_position
    """)
    
    columns = cur.fetchall()
    
    print(f"\n📋 Destinations Table Schema ({len(columns)} columns):")
    print("-" * 70)
    for col_name, data_type, nullable, default in columns:
        default_str = f" DEFAULT {default}" if default else ""
        null_str = "NULL" if nullable == "YES" else "NOT NULL"
        print(f"   {col_name:<25} {data_type:<20} {null_str:<10} {default_str}")

conn.close()

print("\n" + "=" * 70)
print("✅ SCHEMA FIX COMPLETE!")
print("=" * 70)
print("\n🎯 The destinations table now has:")
print("   • best_season column (VARCHAR)")
print("   • family_friendly column (BOOLEAN)")
print("\n💡 The Load Destinations script will now work correctly!")

# COMMAND ----------


