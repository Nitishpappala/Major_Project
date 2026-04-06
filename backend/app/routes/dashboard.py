from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.database import execute_query, execute_scalar

router = APIRouter()

TABLE = "major_project.news_pipeline.gold_articles"


@router.get("/dashboard/dates")
def get_dashboard_dates():
    """Return all distinct article dates available for dashboard filtering."""
    try:
        rows = execute_query(
            f"SELECT DISTINCT article_date FROM {TABLE} ORDER BY article_date DESC"
        )
        return [row["article_date"] for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard")
def get_dashboard(date: Optional[str] = Query(None, description="Filter by date (YYYY-MM-DD)")):
    """Return dashboard summary: totals, sentiment/category/channel distributions, top negative alerts."""
    try:
        date_filter = ""
        if date:
            date_filter = f" WHERE article_date = '{date}'"

        # Total articles
        total = execute_scalar(f"SELECT COUNT(*) FROM {TABLE}{date_filter}")

        # Sentiment distribution
        sentiment_rows = execute_query(
            f"SELECT sentiment_label, COUNT(*) as count FROM {TABLE}{date_filter} GROUP BY sentiment_label"
        )
        sentiment_distribution = {row["sentiment_label"]: row["count"] for row in sentiment_rows}

        # Category distribution
        category_rows = execute_query(
            f"SELECT category, COUNT(*) as count FROM {TABLE}{date_filter} GROUP BY category ORDER BY count DESC"
        )
        category_distribution = {row["category"]: row["count"] for row in category_rows}

        # Channel distribution
        channel_rows = execute_query(
            f"SELECT channel, COUNT(*) as count FROM {TABLE}{date_filter} GROUP BY channel ORDER BY count DESC"
        )
        channel_distribution = {row["channel"]: row["count"] for row in channel_rows}

        # Top 5 negative alerts
        top_negative = execute_query(
            f"SELECT heading, channel, negative_score, url, article_date, ministry "
            f"FROM {TABLE}{date_filter} "
            f"{'WHERE' if not date_filter else 'AND'} is_negative_alert = true "
            f"ORDER BY negative_score DESC LIMIT 5".replace(
                "AND" if not date_filter else "___SKIP___", ""
            )
        )
        # Fix the query construction for top negative alerts
        if date:
            neg_query = (
                f"SELECT heading, channel, negative_score, url, article_date, ministry "
                f"FROM {TABLE} WHERE article_date = '{date}' AND is_negative_alert = true "
                f"ORDER BY negative_score DESC LIMIT 5"
            )
        else:
            neg_query = (
                f"SELECT heading, channel, negative_score, url, article_date, ministry "
                f"FROM {TABLE} WHERE is_negative_alert = true "
                f"ORDER BY negative_score DESC LIMIT 5"
            )
        top_negative = execute_query(neg_query)

        # Sentiment trends over time
        sentiment_trends = execute_query(
            f"SELECT article_date, AVG(positive_score) as positive, AVG(negative_score) as negative, AVG(neutral_score) as neutral FROM {TABLE}{date_filter} GROUP BY article_date ORDER BY article_date"
        )
        sentiment_trends_formatted = [{"date": row["article_date"], "positive": round(row["positive"], 3), "negative": round(row["negative"], 3), "neutral": round(row["neutral"], 3)} for row in sentiment_trends]

        # Category sentiment breakdown
        category_sentiment = execute_query(
            f"SELECT category, sentiment_label, COUNT(*) as count FROM {TABLE}{date_filter} GROUP BY category, sentiment_label ORDER BY category"
        )
        category_sentiment_formatted = {}
        for row in category_sentiment:
            cat = row["category"]
            sent = row["sentiment_label"]
            if cat not in category_sentiment_formatted:
                category_sentiment_formatted[cat] = {"positive": 0, "negative": 0, "neutral": 0}
            category_sentiment_formatted[cat][sent] = row["count"]
        category_sentiment_list = [{"category": cat, **vals} for cat, vals in category_sentiment_formatted.items()]

        # Channel sentiment breakdown
        channel_sentiment = execute_query(
            f"SELECT channel, sentiment_label, COUNT(*) as count FROM {TABLE}{date_filter} GROUP BY channel, sentiment_label ORDER BY channel"
        )
        channel_sentiment_formatted = {}
        for row in channel_sentiment:
            ch = row["channel"]
            sent = row["sentiment_label"]
            if ch not in channel_sentiment_formatted:
                channel_sentiment_formatted[ch] = {"positive": 0, "negative": 0, "neutral": 0}
            channel_sentiment_formatted[ch][sent] = row["count"]
        channel_sentiment_list = [{"channel": ch, **vals} for ch, vals in channel_sentiment_formatted.items()]

        # Ministry sentiment breakdown
        ministry_sentiment = execute_query(
            f"SELECT ministry, sentiment_label, COUNT(*) as count FROM {TABLE}{date_filter} GROUP BY ministry, sentiment_label ORDER BY ministry"
        )
        ministry_sentiment_formatted = {}
        for row in ministry_sentiment:
            min = row["ministry"]
            sent = row["sentiment_label"]
            if min not in ministry_sentiment_formatted:
                ministry_sentiment_formatted[min] = {"positive": 0, "negative": 0, "neutral": 0}
            ministry_sentiment_formatted[min][sent] = row["count"]
        ministry_sentiment_list = [{"ministry": min, **vals} for min, vals in ministry_sentiment_formatted.items()]

        # Daily article volume
        daily_volume = execute_query(
            f"SELECT article_date, COUNT(*) as count FROM {TABLE}{date_filter} GROUP BY article_date ORDER BY article_date"
        )
        daily_volume_formatted = [{"date": row["article_date"], "count": row["count"]} for row in daily_volume]

        # Daily sentiment counts
        daily_sentiment_counts = execute_query(
            f"SELECT article_date, sentiment_label, COUNT(*) as count FROM {TABLE}{date_filter} GROUP BY article_date, sentiment_label ORDER BY article_date"
        )
        daily_sentiment_formatted = {}
        for row in daily_sentiment_counts:
            date = row["article_date"]
            sent = row["sentiment_label"]
            if date not in daily_sentiment_formatted:
                daily_sentiment_formatted[date] = {"positive": 0, "negative": 0, "neutral": 0}
            daily_sentiment_formatted[date][sent] = row["count"]
        daily_sentiment_list = [{"date": date, **vals} for date, vals in daily_sentiment_formatted.items()]

        # Sentiment polarity trend
        sentiment_polarity = execute_query(
            f"SELECT article_date, AVG(positive_score - negative_score) as polarity FROM {TABLE}{date_filter} GROUP BY article_date ORDER BY article_date"
        )
        sentiment_polarity_formatted = [{"date": row["article_date"], "polarity": round(row["polarity"], 3)} for row in sentiment_polarity]

        # Calculate percentages
        positive_count = sentiment_distribution.get("positive", 0)
        negative_count = sentiment_distribution.get("negative", 0)
        neutral_count = sentiment_distribution.get("neutral", 0)
        positive_percent = (positive_count / total * 100) if total else 0
        negative_percent = (negative_count / total * 100) if total else 0
        neutral_percent = (neutral_count / total * 100) if total else 0

        # Format sentiment distribution
        sentiment_dist_formatted = [
            {"name": "Positive", "value": positive_count, "color": "#10b981"},
            {"name": "Negative", "value": negative_count, "color": "#ef4444"},
            {"name": "Neutral", "value": sentiment_distribution.get("neutral", 0), "color": "#f59e0b"},
        ]

        # Format categories
        categories_formatted = [{"name": cat, "count": count} for cat, count in category_distribution.items()]

        # Format channels (placeholder for avgSentiment)
        channels_formatted = [{"channel": ch, "articles": count, "avgSentiment": 0.5} for ch, count in channel_distribution.items()]

        # Format alerts
        alerts_formatted = [{"heading": alert["heading"], "channel": alert["channel"], "negScore": alert["negative_score"], "url": alert["url"]} for alert in top_negative]

        return {
            "stats": {
                "totalArticles": total,
                "positivePercent": round(positive_percent, 1),
                "negativePercent": round(negative_percent, 1),
                "neutralPercent": round(neutral_percent, 1),
            },
            "sentimentDistribution": sentiment_dist_formatted,
            "categories": categories_formatted,
            "channels": channels_formatted,
            "sentimentTrends": sentiment_trends_formatted,
            "categorySentiment": category_sentiment_list,
            "channelSentiment": channel_sentiment_list,
            "ministrySentiment": ministry_sentiment_list,
            "dailyVolume": daily_volume_formatted,
            "dailySentimentCounts": daily_sentiment_list,
            "sentimentPolarity": sentiment_polarity_formatted,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
