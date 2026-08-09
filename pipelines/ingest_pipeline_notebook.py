# Databricks notebook source
# DBTITLE 1,Family Adventure Planner - Data Ingestion Pipeline
# MAGIC %md
# MAGIC # Family Adventure Planner - Data Ingestion Pipeline
# MAGIC
# MAGIC This notebook ingests data from third-party APIs, processes unstructured text, generates embeddings, and loads into Lakebase Postgres.
# MAGIC
# MAGIC ## Requirements Satisfied:
# MAGIC * ✅ **Spark Data Pipeline** - Runnable on Databricks compute
# MAGIC * ✅ **Third-Party API Integration** - Open-Meteo + Wikimedia APIs
# MAGIC * ✅ **Unstructured Data Processing** - Wikipedia articles → TF-IDF embeddings
# MAGIC
# MAGIC ## Data Flow:
# MAGIC 1. Call Open-Meteo Geocoding API → get coordinates
# MAGIC 2. Call Wikimedia API → fetch article extracts
# MAGIC 3. Generate 768-dim embeddings from unstructured text
# MAGIC 4. Insert into Lakebase Postgres with pgvector
# MAGIC
# MAGIC **Run all cells to populate the database with real data from APIs.**

# COMMAND ----------

