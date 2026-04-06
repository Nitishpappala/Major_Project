from fastapi import APIRouter, HTTPException
from app.database import execute_query

router = APIRouter()

TABLE = "major_project.news_pipeline.gold_articles"


@router.get("/project-info")
def get_project_info():
    """Return project pipeline information and statistics."""
    try:
        # Get total articles count
        total_result = execute_query(f"SELECT COUNT(*) as total FROM {TABLE}")
        total_articles = total_result[0]["total"] if total_result else 0

        # Get date range
        date_result = execute_query(
            f"SELECT MIN(article_date) as start_date, MAX(article_date) as end_date FROM {TABLE}"
        )
        start_date = date_result[0]["start_date"] if date_result else None
        end_date = date_result[0]["end_date"] if date_result else None

        # Get channels count
        channels_result = execute_query(
            f"SELECT COUNT(DISTINCT channel) as channel_count FROM {TABLE}"
        )
        channels_count = channels_result[0]["channel_count"] if channels_result else 0

        # Get categories count
        categories_result = execute_query(
            f"SELECT COUNT(DISTINCT category) as category_count FROM {TABLE} WHERE category IS NOT NULL AND category != ''"
        )
        categories_count = categories_result[0]["category_count"] if categories_result else 0

        # Get sentiment breakdown
        sentiment_result = execute_query(
            f"SELECT "
            f"  SUM(CASE WHEN sentiment_label = 'positive' THEN 1 ELSE 0 END) as positive_count, "
            f"  SUM(CASE WHEN sentiment_label = 'negative' THEN 1 ELSE 0 END) as negative_count, "
            f"  SUM(CASE WHEN sentiment_label = 'neutral' THEN 1 ELSE 0 END) as neutral_count "
            f"FROM {TABLE}"
        )
        sentiment = sentiment_result[0] if sentiment_result else {}

        return {
            "total_articles": total_articles,
            "channels_count": channels_count,
            "categories_count": categories_count,
            "date_range": {
                "start": str(start_date) if start_date else "N/A",
                "end": str(end_date) if end_date else "N/A",
            },
            "sentiment_distribution": {
                "positive": sentiment.get("positive_count", 0),
                "negative": sentiment.get("negative_count", 0),
                "neutral": sentiment.get("neutral_count", 0),
            },
            "pipeline_stages": [
                {
                    "name": "Data Collection",
                    "description": "Scraping news from multiple sources",
                    "status": "completed",
                },
                {
                    "name": "Bronze Layer",
                    "description": "Raw data ingestion to Delta tables",
                    "status": "completed",
                },
                {
                    "name": "Silver Layer",
                    "description": "Data cleaning and standardization",
                    "status": "completed",
                },
                {
                    "name": "Gold Layer",
                    "description": "Sentiment analysis and enrichment",
                    "status": "completed",
                },
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
