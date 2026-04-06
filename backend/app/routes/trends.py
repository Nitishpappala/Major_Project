from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.database import execute_query

router = APIRouter()

TABLE = "major_project.news_pipeline.gold_articles"


@router.get("/trends")
def get_trends(
    channel: Optional[str] = None,
    category: Optional[str] = None,
):
    """Return sentiment trends grouped by date."""
    try:
        conditions = []
        if channel:
            conditions.append(f"channel = '{channel}'")
        if category:
            conditions.append(f"category = '{category}'")

        where_clause = ""
        if conditions:
            where_clause = " WHERE " + " AND ".join(conditions)

        rows = execute_query(
            f"SELECT "
            f"  article_date, "
            f"  ROUND(AVG(positive_score), 4) as avg_positive, "
            f"  ROUND(AVG(negative_score), 4) as avg_negative, "
            f"  ROUND(AVG(neutral_score), 4) as avg_neutral, "
            f"  COUNT(*) as article_count "
            f"FROM {TABLE}{where_clause} "
            f"GROUP BY article_date "
            f"ORDER BY article_date ASC"
        )

        return {"trends": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
