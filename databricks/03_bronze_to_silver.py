# Databricks notebook source
# MAGIC %md
# MAGIC # 03 - Bronze → Silver (Cleaning)
# MAGIC Reads **only unprocessed** articles from bronze (yesterday's data that isn't already in silver),
# MAGIC applies text preprocessing, and **appends** to `silver_articles`.
# MAGIC
# MAGIC **Preprocessing:** lowercase, expand contractions, remove punctuation/numbers/stopwords
# MAGIC
# MAGIC **Input:** `major_project.news_pipeline.bronze_articles` (only new rows)
# MAGIC **Output:** `major_project.news_pipeline.silver_articles` (append only)

# COMMAND ----------

# MAGIC %pip install contractions
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %sql
# MAGIC USE CATALOG major_project;
# MAGIC USE SCHEMA news_pipeline;

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE TABLE IF NOT EXISTS silver_articles (
# MAGIC   heading STRING,
# MAGIC   body_original STRING,
# MAGIC   body_cleaned STRING,
# MAGIC   category_from_url STRING,
# MAGIC   url STRING,
# MAGIC   channel STRING,
# MAGIC   article_date DATE,
# MAGIC   cleaned_at TIMESTAMP
# MAGIC )
# MAGIC USING DELTA
# MAGIC COMMENT 'Silver layer - cleaned news articles. Appended daily, only new data processed.';

# COMMAND ----------

from datetime import datetime, timedelta

yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Only process data not already in Silver
# MAGIC This ensures re-running the pipeline doesn't reprocess old data.

# COMMAND ----------

# Check what dates are already in silver
already_in_silver = spark.sql(f"""
    SELECT COUNT(*) as cnt FROM silver_articles WHERE article_date = '{yesterday}'
""").collect()[0]["cnt"]

if already_in_silver > 0:
    print(f"Date {yesterday} already has {already_in_silver} rows in silver. Skipping.")
    dbutils.notebook.exit(f"Already processed: {already_in_silver} rows")

# Get only yesterday's data from bronze
df_bronze = spark.sql(f"""
    SELECT * FROM bronze_articles
    WHERE article_date = '{yesterday}'
""")

count = df_bronze.count()
print(f"New articles to clean (date={yesterday}): {count}")

if count == 0:
    print("No new articles to process.")
    dbutils.notebook.exit("No data")

# COMMAND ----------

import pandas as pd
pdf = df_bronze.toPandas()
print(f"Loaded {len(pdf)} rows into Pandas")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Preprocessing

# COMMAND ----------

import re
import contractions

STOPWORDS = set([
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your",
    "yours", "yourself", "yourselves", "he", "him", "his", "himself", "she", "her",
    "hers", "herself", "it", "its", "itself", "they", "them", "their", "theirs",
    "themselves", "what", "which", "who", "whom", "this", "that", "these", "those",
    "am", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "having", "do", "does", "did", "doing", "a", "an", "the", "and", "but", "if",
    "or", "because", "as", "until", "while", "of", "at", "by", "for", "with",
    "about", "against", "between", "through", "during", "before", "after", "above",
    "below", "to", "from", "up", "down", "in", "out", "on", "off", "over", "under",
    "again", "further", "then", "once", "here", "there", "when", "where", "why",
    "how", "all", "both", "each", "few", "more", "most", "other", "some", "such",
    "no", "nor", "only", "own", "same", "so", "than", "too", "very", "s", "t",
    "can", "will", "just", "don", "should", "now", "d", "ll", "m", "o", "re", "ve",
    "y", "ain", "aren", "couldn", "didn", "doesn", "hadn", "hasn", "haven", "isn",
    "ma", "mightn", "mustn", "needn", "shan", "shouldn", "wasn", "weren", "won",
    "wouldn", "any",
])
STOPWORDS.discard("not")  # keep "not" — critical for sentiment


def clean_text(text):
    """Full text preprocessing pipeline."""
    if not isinstance(text, str) or not text.strip():
        return ""
    text = text.lower()
    try:
        text = contractions.fix(text)
    except Exception:
        pass
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\d+', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    words = [w for w in text.split() if w not in STOPWORDS and len(w) > 1]
    return " ".join(words)

# COMMAND ----------

# Filter junk
print(f"Before cleaning: {len(pdf)} rows")

pdf = pdf[~pdf["heading"].astype(str).str.contains("horoscope", case=False, na=False)]
pdf["body"] = pdf["body"].apply(lambda x: str(x).split("Edited By:")[0])
pdf = pdf[~pdf["body"].astype(str).str.contains("dear subscriber", case=False, na=False)]
pdf = pdf[pdf["body"].apply(lambda x: isinstance(x, str) and len(str(x).strip()) > 50)]

print(f"After filtering:  {len(pdf)} rows")

# COMMAND ----------

# Apply cleaning
pdf["body_original"] = pdf["body"]
pdf["body_cleaned"] = pdf["body"].apply(clean_text)
pdf = pdf[pdf["body_cleaned"].str.len() > 10]

print(f"After cleaning:   {len(pdf)} rows")

for _, row in pdf.head(3).iterrows():
    print(f"\n  [{row['channel']}] {row['heading'][:60]}...")
    print(f"    Cleaned: {row['body_cleaned'][:80]}...")

# COMMAND ----------

# Append to silver
silver_pdf = pdf[["heading", "body_original", "body_cleaned", "category_from_url", "url", "channel", "article_date"]]
from pyspark.sql.functions import current_timestamp
df_silver = spark.createDataFrame(silver_pdf).withColumn("cleaned_at", current_timestamp())
df_silver.write.mode("append").saveAsTable("major_project.news_pipeline.silver_articles")

print(f"\n✓ Appended {len(silver_pdf)} cleaned articles to silver_articles")

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT article_date, channel, COUNT(*) as cnt
# MAGIC FROM major_project.news_pipeline.silver_articles
# MAGIC GROUP BY article_date, channel
# MAGIC ORDER BY article_date DESC, cnt DESC;
