"""
Text article scrapers for Indian news websites.
Scrapes ONLY articles published YESTERDAY.
Sources: ThePrint, News18, IndiaTv, IndiaToday, AajTak, News18 Punjab
Outputs: .xlsx files with columns [Heading, Body, Category, URL, Date]
"""

import requests
from bs4 import BeautifulSoup
import xlsxwriter
from deep_translator import GoogleTranslator
import os
import re
from datetime import datetime, timedelta


HEADERS = {
    'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) '
                  'AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148'
}

MAX_PAGES_TO_CRAWL = 200  # crawl more pages to find all yesterday's articles
YESTERDAY = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")  # e.g. "2026-03-28"


def _get_article_date(soup, url):
    """
    Extract the publish date from an article page.
    Tries multiple methods:
      1. <meta property="article:published_time">
      2. <meta name="publish-date"> or <meta name="date">
      3. <time datetime="..."> tag
      4. JSON-LD script (datePublished)
      5. Date pattern in URL like /2026/03/28/
    Returns date string as "YYYY-MM-DD" or None if not found.
    """
    # Method 1: Open Graph meta tag (most common)
    for attr in ['article:published_time', 'og:article:published_time']:
        meta = soup.find('meta', {'property': attr})
        if meta and meta.get('content'):
            try:
                return meta['content'][:10]  # "2026-03-28T14:00:00" -> "2026-03-28"
            except Exception:
                pass

    # Method 2: Other meta tags
    for name in ['publish-date', 'date', 'pubdate', 'publishdate', 'Date']:
        meta = soup.find('meta', {'name': name})
        if meta and meta.get('content'):
            try:
                return meta['content'][:10]
            except Exception:
                pass

    # Method 3: <time> tag with datetime attribute
    time_tag = soup.find('time', {'datetime': True})
    if time_tag:
        try:
            return time_tag['datetime'][:10]
        except Exception:
            pass

    # Method 4: JSON-LD structured data
    for script in soup.find_all('script', {'type': 'application/ld+json'}):
        try:
            import json
            data = json.loads(script.string)
            if isinstance(data, list):
                data = data[0]
            if 'datePublished' in data:
                return data['datePublished'][:10]
        except Exception:
            pass

    # Method 5: Date in URL pattern like /2026/03/28/ or /2026-03-28/
    date_pattern = re.search(r'/(\d{4})/(\d{2})/(\d{2})/', url)
    if date_pattern:
        return f"{date_pattern.group(1)}-{date_pattern.group(2)}-{date_pattern.group(3)}"

    date_pattern2 = re.search(r'/(\d{4}-\d{2}-\d{2})/', url)
    if date_pattern2:
        return date_pattern2.group(1)

    return None


def _is_yesterday(date_str):
    """Check if a date string matches yesterday's date."""
    if not date_str:
        return False
    return date_str == YESTERDAY


def _crawl_and_collect(base_url, domain, worksheet, extract_fn, target_date=YESTERDAY):
    """
    Generic crawler: discovers links from base_url, extracts article data,
    but ONLY keeps articles published on target_date (yesterday).
    """
    r = requests.get(base_url, headers=HEADERS)
    urls_to_visit = []
    unique_urls = {}
    row = 1
    count = 0
    pages_visited = 0

    if r.status_code == 200:
        soup = BeautifulSoup(r.text, 'html.parser')
        for url_tag in soup.findAll('a'):
            try:
                if url_tag.has_attr('href'):
                    href = url_tag['href']
                    if "video" not in href.split("/") and "tag" not in href.split("/") and "author" not in href.split("/"):
                        if href.startswith('/') and f"https://{domain}" + href not in unique_urls:
                            full = f"https://{domain}" + href
                            unique_urls[full] = True
                            urls_to_visit.append(full)
                        elif href.startswith('h') and domain in href and href not in unique_urls:
                            unique_urls[href] = True
                            urls_to_visit.append(href)
            except Exception:
                continue

    print(f"  Filtering for articles from: {target_date}")

    while urls_to_visit and pages_visited < MAX_PAGES_TO_CRAWL:
        url_to_visit = urls_to_visit.pop(0)
        skip_segments = ["tags", "tag", "livetv", "video", "videos",
                         "web-stories", "astrology", "news-podcasts",
                         "lifestyle", "visualstories"]
        if not url_to_visit.startswith('h'):
            continue
        if any(seg in url_to_visit.split("/") for seg in skip_segments):
            continue

        try:
            r = requests.get(url_to_visit, headers=HEADERS, timeout=10)
            if r.status_code != 200:
                continue
            pages_visited += 1
            soup = BeautifulSoup(r.text, 'html.parser')

            # Discover more links
            for url_tag in soup.findAll('a'):
                try:
                    if url_tag.has_attr('href'):
                        href = url_tag['href']
                        if "video" not in href.split("/") and "tag" not in href.split("/") and "author" not in href.split("/"):
                            if href.startswith('/') and f"https://{domain}" + href not in unique_urls:
                                full = f"https://{domain}" + href
                                unique_urls[full] = True
                                urls_to_visit.append(full)
                            elif href.startswith('h') and domain in href and href not in unique_urls:
                                unique_urls[href] = True
                                urls_to_visit.append(href)
                except Exception:
                    continue

            # Check if this article is from yesterday
            article_date = _get_article_date(soup, url_to_visit)
            if not _is_yesterday(article_date):
                continue  # skip — not yesterday's article

            # Extract article content
            result = extract_fn(soup, url_to_visit)
            if result:
                heading, body, category, url = result
                worksheet.write(row, 0, heading)
                worksheet.write(row, 1, body)
                worksheet.write(row, 2, category)
                worksheet.write(row, 3, url)
                worksheet.write(row, 4, target_date)
                row += 1
                count += 1
                print(f"  [{count}] [{article_date}] {heading[:60]}...")
        except Exception:
            continue

    print(f"  Pages visited: {pages_visited}, Articles from {target_date}: {count}")
    return count


