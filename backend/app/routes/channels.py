from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.database import execute_query

router = APIRouter()

TABLE = "major_project.news_pipeline.gold_articles"


@router.get("/channels")
def get_channels():
    """Return per-channel statistics."""
    try:
        rows = execute_query(
            f"SELECT "
            f"  channel, "
            f"  COUNT(*) as article_count, "
            f"  ROUND(AVG(positive_score), 4) as avg_positive, "
            f"  ROUND(AVG(negative_score), 4) as avg_negative, "
            f"  ROUND(AVG(neutral_score), 4) as avg_neutral, "
            f"  SUM(CASE WHEN is_negative_alert = true THEN 1 ELSE 0 END) as negative_alert_count "
            f"FROM {TABLE} "
            f"GROUP BY channel "
            f"ORDER BY article_count DESC"
        )
        return {"channels": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/channels/compare")
def compare_channels(
    channels: str = Query(..., description="Comma-separated channel names, e.g. TheHindu,IndianExpress"),
    category: Optional[str] = Query(None, description="Filter by category"),
):
    """Compare 2+ channels, optionally filtered to a specific category."""
    try:
        channel_list = [c.strip() for c in channels.split(",") if c.strip()]
        if len(channel_list) < 2:
            raise HTTPException(status_code=400, detail="Provide at least 2 channels to compare")

        quoted = ", ".join(f"'{c}'" for c in channel_list)
        conditions = [f"channel IN ({quoted})"]
        if category:
            conditions.append(f"category = '{category}'")

        where_clause = " WHERE " + " AND ".join(conditions)

        rows = execute_query(
            f"SELECT heading, url, channel, category, article_date, "
            f"positive_score, negative_score, neutral_score, sentiment_label "
            f"FROM {TABLE}{where_clause} "
            f"ORDER BY channel, article_date DESC"
        )

        # Group by channel
        result = {}
        for row in rows:
            ch = row["channel"]
            if ch not in result:
                result[ch] = []
            result[ch].append(row)

        return {"comparison": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
