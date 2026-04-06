# Databricks notebook source
# MAGIC %md
# MAGIC # 01 - Data Extraction → Volume
# MAGIC Scrapes **yesterday's** news articles from all major Indian news channels.
# MAGIC Saves raw CSV to Unity Catalog Volume. Appends a new file each day.
# MAGIC
# MAGIC **10 Major News Sources:**
# MAGIC Times of India, Hindustan Times, The Hindu, Indian Express,
# MAGIC IndiaToday, ThePrint, Economic Times, LiveMint, Scroll.in, AajTak (Hindi→English)
# MAGIC
# MAGIC **Output:** `/Volumes/major_project/news_pipeline/raw_files/arrived_YYYY-MM-DD.csv`

# COMMAND ----------

# MAGIC %pip install requests beautifulsoup4 deep-translator
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE CATALOG IF NOT EXISTS major_project;
# MAGIC CREATE SCHEMA IF NOT EXISTS major_project.news_pipeline;
# MAGIC CREATE VOLUME IF NOT EXISTS major_project.news_pipeline.raw_files;

# COMMAND ----------

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import csv
import os
import re
import json

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

YESTERDAY = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
MAX_PAGES = 200  # max pages to crawl per source

# COMMAND ----------

# MAGIC %md
# MAGIC ### Helper: Date extraction from article pages

# COMMAND ----------

def get_article_date(soup, url):
    """Extract publish date from meta tags, time tag, JSON-LD, or URL pattern."""
    for attr in ["article:published_time", "og:article:published_time"]:
        meta = soup.find("meta", {"property": attr})
        if meta and meta.get("content"):
            return meta["content"][:10]

    for name in ["publish-date", "date", "pubdate", "publishdate", "original-source"]:
        meta = soup.find("meta", {"name": name})
        if meta and meta.get("content"):
            return meta["content"][:10]

    time_tag = soup.find("time", {"datetime": True})
    if time_tag:
        return time_tag["datetime"][:10]

    for script in soup.find_all("script", {"type": "application/ld+json"}):
        try:
            data = json.loads(script.string)
            if isinstance(data, list):
                data = data[0]
            if "datePublished" in data:
                return data["datePublished"][:10]
        except Exception:
            pass

    m = re.search(r"/(\d{4})/(\d{2})/(\d{2})/", url)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return None

# COMMAND ----------

# MAGIC %md
# MAGIC ### Generic Crawler

# COMMAND ----------

def crawl_source(base_url, domain, extract_fn, source_name, target_date=YESTERDAY):
    """Crawl a news site, keep ONLY articles published on target_date."""
    articles = []
    try:
        r = requests.get(base_url, headers=HEADERS, timeout=15)
    except Exception as e:
        print(f"  [{source_name}] Cannot reach {base_url}: {e}")
        return articles

    if r.status_code != 200:
        print(f"  [{source_name}] HTTP {r.status_code} for {base_url}")
        return articles

    soup = BeautifulSoup(r.text, "html.parser")
    urls_to_visit = []
    unique_urls = set()
    skip = {"video", "tag", "author", "tags", "livetv", "videos", "web-stories",
            "astrology", "visualstories", "photos", "photo-gallery", "live-tv", "podcast"}

    for a in soup.findAll("a", href=True):
        href = a["href"]
        if any(s in href.split("/") for s in skip):
            continue
        if href.startswith("/"):
            full = f"https://{domain}{href}"
        elif href.startswith("http") and domain in href:
            full = href
        else:
            continue
        if full not in unique_urls:
            unique_urls.add(full)
            urls_to_visit.append(full)

    pages = 0
    while urls_to_visit and pages < MAX_PAGES:
        url = urls_to_visit.pop(0)
        if not url.startswith("http"):
            continue
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            if r.status_code != 200:
                continue
            pages += 1
            soup = BeautifulSoup(r.text, "html.parser")

            for a in soup.findAll("a", href=True):
                href = a["href"]
                if any(s in href.split("/") for s in skip):
                    continue
                if href.startswith("/"):
                    full = f"https://{domain}{href}"
                elif href.startswith("http") and domain in href:
                    full = href
                else:
                    continue
                if full not in unique_urls:
                    unique_urls.add(full)
                    urls_to_visit.append(full)

            article_date = get_article_date(soup, url)
            if article_date != target_date:
                continue

            result = extract_fn(soup, url)
            if result:
                heading, body, category = result
                if len(body.strip()) > 50:
                    articles.append({
                        "heading": heading.strip(),
                        "body": body.strip(),
                        "category_from_url": category,
                        "url": url,
                        "channel": source_name,
                        "article_date": target_date,
                    })
                    print(f"  [{source_name}] [{len(articles)}] {heading[:65]}...")
        except Exception:
            continue

    print(f"  [{source_name}] Pages: {pages}, Yesterday's articles: {len(articles)}")
    return articles

