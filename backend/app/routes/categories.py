from fastapi import APIRouter, HTTPException
from app.database import execute_query

router = APIRouter()

TABLE = "major_project.news_pipeline.gold_articles"


@router.get("/categories")
def get_categories():
    """Return available categories."""
    try:
        rows = execute_query(
            f"SELECT "
            f"  category, "
            f"  COUNT(*) as article_count "
            f"FROM {TABLE} "
            f"WHERE category IS NOT NULL AND category != '' "
            f"GROUP BY category "
            f"ORDER BY article_count DESC"
        )
        return {"categories": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))