def _extract_theprint(soup, url):
    if not (soup.find('h1') and (soup.find('html', {'lang': 'en'}) or
            soup.find('html', {'lang': 'en-US'}) or soup.find('html', {'lang': 'en-UK'}))):
        return None
    heading = soup.find('h1')
    post = soup.find('div', {'id': 'postexcerpt'})
    if not post:
        return None
    paragraphs = post.findAll('p')
    if not paragraphs:
        return None
    news = ""
    for i in range(max(0, len(paragraphs) - 4)):
        news += paragraphs[i].text
    category = url.split("/")[3] if len(url.split("/")) > 3 else ""
    return heading.text, news, category, url


def _extract_news18(soup, url):
    heading_el = soup.find('h1', {'class': lambda x: x and 'article_heading1' in x})
    if not heading_el:
        return None
    if not (soup.find('html', {'lang': 'en'}) or soup.find('html', {'lang': 'en-us'})):
        return None
    body_div = soup.find('div', {'class': lambda x: x and 'article-body' in x})
    if not body_div:
        return None
    paragraphs = body_div.findAll('p')
    if not paragraphs:
        return None
    news = "".join(p.text for p in paragraphs)
    category = url.split("/")[3] if len(url.split("/")) > 3 else ""
    return heading_el.text, news, category, url


def _extract_indiatv(soup, url):
    title_div = soup.find('div', {'class': 'article-title'})
    if not title_div:
        return None
    if not (soup.find('html', {'lang': 'en'}) or soup.find('html', {'lang': 'en-us'})):
        return None
    heading = title_div.find('h1')
    if not heading:
        return None
    content_div = soup.find('div', {'id': 'content'})
    if not content_div:
        return None
    paragraphs = content_div.findAll('p')
    if not paragraphs:
        return None
    news = ""
    for i in range(max(0, len(paragraphs) - 4)):
        news += paragraphs[i].text
    parts = url.split("/")
    category = parts[4] if len(parts) > 4 and parts[3] == 'news' else parts[3] if len(parts) > 3 else ""
    return heading.text, news, category, url


def _extract_indiatoday(soup, url):
    body_div = soup.find('div', {'class': lambda x: x and 'story__content__body' in str(x)})
    if not body_div:
        return None
    if not (soup.find('html', {'lang': 'en'}) or soup.find('html', {'lang': 'en-us'})):
        return None
    heading = body_div.find('h1')
    if not heading:
        return None
    desc_div = soup.find('div', {'class': lambda x: x and 'Story_description' in str(x)})
    if not desc_div:
        return None
    paragraphs = desc_div.findAll('p')
    if not paragraphs:
        return None
    news = "".join(p.text for p in paragraphs)
    parts = url.split("/")
    category = "india" if len(parts) > 3 and parts[3] == 'cities' else parts[3] if len(parts) > 3 else ""
    return heading.text, news, category, url


def _extract_aajtak(soup, url):
    """AajTak articles are in Hindi - translates to English."""
    if not soup.find('html', {'lang': 'hi'}):
        return None
    heading_div = soup.find('div', {'class': 'story-heading'})
    if not heading_div:
        return None
    heading = heading_div.find('h1')
    if not heading:
        return None
    body_div = soup.find('div', {'class': 'story-with-main-sec'})
    if not body_div:
        return None
    paragraphs = body_div.findAll('p')
    if not paragraphs:
        return None
    news = ""
    for i in range(max(0, len(paragraphs) - 4)):
        news += paragraphs[i].text
    news = news.replace("\xa0", "").replace("\n", "")
    heading_text = heading.text.replace("\xa0", "").replace("\n", "")
    try:
        news = GoogleTranslator(source='auto', target='en').translate(news[:2300])
        heading_text = GoogleTranslator(source='auto', target='en').translate(heading_text)
    except Exception as e:
        print(f"  Translation error: {e}")
    category = url.split("/")[3] if len(url.split("/")) > 3 else ""
    return heading_text, news, category, url