# COMMAND ----------

# MAGIC %md
# MAGIC ### Extractor Functions — Major Indian News Channels
# MAGIC
# MAGIC **Working channels (10):** TimesOfIndia, HindustanTimes, TheHindu, IndianExpress,
# MAGIC IndiaToday, ThePrint, EconomicTimes, LiveMint, Scroll, AajTak
# MAGIC
# MAGIC Removed: NDTV (403), News18 (403), TheWire (blocked), IndiaTv (broken), DeccanHerald (broken)

# COMMAND ----------

def _get_cat(url, idx=3):
    parts = url.split("/")
    return parts[idx] if len(parts) > idx else ""


# --- 1. Times of India ---
# Body is in div[data-articlebody], date in JSON-LD datePublished
def extract_toi(soup, url):
    h = soup.find("h1")
    if not h:
        return None
    # TOI uses data-articlebody attribute for article text
    story = soup.find("div", attrs={"data-articlebody": True})
    if not story:
        return None
    body = story.get_text(separator=" ", strip=True)
    if len(body) < 50:
        return None
    return h.text.strip(), body, _get_cat(url)


# --- 2. Hindustan Times ---
# Body is in div.detail, date in article:published_time meta tag
def extract_ht(soup, url):
    h = soup.find("h1")
    if not h:
        return None
    # HT uses div with class "detail" for article body
    story = soup.find("div", {"class": lambda x: x and "detail" in x})
    if not story:
        return None
    paras = story.find_all("p")
    if not paras:
        return None
    body = " ".join(p.text for p in paras)
    if len(body) < 50:
        return None
    return h.text.strip(), body, _get_cat(url)


# --- 3. The Hindu ---
def extract_thehindu(soup, url):
    h = soup.find("h1")
    if not h:
        return None
    story = (soup.find("div", {"class": lambda x: x and "articlebodycontent" in str(x).lower()})
             or soup.find("article"))
    if not story:
        return None
    paras = story.find_all("p")
    if not paras:
        return None
    body = " ".join(p.text for p in paras)
    return h.text.strip(), body, _get_cat(url)


# --- 4. Indian Express ---
def extract_indianexpress(soup, url):
    h = soup.find("h1")
    if not h:
        return None
    story = (soup.find("div", {"class": lambda x: x and "full-details" in str(x)})
             or soup.find("div", {"id": "pcl-full-content"}))
    if not story:
        return None
    paras = story.find_all("p")
    if not paras:
        return None
    body = " ".join(p.text for p in paras)
    return h.text.strip(), body, _get_cat(url)


# --- 5. IndiaToday ---
def extract_indiatoday(soup, url):
    bd = soup.find("div", {"class": lambda x: x and "story__content__body" in str(x)})
    if not bd:
        return None
    h = bd.find("h1") or soup.find("h1")
    if not h:
        return None
    dd = soup.find("div", {"class": lambda x: x and "Story_description" in str(x)})
    if not dd:
        return None
    paras = dd.find_all("p")
    if not paras:
        return None
    body = " ".join(p.text for p in paras)
    parts = url.split("/")
    cat = "india" if len(parts) > 3 and parts[3] == "cities" else _get_cat(url)
    return h.text.strip(), body, cat


# --- 6. ThePrint ---
def extract_theprint(soup, url):
    h = soup.find("h1")
    if not h:
        return None
    if not (soup.find("html", {"lang": "en"}) or soup.find("html", {"lang": "en-US"})):
        return None
    post = soup.find("div", {"id": "postexcerpt"})
    if not post:
        return None
    paras = post.find_all("p")
    if not paras:
        return None
    body = " ".join(p.text for p in paras[: max(1, len(paras) - 4)])
    return h.text.strip(), body, _get_cat(url)


# --- 7. Economic Times ---
def extract_et(soup, url):
    h = soup.find("h1")
    if not h:
        return None
    # ET uses data-articlebody like TOI, or artText class, or article tag
    story = (soup.find("div", attrs={"data-articlebody": True})
             or soup.find("div", {"class": lambda x: x and "artText" in str(x)})
             or soup.find("article"))
    if not story:
        return None
    paras = story.find_all("p")
    body = " ".join(p.text for p in paras) if paras else story.get_text(separator=" ", strip=True)
    if len(body) < 50:
        return None
    return h.text.strip(), body, _get_cat(url)


