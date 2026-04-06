import math
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.database import execute_query, execute_scalar

router = APIRouter()

TABLE = "major_project.news_pipeline.gold_articles"

ALLOWED_SORT = {
    "negative_score",
    "positive_score",
    "article_date",
}


@router.get("/articles")
def get_articles(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    channel: Optional[str] = None,
    category: Optional[str] = None,
    sentiment: Optional[str] = None,
    search: Optional[str] = None,
    date: Optional[str] = None,
    sort_by: Optional[str] = None,
):
    """Return a paginated list of articles with optional filters."""
    try:
        conditions = []
        if channel:
            conditions.append(f"channel = '{channel}'")
        if category:
            conditions.append(f"category = '{category}'")
        if sentiment:
            conditions.append(f"sentiment_label = '{sentiment}'")
        if date:
            conditions.append(f"article_date = '{date}'")
        if search:
            safe_search = search.replace("'", "''")
            conditions.append(f"LOWER(heading) LIKE LOWER('%{safe_search}%')")

        where_clause = ""
        if conditions:
            where_clause = " WHERE " + " AND ".join(conditions)

        # Determine sort order
        order_clause = "ORDER BY article_date DESC"
        if sort_by and sort_by in ALLOWED_SORT:
            order_clause = f"ORDER BY {sort_by} DESC"

        # Get total count
        total = execute_scalar(f"SELECT COUNT(*) FROM {TABLE}{where_clause}")

        # Calculate offset
        offset = (page - 1) * per_page
        total_pages = math.ceil(total / per_page) if total else 0

        # Get articles
        rows = execute_query(
            f"SELECT heading, body_cleaned, url, channel, article_date, category, "
            f"positive_score, negative_score, neutral_score, sentiment_label, "
            f"ministry, is_negative_alert, processed_at "
            f"FROM {TABLE}{where_clause} {order_clause} "
            f"LIMIT {per_page} OFFSET {offset}"
        )

        return {
            "articles": rows,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": total_pages,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
