# Databricks notebook source
# MAGIC %md
# MAGIC # 02 - Volume → Bronze
# MAGIC Reads the raw CSV from Volume and **appends** to `bronze_articles` Delta table.
# MAGIC Only loads yesterday's file — skips if already ingested.
# MAGIC
# MAGIC **Input:** `/Volumes/major_project/news_pipeline/raw_files/arrived_YYYY-MM-DD.csv`
# MAGIC **Output:** `major_project.news_pipeline.bronze_articles` (append only)

# COMMAND ----------

# MAGIC %sql
# MAGIC USE CATALOG major_project;
# MAGIC USE SCHEMA news_pipeline;

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE TABLE IF NOT EXISTS bronze_articles (
# MAGIC   heading STRING,
# MAGIC   body STRING,
# MAGIC   category_from_url STRING,
# MAGIC   url STRING,
# MAGIC   channel STRING,
# MAGIC   article_date DATE,
# MAGIC   ingested_at TIMESTAMP
# MAGIC )
# MAGIC USING DELTA
# MAGIC COMMENT 'Bronze layer - raw scraped news articles. Appended daily.';

# COMMAND ----------

from datetime import datetime, timedelta
import os

yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
volume_path = "/Volumes/major_project/news_pipeline/raw_files"
file_path = f"{volume_path}/arrived_{yesterday}.csv"

print(f"Target date: {yesterday}")
print(f"File path:   {file_path}")
print(f"File exists: {os.path.exists(file_path)}")

# COMMAND ----------

# Check if this date was already ingested (prevent duplicates on re-run)
already_ingested = spark.sql(f"""
    SELECT COUNT(*) as cnt FROM bronze_articles WHERE article_date = '{yesterday}'
""").collect()[0]["cnt"]

if already_ingested > 0:
    print(f"Date {yesterday} already has {already_ingested} rows in bronze. Skipping to avoid duplicates.")
    dbutils.notebook.exit(f"Already ingested: {already_ingested} rows")

# COMMAND ----------

if not os.path.exists(file_path):
    print(f"File not found: {file_path}")
    print("Run notebook 01 first to scrape data.")
    dbutils.notebook.exit("No file found")

# Read CSV from Volume (with proper quoting for article body text)
df_raw = (
    spark.read.format("csv")
    .option("header", "true")
    .option("inferSchema", "false")
    .option("multiLine", "true")
    .option("escape", '"')
    .option("quote", '"')
    .load(file_path)
)

from pyspark.sql.functions import current_timestamp

df_bronze = (
    df_raw
    .withColumn("article_date", df_raw["article_date"].cast("date"))
    .withColumn("ingested_at", current_timestamp())
)

row_count = df_bronze.count()
print(f"Rows loaded from CSV: {row_count}")
df_bronze.show(5, truncate=60)

# COMMAND ----------

# APPEND to bronze (never overwrite — data accumulates daily)
df_bronze.write.mode("append").saveAsTable("major_project.news_pipeline.bronze_articles")

print(f"✓ Appended {row_count} rows to bronze_articles for {yesterday}")

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Daily article counts by channel
# MAGIC SELECT article_date, channel, COUNT(*) as articles
# MAGIC FROM major_project.news_pipeline.bronze_articles
# MAGIC GROUP BY article_date, channel
# MAGIC ORDER BY article_date DESC, articles DESC;
