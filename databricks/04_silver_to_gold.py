# Databricks notebook source
# MAGIC %md
# MAGIC # 04 - Silver → Gold (Sentiment & Classification)
# MAGIC Reads **only unprocessed** articles from silver, applies:
# MAGIC 1. **Sentiment Analysis** (TextBlob — lightweight, fits free tier)
# MAGIC 2. **Classification** (keyword-based — 10 categories, no model needed)
# MAGIC
# MAGIC **Appends** to `gold_articles` with **channel** and **article_date** columns.
# MAGIC
# MAGIC **Input:** `major_project.news_pipeline.silver_articles` (only new rows)
# MAGIC **Output:** `major_project.news_pipeline.gold_articles` (append only)

# COMMAND ----------

# MAGIC %pip install textblob
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %sql
# MAGIC USE CATALOG major_project;
# MAGIC USE SCHEMA news_pipeline;

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE TABLE IF NOT EXISTS gold_articles (
# MAGIC   heading STRING,
# MAGIC   body_cleaned STRING,
# MAGIC   url STRING,
# MAGIC   channel STRING,
# MAGIC   article_date DATE,
# MAGIC   category STRING,
# MAGIC   positive_score DOUBLE,
# MAGIC   negative_score DOUBLE,
# MAGIC   neutral_score DOUBLE,
# MAGIC   sentiment_label STRING,
# MAGIC   ministry STRING,
# MAGIC   is_negative_alert BOOLEAN,
# MAGIC   processed_at TIMESTAMP
# MAGIC )
# MAGIC USING DELTA
# MAGIC COMMENT 'Gold layer - final articles with sentiment, category, channel, date. Appended daily.';

# COMMAND ----------

from datetime import datetime, timedelta

yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Only process new data (skip already-processed dates)

# COMMAND ----------

already_in_gold = spark.sql(f"""
    SELECT COUNT(*) as cnt FROM gold_articles WHERE article_date = '{yesterday}'
""").collect()[0]["cnt"]

if already_in_gold > 0:
    print(f"Date {yesterday} already has {already_in_gold} rows in gold. Skipping.")
    dbutils.notebook.exit(f"Already processed: {already_in_gold} rows")

df_silver = spark.sql(f"""
    SELECT * FROM silver_articles WHERE article_date = '{yesterday}'
""")

count = df_silver.count()
print(f"Silver articles to analyze (date={yesterday}): {count}")

if count == 0:
    print("No new articles to process.")
    dbutils.notebook.exit("No data")

pdf = df_silver.toPandas()

# COMMAND ----------

# MAGIC %md
# MAGIC ### Sentiment Analysis (TextBlob)

# COMMAND ----------

from textblob import TextBlob


def analyze_sentiment(text):
    """Returns (positive, negative, neutral, label) — scores sum to 1.0"""
    if not isinstance(text, str) or not text.strip():
        return 0.0, 0.0, 1.0, "neutral"

    polarity = TextBlob(text).sentiment.polarity  # -1.0 to +1.0

    if polarity > 0.1:
        positive = 0.4 + (polarity * 0.5)
        negative = 0.05
        neutral = 1.0 - positive - negative
        label = "positive"
    elif polarity < -0.1:
        negative = 0.4 + (abs(polarity) * 0.5)
        positive = 0.05
        neutral = 1.0 - positive - negative
        label = "negative"
    else:
        neutral = 0.6 + (1.0 - abs(polarity) * 10) * 0.3
        positive = (1.0 - neutral) / 2
        negative = (1.0 - neutral) / 2
        label = "neutral"

    positive = max(0.0, min(1.0, positive))
    negative = max(0.0, min(1.0, negative))
    neutral = max(0.0, min(1.0, neutral))
    total = positive + negative + neutral
    if total > 0:
        positive /= total
        negative /= total
        neutral /= total

    return round(positive, 4), round(negative, 4), round(neutral, 4), label

# COMMAND ----------

# MAGIC %md
# MAGIC ### Classification (Keyword-Based, 10 Categories)

# COMMAND ----------

KEYWORD_MAP = {
    "Sports": ["cricket", "football", "match", "player", "team", "sport", "olympic",
               "tournament", "goal", "wicket", "ipl", "fifa", "tennis", "hockey",
               "batsman", "bowler", "innings", "stadium", "league", "medal", "coach"],
    "Politics": ["minister", "parliament", "election", "political", "government", "bjp",
                 "congress", "vote", "campaign", "modi", "opposition", "bill", "policy",
                 "president", "prime minister", "lok sabha", "rajya sabha", "mla", "rally"],
    "Business": ["market", "stock", "economy", "company", "profit", "revenue", "trade",
                 "investment", "gdp", "inflation", "rbi", "bank", "startup", "ipo",
                 "sensex", "nifty", "rupee", "share", "fiscal", "budget", "tax"],
    "Technology": ["technology", "software", "app", "digital", "ai", "artificial",
                   "computer", "internet", "cyber", "tech", "google", "apple", "robot",
                   "smartphone", "data", "chip", "5g", "cloud", "elon musk", "tesla"],
    "Entertainment": ["movie", "film", "bollywood", "actor", "actress", "celebrity",
                      "music", "song", "album", "award", "netflix", "series", "show",
                      "director", "box office", "trailer", "ott", "dance", "hollywood"],
    "Crime": ["murder", "arrested", "police", "crime", "theft", "robbery", "fraud",
              "accused", "suspect", "criminal", "jail", "prison", "investigation",
              "kidnap", "assault", "drug", "scam", "fir", "rape", "encounter"],
    "Judiciary": ["court", "judge", "verdict", "supreme", "high court", "petition",
                  "hearing", "bail", "lawyer", "legal", "judicial", "bench",
                  "constitution", "appeal", "acquit", "convict", "pil"],
    "International": ["us ", "china", "pakistan", "russia", "ukraine", "united nations",
                      "global", "world", "foreign", "international", "nato", "eu ",
                      "biden", "trump", "iran", "israel", "gaza", "britain", "canada"],
    "Science": ["science", "research", "nasa", "isro", "space", "discovery",
                "scientist", "study", "experiment", "climate", "environment",
                "vaccine", "health", "disease", "medical", "virus", "earthquake"],
    "Culture": ["culture", "festival", "tradition", "heritage", "temple", "religion",
                "art", "museum", "dance", "diwali", "eid", "christmas", "holi",
                "spiritual", "pilgrim", "ancient", "yoga"],
}

MINISTRY_MAP = {
    "Sports": "Ministry of Youth Affairs and Sports",
    "Culture": "Ministry of Culture",
    "International": "Ministry of External Affairs",
    "Politics": "Ministry of Home Affairs",
    "Science": "Ministry of Science and Technology",
    "Technology": "Ministry of Electronics and IT",
    "Business": "Ministry of Finance",
    "Entertainment": "Ministry of Information and Broadcasting",
    "Judiciary": "Ministry of Law and Justice",
    "Crime": "Department of Internal Security",
}


def classify_article(text):
    if not isinstance(text, str):
        return "Politics"
    text_lower = text.lower()
    scores = {cat: sum(1 for kw in kws if kw in text_lower) for cat, kws in KEYWORD_MAP.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "Politics"

# COMMAND ----------

# MAGIC %md
# MAGIC ### Apply to all articles

# COMMAND ----------

print(f"Processing {len(pdf)} articles...\n")

results = []
for i, row in pdf.iterrows():
    text = row["body_cleaned"]
    pos, neg, neu, label = analyze_sentiment(text)
    cat = classify_article(text)

    results.append({
        "positive_score": pos,
        "negative_score": neg,
        "neutral_score": neu,
        "sentiment_label": label,
        "category": cat,
        "ministry": MINISTRY_MAP.get(cat, cat),
        "is_negative_alert": neg >= 0.5,
    })

    if (i + 1) % 10 == 0 or i == 0:
        print(f"  [{i+1}/{len(pdf)}] [{cat:15s}] [{label:8s}] {row['heading'][:50]}...")

import pandas as pd
results_df = pd.DataFrame(results)
pdf = pdf.reset_index(drop=True)
pdf = pd.concat([pdf, results_df], axis=1)

print(f"\n✓ All {len(pdf)} articles analyzed")

# COMMAND ----------

# Append to gold
gold_pdf = pdf[[
    "heading", "body_cleaned", "url", "channel", "article_date",
    "category", "positive_score", "negative_score", "neutral_score",
    "sentiment_label", "ministry", "is_negative_alert"
]]

from pyspark.sql.functions import current_timestamp
df_gold = spark.createDataFrame(gold_pdf).withColumn("processed_at", current_timestamp())
df_gold.write.mode("append").saveAsTable("major_project.news_pipeline.gold_articles")

print(f"✓ Appended {len(gold_pdf)} articles to gold_articles")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Results

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Full results: channel, date, category, sentiment
# MAGIC SELECT heading, channel, article_date, category, sentiment_label,
# MAGIC        ROUND(positive_score * 100, 1) as pos_pct,
# MAGIC        ROUND(negative_score * 100, 1) as neg_pct,
# MAGIC        ROUND(neutral_score * 100, 1) as neu_pct,
# MAGIC        ministry
# MAGIC FROM major_project.news_pipeline.gold_articles
# MAGIC WHERE article_date = current_date() - INTERVAL 1 DAY
# MAGIC ORDER BY negative_score DESC;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Per-channel sentiment summary
# MAGIC SELECT channel, COUNT(*) as articles,
# MAGIC        ROUND(AVG(positive_score) * 100, 1) as avg_pos,
# MAGIC        ROUND(AVG(negative_score) * 100, 1) as avg_neg,
# MAGIC        ROUND(AVG(neutral_score) * 100, 1) as avg_neu,
# MAGIC        SUM(CASE WHEN is_negative_alert THEN 1 ELSE 0 END) as neg_alerts
# MAGIC FROM major_project.news_pipeline.gold_articles
# MAGIC WHERE article_date = current_date() - INTERVAL 1 DAY
# MAGIC GROUP BY channel
# MAGIC ORDER BY articles DESC;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Category distribution across all channels
# MAGIC SELECT category, COUNT(*) as cnt,
# MAGIC        COLLECT_SET(channel) as channels
# MAGIC FROM major_project.news_pipeline.gold_articles
# MAGIC WHERE article_date = current_date() - INTERVAL 1 DAY
# MAGIC GROUP BY category
# MAGIC ORDER BY cnt DESC;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Negative alerts → ministry notifications
# MAGIC SELECT heading, channel, article_date, ministry,
# MAGIC        ROUND(negative_score * 100, 1) as neg_pct, url
# MAGIC FROM major_project.news_pipeline.gold_articles
# MAGIC WHERE is_negative_alert = true
# MAGIC   AND article_date = current_date() - INTERVAL 1 DAY
# MAGIC ORDER BY negative_score DESC;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Historical daily totals (grows over time as pipeline runs daily)
# MAGIC SELECT article_date, COUNT(*) as total_articles,
# MAGIC        SUM(CASE WHEN is_negative_alert THEN 1 ELSE 0 END) as negative_alerts
# MAGIC FROM major_project.news_pipeline.gold_articles
# MAGIC GROUP BY article_date
# MAGIC ORDER BY article_date DESC;
