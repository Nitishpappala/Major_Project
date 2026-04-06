from fastapi import APIRouter, HTTPException
from app.database import execute_query

router = APIRouter()

TABLE = "major_project.news_pipeline.gold_articles"


@router.get("/lineage")
def get_lineage():
    """Return data lineage and pipeline information with statistics."""
    try:
        # Get statistics for each stage
        total_result = execute_query(f"SELECT COUNT(*) as total FROM {TABLE}")
        total_articles = total_result[0]["total"] if total_result else 0

        # Get channels for data collection stage
        channels_result = execute_query(
            f"SELECT DISTINCT channel FROM {TABLE} ORDER BY channel"
        )
        channels = [row["channel"] for row in channels_result] if channels_result else []

        # Get processed articles count (articles in silver layer - cleaned)
        cleaned_result = execute_query(
            f"SELECT COUNT(*) as count FROM {TABLE} WHERE heading IS NOT NULL AND heading != ''"
        )
        cleaned_count = cleaned_result[0]["count"] if cleaned_result else 0

        # Get sentiment analyzed articles
        sentiment_result = execute_query(
            f"SELECT COUNT(*) as count FROM {TABLE} WHERE positive_score IS NOT NULL"
        )
        sentiment_count = sentiment_result[0]["count"] if sentiment_result else 0

        # Get categorized articles
        category_result = execute_query(
            f"SELECT COUNT(*) as count FROM {TABLE} WHERE category IS NOT NULL AND category != ''"
        )
        category_count = category_result[0]["count"] if category_result else 0

        # Get sentiment distribution for gold layer
        sentiment_breakdown = execute_query(
            f"SELECT "
            f"  sentiment_label, "
            f"  COUNT(*) as count "
            f"FROM {TABLE} "
            f"WHERE sentiment_label IS NOT NULL "
            f"GROUP BY sentiment_label"
        )
        sentiment_dist = {row.get("sentiment_label", "unknown"): row.get("count", 0) for row in sentiment_breakdown}

        lineage = {
            "lineage_stages": [
                {
                    "stage_number": 1,
                    "stage_name": "Data Collection",
                    "description": "Scraping news articles from 10+ Indian news channels",
                    "status": "completed",
                    "input": "Web Scraping from News Sites",
                    "output": "Raw Articles",
                    "data_count": total_articles,
                    "channels": channels,
                    "tools": ["BeautifulSoup", "Selenium", "Scrapers"],
                },
                {
                    "stage_number": 2,
                    "stage_name": "Bronze Layer (Raw)",
                    "description": "Raw data ingestion to Delta tables with minimal processing",
                    "status": "completed",
                    "input": "Raw Articles",
                    "output": "Delta Tables (Bronze)",
                    "data_count": total_articles,
                    "tools": ["Databricks", "Delta Lake"],
                },
                {
                    "stage_number": 3,
                    "stage_name": "Silver Layer (Cleaned)",
                    "description": "Data cleaning, deduplication, and standardization",
                    "status": "completed",
                    "input": "Delta Tables (Bronze)",
                    "output": "Cleaned & Standardized Data",
                    "data_count": cleaned_count,
                    "tools": ["Python", "spaCy", "NLTK", "Pandas"],
                },
                {
                    "stage_number": 4,
                    "stage_name": "Gold Layer (Enriched)",
                    "description": "Sentiment analysis and categorization using ML models",
                    "status": "completed",
                    "input": "Cleaned Data",
                    "output": "Enriched Articles with Sentiment & Category",
                    "data_count": sentiment_count,
                    "sentiment_count": sentiment_count,
                    "category_count": category_count,
                    "sentiment_distribution": sentiment_dist,
                    "tools": ["RoBERTa (Sentiment)", "DistilBERT (Classification)"],
                },
                {
                    "stage_number": 5,
                    "stage_name": "Presentation Layer",
                    "description": "Display and analyze data through interactive dashboards",
                    "status": "completed",
                    "input": "Enriched Articles",
                    "output": "Interactive Dashboards & Reports",
                    "data_count": sentiment_count,
                    "tools": ["FastAPI", "React", "Recharts"],
                },
            ],
            "summary": {
                "total_articles_collected": total_articles,
                "articles_cleaned": cleaned_count,
                "articles_with_sentiment": sentiment_count,
                "articles_with_category": category_count,
                "unique_channels": len(channels),
            },
        }

        return lineage
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