def _extract_news18_punjab(soup, url):
    """News18 Punjab articles - translates Punjabi to English."""
    heading_el = soup.find('h1', {'class': lambda x: x and 'article_heading1' in x})
    if not heading_el:
        return None
    if not soup.find('html', {'lang': 'pa'}):
        return None
    body_div = soup.find('div', {'class': lambda x: x and 'article_content' in x})
    if not body_div:
        return None
    paragraphs = body_div.findAll('p')
    if not paragraphs:
        return None
    news = "".join(p.text for p in paragraphs)
    news = news.replace("\xa0", "").replace("\n", "")
    heading_text = heading_el.text.replace("\xa0", "").replace("\n", "")
    try:
        news = GoogleTranslator(source='auto', target='en').translate(news[:2300])
        heading_text = GoogleTranslator(source='auto', target='en').translate(heading_text)
    except Exception as e:
        print(f"  Translation error: {e}")
    category = url.split("/")[3] if len(url.split("/")) > 3 else ""
    return heading_text, news, category, url


def _make_workbook(output_dir, filename):
    """Create a workbook with headers including Date column."""
    path = os.path.join(output_dir, filename)
    workbook = xlsxwriter.Workbook(path)
    ws = workbook.add_worksheet()
    ws.write(0, 0, "Heading")
    ws.write(0, 1, "Body")
    ws.write(0, 2, "Category")
    ws.write(0, 3, "URL")
    ws.write(0, 4, "Date")
    return workbook, ws, path


def scrape_theprint(output_dir):
    workbook, ws, path = _make_workbook(output_dir, "ThePrint.xlsx")
    print(f"\n[ThePrint] Scraping yesterday's articles ({YESTERDAY}) -> {path}")
    count = _crawl_and_collect("https://theprint.in", "theprint.in", ws, _extract_theprint)
    workbook.close()
    print(f"[ThePrint] Done - {count} articles from {YESTERDAY}")


def scrape_news18(output_dir):
    workbook, ws, path = _make_workbook(output_dir, "News18.xlsx")
    print(f"\n[News18] Scraping yesterday's articles ({YESTERDAY}) -> {path}")
    count = _crawl_and_collect("https://www.news18.com", "www.news18.com", ws, _extract_news18)
    workbook.close()
    print(f"[News18] Done - {count} articles from {YESTERDAY}")


def scrape_indiatv(output_dir):
    workbook, ws, path = _make_workbook(output_dir, "IndiaTv.xlsx")
    print(f"\n[IndiaTv] Scraping yesterday's articles ({YESTERDAY}) -> {path}")
    count = _crawl_and_collect("https://www.indiatvnews.com", "www.indiatvnews.com", ws, _extract_indiatv)
    workbook.close()
    print(f"[IndiaTv] Done - {count} articles from {YESTERDAY}")


def scrape_indiatoday(output_dir):
    workbook, ws, path = _make_workbook(output_dir, "IndiaToday.xlsx")
    print(f"\n[IndiaToday] Scraping yesterday's articles ({YESTERDAY}) -> {path}")
    count = _crawl_and_collect("https://www.indiatoday.in", "www.indiatoday.in", ws, _extract_indiatoday)
    workbook.close()
    print(f"[IndiaToday] Done - {count} articles from {YESTERDAY}")


def scrape_aajtak(output_dir):
    workbook, ws, path = _make_workbook(output_dir, "AajTak.xlsx")
    print(f"\n[AajTak] Scraping yesterday's Hindi articles ({YESTERDAY}) -> {path}")
    count = _crawl_and_collect("https://www.aajtak.in", "www.aajtak.in", ws, _extract_aajtak)
    workbook.close()
    print(f"[AajTak] Done - {count} articles from {YESTERDAY}")


def scrape_news18_punjab(output_dir):
    workbook, ws, path = _make_workbook(output_dir, "News18_Punjab.xlsx")
    print(f"\n[News18 Punjab] Scraping yesterday's Punjabi articles ({YESTERDAY}) -> {path}")
    count = _crawl_and_collect("https://punjab.news18.com", "punjab.news18.com", ws, _extract_news18_punjab)
    workbook.close()
    print(f"[News18 Punjab] Done - {count} articles from {YESTERDAY}")


def scrape_all_text(output_dir):
    """Run all text article scrapers. Collects ONLY yesterday's articles."""
    os.makedirs(output_dir, exist_ok=True)
    print(f"\n{'='*60}")
    print(f"  Collecting all articles from YESTERDAY: {YESTERDAY}")
    print(f"{'='*60}")
    scrape_indiatoday(output_dir)
    scrape_news18(output_dir)
    scrape_indiatv(output_dir)
    scrape_theprint(output_dir)
    scrape_aajtak(output_dir)
    scrape_news18_punjab(output_dir)
    print(f"\n=== All text scraping complete (date: {YESTERDAY}) ===")


if __name__ == "__main__":
    scrape_all_text(os.path.join(os.path.dirname(__file__), "..", "data"))