# --- 8. LiveMint ---
def extract_livemint(soup, url):
    h = soup.find("h1")
    if not h:
        return None
    story = (soup.find("div", {"class": lambda x: x and "contentSec" in str(x)})
             or soup.find("div", {"id": "article-body"})
             or soup.find("article"))
    if not story:
        return None
    paras = story.find_all("p")
    if not paras:
        return None
    body = " ".join(p.text for p in paras)
    return h.text.strip(), body, _get_cat(url)


# --- 9. Scroll.in ---
def extract_scroll(soup, url):
    h = soup.find("h1")
    if not h:
        return None
    story = (soup.find("div", {"class": lambda x: x and "article-body" in str(x)})
             or soup.find("article"))
    if not story:
        return None
    paras = story.find_all("p")
    if not paras:
        return None
    body = " ".join(p.text for p in paras)
    return h.text.strip(), body, _get_cat(url)


# --- 10. AajTak (Hindi → translated to English) ---
def extract_aajtak(soup, url):
    if not soup.find("html", {"lang": "hi"}):
        return None
    hd = soup.find("div", {"class": "story-heading"})
    if not hd:
        return None
    h = hd.find("h1")
    if not h:
        return None
    bd = soup.find("div", {"class": "story-with-main-sec"})
    if not bd:
        return None
    paras = bd.find_all("p")
    if not paras:
        return None
    news = " ".join(p.text for p in paras[: max(1, len(paras) - 4)])
    news = news.replace("\xa0", "").replace("\n", "")
    heading = h.text.replace("\xa0", "").replace("\n", "")
    try:
        from deep_translator import GoogleTranslator
        news = GoogleTranslator(source="auto", target="en").translate(news[:2300]) or news
        heading = GoogleTranslator(source="auto", target="en").translate(heading) or heading
    except Exception:
        pass
    return heading.strip(), news.strip(), _get_cat(url)


# COMMAND ----------

# MAGIC %md
# MAGIC ### Run All 15 Scrapers

# COMMAND ----------

print(f"{'='*60}")
print(f"  Scraping ALL major Indian news channels")
print(f"  Target date: {YESTERDAY}")
print(f"{'='*60}\n")

ALL_SOURCES = [
    ("https://timesofindia.indiatimes.com","timesofindia.indiatimes.com",extract_toi,           "TimesOfIndia"),
    ("https://www.hindustantimes.com",     "www.hindustantimes.com",    extract_ht,             "HindustanTimes"),
    ("https://www.thehindu.com",           "www.thehindu.com",          extract_thehindu,       "TheHindu"),
    ("https://indianexpress.com",          "indianexpress.com",         extract_indianexpress,  "IndianExpress"),
    ("https://www.indiatoday.in",          "www.indiatoday.in",         extract_indiatoday,     "IndiaToday"),
    ("https://theprint.in",                "theprint.in",               extract_theprint,       "ThePrint"),
    ("https://economictimes.indiatimes.com","economictimes.indiatimes.com",extract_et,           "EconomicTimes"),
    ("https://www.livemint.com",           "www.livemint.com",          extract_livemint,       "LiveMint"),
    ("https://scroll.in",                  "scroll.in",                 extract_scroll,         "Scroll"),
    ("https://www.aajtak.in",              "www.aajtak.in",             extract_aajtak,         "AajTak"),
]

all_articles = []
for base_url, domain, fn, name in ALL_SOURCES:
    print(f"\n--- {name} ---")
    try:
        articles = crawl_source(base_url, domain, fn, name)
        all_articles.extend(articles)
    except Exception as e:
        print(f"  [{name}] FAILED: {e}")


print(f"\n{'='*60}")
print(f"  Total articles scraped: {len(all_articles)}")
print(f"  From {len(set(a['channel'] for a in all_articles))} channels")
print(f"{'='*60}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Save to Volume (appends a new file per day, never overwrites)

# COMMAND ----------

volume_path = "/Volumes/major_project/news_pipeline/raw_files"
file_name = f"arrived_{YESTERDAY}.csv"
file_path = f"{volume_path}/{file_name}"

if all_articles:
    fieldnames = ["heading", "body", "category_from_url", "url", "channel", "article_date"]
    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(all_articles)

    size_kb = os.path.getsize(file_path) / 1024
    print(f"Saved {len(all_articles)} articles → {file_path}")
    print(f"File size: {size_kb:.1f} KB")

    # Channel breakdown
    from collections import Counter
    counts = Counter(a["channel"] for a in all_articles)
    print(f"\nPer channel:")
    for ch, cnt in counts.most_common():
        print(f"  {ch:20s}: {cnt}")
else:
    print("No articles scraped. Nothing saved.")
