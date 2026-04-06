"""
=============================================================
  NEWS SENTIMENT ANALYSIS & CLASSIFICATION PIPELINE
=============================================================
  A standalone ML pipeline that:
    1. Scrapes news articles from Indian news websites
    2. Preprocesses the text (cleaning, lemmatization, etc.)
    3. Runs sentiment analysis (RoBERTa)
    4. Classifies articles into categories (DistilBERT / keyword fallback)
    5. Outputs final results as Excel + prints a summary

  Usage:
    python main.py                  # Run full pipeline (scrape + process)
    python main.py --skip-videos    # Scrape text only, skip video scraping
=============================================================
"""

import os
import sys
import argparse
import pandas as pd

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from data_collection.scrapers import scrape_all_text
from preprocessing.preprocess import preprocess_all
from sentiment_analysis.sentiment import SentimentAnalyzer
from classification.classify import NewsClassifier


# Paths
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
MAPPING_FILE = os.path.join(PROJECT_ROOT, "sentiment_analysis", "mapping.txt")
MODEL_FILE = os.path.join(DATA_DIR, "distilbert_model.h5")


def step1_collect_data(skip_videos=False):
    """Step 1: Scrape news articles from websites into data/*.xlsx"""
    print("\n" + "=" * 60)
    print("  STEP 1: DATA COLLECTION")
    print("=" * 60)

    os.makedirs(DATA_DIR, exist_ok=True)

    # Text scrapers
    print("\n--- Text Article Scraping ---")
    scrape_all_text(DATA_DIR)

    # Video scrapers (optional, slow due to Selenium + speech-to-text)
    if not skip_videos:
        print("\n--- Video Scraping (this is slow, uses Selenium) ---")
        try:
            from data_collection.video_scrapers import scrape_all_videos
            scrape_all_videos(DATA_DIR)
        except Exception as e:
            print(f"\n  WARNING: Video scraping failed: {e}")
            print("  Continuing with text articles only...")
    else:
        print("\n--- Skipping video scraping (--skip-videos) ---")


def step2_preprocess():
    """Step 2: Preprocess all scraped data from data/*.xlsx -> data/Final_Prepped_Data.xlsx"""
    print("\n" + "=" * 60)
    print("  STEP 2: PREPROCESSING")
    print("=" * 60)
    df = preprocess_all(DATA_DIR)
    return df


def step3_analyze(df):
    """Step 3: Run sentiment analysis and classification on preprocessed data."""
    print("\n" + "=" * 60)
    print("  STEP 3: SENTIMENT ANALYSIS & CLASSIFICATION")
    print("=" * 60)

    if df.empty:
        print("  ERROR: No data to analyze. Check previous steps.")
        return df

    # Initialize models
    sentiment_analyzer = SentimentAnalyzer(mapping_file=MAPPING_FILE)
    classifier = NewsClassifier(model_path=MODEL_FILE)

    # Run sentiment analysis
    print(f"\n--- Sentiment Analysis ({len(df)} articles) ---")
    df["Sentiment"] = sentiment_analyzer.analyze_series(df["Body"])

    # Run classification
    print(f"\n--- Classification ({len(df)} articles) ---")
    df["Category"] = classifier.classify_series(df["Body"])

    return df


def step4_output(df):
    """Step 4: Save results and print summary."""
    print("\n" + "=" * 60)
    print("  STEP 4: OUTPUT RESULTS")
    print("=" * 60)

    if df.empty:
        print("  No results to output.")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Extract sentiment scores into separate columns for readability
    df["Positive"] = df["Sentiment"].apply(lambda x: round(x[0] * 100, 1) if isinstance(x, list) else 0)
    df["Negative"] = df["Sentiment"].apply(lambda x: round(x[1] * 100, 1) if isinstance(x, list) else 0)
    df["Neutral"] = df["Sentiment"].apply(lambda x: round(x[2] * 100, 1) if isinstance(x, list) else 0)

    # Save full results
    output_path = os.path.join(OUTPUT_DIR, "Final_Results.xlsx")
    save_cols = ["Heading", "Body", "Category", "Positive", "Negative", "Neutral", "URL"]
    save_cols = [c for c in save_cols if c in df.columns]
    df[save_cols].to_excel(output_path, index=False)
    print(f"\n  Full results saved: {output_path}")

    # Save high-negativity alerts (negative >= 50%)
    alerts = df[df["Negative"] >= 50.0]
    if not alerts.empty:
        alert_path = os.path.join(OUTPUT_DIR, "Negative_Alerts.xlsx")
        alerts[save_cols].to_excel(alert_path, index=False)
        print(f"  Negative alerts saved: {alert_path} ({len(alerts)} articles)")

    # Print summary
    print("\n" + "-" * 60)
    print("  SUMMARY")
    print("-" * 60)
    print(f"  Total articles processed: {len(df)}")
    print(f"\n  Category distribution:")
    for cat, count in df["Category"].value_counts().items():
        print(f"    {cat:20s}: {count}")

    print(f"\n  Sentiment overview:")
    avg_pos = df["Positive"].mean()
    avg_neg = df["Negative"].mean()
    avg_neu = df["Neutral"].mean()
    print(f"    Avg Positive: {avg_pos:.1f}%")
    print(f"    Avg Negative: {avg_neg:.1f}%")
    print(f"    Avg Neutral:  {avg_neu:.1f}%")

    high_neg = len(df[df["Negative"] >= 50])
    print(f"\n  High-negativity articles (>=50%): {high_neg}")

    # Print top 5 most negative articles
    if high_neg > 0:
        print(f"\n  Top negative articles:")
        top_neg = df.nlargest(min(5, len(df)), "Negative")
        for _, row in top_neg.iterrows():
            heading = str(row.get("Heading", ""))[:60]
            print(f"    [{row['Negative']:.0f}% neg] [{row['Category']}] {heading}...")

    # Ministry mapping (from original project)
    ministry_map = {
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
    if high_neg > 0:
        print(f"\n  Ministry-wise negative alerts:")
        for _, row in alerts.iterrows():
            cat = row["Category"]
            ministry = ministry_map.get(cat, cat)
            heading = str(row.get("Heading", ""))[:50]
            print(f"    -> {ministry}: {heading}...")

    print("\n" + "=" * 60)
    print("  PIPELINE COMPLETE")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="News Sentiment Analysis & Classification Pipeline")
    parser.add_argument("--skip-videos", action="store_true",
                        help="Skip video scraping (text articles only)")
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("  NEWS SENTIMENT ANALYSIS & CLASSIFICATION PIPELINE")
    print("=" * 60)

    # Step 1: Scrape data -> data/*.xlsx (skipped — data already collected)
    # step1_collect_data(skip_videos=args.skip_videos)
    print("\n  Skipping data collection — using existing data/*.xlsx files")

    # Step 2: Preprocess scraped data -> data/Final_Prepped_Data.xlsx
    df = step2_preprocess()

    # Step 3: Sentiment + Classification
    df = step3_analyze(df)

    # Step 4: Output results -> output/Final_Results.xlsx
    step4_output(df)


if __name__ == "__main__":
    main()
