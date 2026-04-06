"""
Video scrapers for Indian news websites.
Scrapes video pages, extracts audio, converts speech-to-text (Hindi), translates to English.
Sources: AajTak, IndianExpress, ZeeNews
Outputs: .xlsx files with columns [Heading, VideoText, Body, URL]
"""

import os
import csv
import json
import time
import requests
from bs4 import BeautifulSoup
import xlsxwriter
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from deep_translator import GoogleTranslator
try:
    import moviepy.editor as mp
except ImportError:
    from moviepy import VideoFileClip
    # Create a shim so mp.VideoFileClip works
    class mp:
        VideoFileClip = VideoFileClip
import speech_recognition as sr


def _get_chrome_driver(headless=True, capture_network=False):
    """Create a headless Chrome WebDriver."""
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument('--headless')
    options.add_argument("--ignore-certificate-errors")
    if capture_network:
        options.add_argument('--enable-logging')
        options.add_argument('--log-level=0')
        options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    driver = webdriver.Chrome(options=options)
    return driver


# --------------- AajTak Video ---------------

def _aajtak_single_video(url):
    """Scrape a single AajTak video page: download .ts segments, extract audio, STT, translate."""
    main_url = url

    def download_video(dl_url, filename):
        r = requests.get(dl_url)
        with open(filename, 'wb') as f:
            f.write(r.content)

    driver = _get_chrome_driver(headless=True, capture_network=True)
    driver.get(url)

    title = driver.find_element(By.XPATH, '//div[@class="story-heading"]').text
    description = driver.find_element(By.XPATH, '//div[@class="common-area"]').text
    time.sleep(140)

    logs = driver.get_log("performance")
    with open("aajtak_network.json", "w", encoding="utf-8") as f:
        f.write("[")
        for log in logs:
            network_log = json.loads(log["message"])["message"]
            if any(x in network_log["method"] for x in ["Network.response", "Network.request", "Network.webSocket"]):
                f.write(json.dumps(network_log) + ",")
        f.write("{}]")
    driver.quit()

    with open("aajtak_network.json", "r", encoding="utf-8") as f:
        logs = json.loads(f.read())

    tsvideourl = []
    for i in range(len(logs)):
        try:
            u = logs[i]["params"]["request"]["url"]
            if u.endswith('.ts'):
                tsvideourl.append(u)
        except Exception:
            pass

    actualvideourl = []
    if tsvideourl:
        for u in tsvideourl:
            if u.split("/")[6] == tsvideourl[0].split("/")[6]:
                actualvideourl.append(u)

    video_text = ""
    count = 0
    for vid_url in actualvideourl:
        try:
            download_video(vid_url, f"aajtak{count}.ts")
            video = mp.VideoFileClip(f"aajtak{count}.ts")
            audio_file = video.audio
            audio_file.write_audiofile(f"aajtak{count}.wav")
            r = sr.Recognizer()
            with sr.AudioFile(f"aajtak{count}.wav") as source:
                data = r.record(source)
            text = r.recognize_google(data, language='hi')
            result = GoogleTranslator(source='auto', target='en').translate(text)
            video_text += result
        except Exception:
            pass
        finally:
            count += 1
            try:
                video.close()
                audio_file.close()
            except Exception:
                pass

    for i in range(count):
        for ext in [".ts", ".wav"]:
            try:
                os.remove(f"aajtak{i}{ext}")
            except Exception:
                pass
    try:
        os.remove("aajtak_network.json")
    except Exception:
        pass

    return title, video_text, description, main_url


# --------------- Indian Express Video ---------------

def _indianexpress_single_video(url):
    """Scrape a single IndianExpress video page via YouTube embed."""
    from pydub import AudioSegment
    from moviepy.editor import AudioFileClip

    main_url = url
    driver = _get_chrome_driver(headless=True)
    driver.get(url)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    title = driver.find_element(By.XPATH, "//h1[@class='heading']").text
    description = driver.find_element(By.XPATH, "//div[@class='yt-video-container']").text
    time.sleep(20)

    youtube_iframes = driver.find_elements(By.TAG_NAME, 'iframe')
    yt_url = ""
    for iframe in youtube_iframes:
        src = iframe.get_attribute('src')
        if src and 'youtube.com' in src:
            yt_url = src

    driver.quit()

    video_text = ""
    if yt_url:
        try:
            from pytube import YouTube
            yt = YouTube(yt_url)
            audio_stream = yt.streams.filter(only_audio=True).first()
            os.makedirs("audio", exist_ok=True)
            audio_stream.download(output_path="audio", filename="video.mp4")

            audio_clip = AudioFileClip("./audio/video.mp4")
            audio_clip.write_audiofile("./audio/video.wav", codec='pcm_s16le')
            audio_clip.close()

            audio = AudioSegment.from_wav("./audio/video.wav")
            chunk_size_ms = 10000
            start = 0
            while start < len(audio):
                chunk = audio[start:start + chunk_size_ms]
                chunk.export('temp_chunk.wav', format='wav')
                try:
                    r = sr.Recognizer()
                    with sr.AudioFile("temp_chunk.wav") as source:
                        data = r.record(source)
                    text = r.recognize_google(data, language='hi')
                    result = GoogleTranslator(source='auto', target='en').translate(text)
                    video_text += result
                except Exception:
                    pass
                start += chunk_size_ms

            for f in ["temp_chunk.wav", "audio/video.mp4", "audio/video.wav"]:
                try:
                    os.remove(f)
                except Exception:
                    pass
            try:
                os.rmdir("audio")
            except Exception:
                pass
        except Exception as e:
            print(f"  IndianExpress video error: {e}")

    return title, video_text, description, main_url


# --------------- Zee News Video ---------------

def _zeenews_single_video(url):
    """Scrape a single ZeeNews video page."""
    main_url = url

    def download_video(dl_url, filename):
        r = requests.get(dl_url)
        with open(filename, 'wb') as f:
            f.write(r.content)

    driver = _get_chrome_driver(headless=True, capture_network=True)
    driver.get(url)

    title = driver.find_element(By.TAG_NAME, "h1").text
    description = driver.find_element(By.XPATH, '//div[@class="video_decription"]').text
    try:
        play = driver.find_element(By.XPATH, "//button[@class='playkit-pre-playback-play-button']")
        play.click()
    except Exception:
        pass
    time.sleep(140)

    logs = driver.get_log("performance")
    with open("zeenews_network.json", "w", encoding="utf-8") as f:
        f.write("[")
        for log in logs:
            network_log = json.loads(log["message"])["message"]
            if any(x in network_log["method"] for x in ["Network.response", "Network.request", "Network.webSocket"]):
                f.write(json.dumps(network_log) + ",")
        f.write("{}]")
    driver.quit()

    with open("zeenews_network.json", "r", encoding="utf-8") as f:
        logs = json.loads(f.read())

    tsvideourl = []
    for i in range(len(logs)):
        try:
            u = logs[i]["params"]["request"]["url"]
            if u.endswith('.ts'):
                tsvideourl.append(u)
        except Exception:
            pass

    actualvideourl = []
    if tsvideourl:
        for u in tsvideourl:
            if u.split("/")[5] == tsvideourl[0].split("/")[5]:
                actualvideourl.append(u)

    video_text = ""
    count = 0
    for vid_url in actualvideourl:
        try:
            download_video(vid_url, f"zeenews{count}.ts")
            video = mp.VideoFileClip(f"zeenews{count}.ts")
            audio_file = video.audio
            audio_file.write_audiofile(f"zeenews{count}.wav")
            r = sr.Recognizer()
            with sr.AudioFile(f"zeenews{count}.wav") as source:
                data = r.record(source)
            text = r.recognize_google(data, language='hi')
            result = GoogleTranslator(source='auto', target='en').translate(text)
            video_text += result
        except Exception:
            pass
        finally:
            count += 1
            try:
                video.close()
                audio_file.close()
            except Exception:
                pass

    for i in range(count):
        for ext in [".ts", ".wav"]:
            try:
                os.remove(f"zeenews{i}{ext}")
            except Exception:
                pass
    try:
        os.remove("zeenews_network.json")
    except Exception:
        pass

    return title, video_text, description, main_url


# --------------- Crawl + Scrape Wrappers ---------------

def _crawl_video_links(start_url, domain, link_filter, csv_path, max_links=10):
    """Crawl a website and collect video page URLs into a CSV file."""
    visited = set()
    to_visit = [start_url]
    all_links = set()

    def fetch_html(u):
        try:
            r = requests.get(u, headers={'User-Agent': 'Mozilla/5.0'})
            return r.text if r.status_code == 200 else None
        except Exception:
            return None

    while to_visit and len(all_links) < max_links:
        current = to_visit.pop(0)
        if current in visited:
            continue
        html = fetch_html(current)
        if not html:
            continue
        soup = BeautifulSoup(html, 'html.parser')
        for tag in soup.find_all('a', href=True):
            href = tag['href']
            if not href.startswith('http'):
                href = f"https://{domain}" + href
            if domain in href:
                if link_filter(href) and href not in all_links and len(href) > 60:
                    all_links.add(href)
                to_visit.append(href)
        visited.add(current)

    with open(csv_path, 'w', newline='') as f:
        for link in all_links:
            f.write(link + '\n')

    return list(all_links)


def scrape_aajtak_videos(output_dir):
    """Crawl AajTak video pages and extract text from videos."""
    path = os.path.join(output_dir, "AajTak_Video.xlsx")
    csv_path = os.path.join(output_dir, "aajtak_link.csv")
    print(f"\n[AajTak Video] Crawling video links...")

    links = _crawl_video_links(
        "https://www.aajtak.in/videos", "www.aajtak.in",
        lambda href: "/video/" in href, csv_path, max_links=5
    )
    print(f"[AajTak Video] Found {len(links)} video links. Processing...")

    workbook = xlsxwriter.Workbook(path)
    ws = workbook.add_worksheet()
    ws.write(0, 0, "Heading"); ws.write(0, 1, "VideoText"); ws.write(0, 2, "Body"); ws.write(0, 3, "URL")
    row = 1

    for video_url in links:
        try:
            title, video_text, description, url = _aajtak_single_video(video_url)
            ws.write(row, 0, title)
            ws.write(row, 1, video_text)
            ws.write(row, 2, description)
            ws.write(row, 3, url)
            print(f"  [AajTak Video] {title[:60]}...")
            row += 1
        except Exception as e:
            print(f"  [AajTak Video] Error: {e}")

    workbook.close()
    print(f"[AajTak Video] Done - {row - 1} videos")


def scrape_indianexpress_videos(output_dir):
    """Crawl Indian Express video pages and extract text."""
    path = os.path.join(output_dir, "IndianExpress_Video.xlsx")
    csv_path = os.path.join(output_dir, "indianexpress_link.csv")
    print(f"\n[IndianExpress Video] Crawling video links...")

    links = _crawl_video_links(
        "https://indianexpress.com/", "indianexpress.com",
        lambda href: "/videos/" in href, csv_path, max_links=5
    )
    print(f"[IndianExpress Video] Found {len(links)} video links. Processing...")

    workbook = xlsxwriter.Workbook(path)
    ws = workbook.add_worksheet()
    ws.write(0, 0, "Heading"); ws.write(0, 1, "VideoText"); ws.write(0, 2, "Body"); ws.write(0, 3, "URL")
    row = 1

    for video_url in links:
        try:
            title, video_text, description, url = _indianexpress_single_video(video_url)
            ws.write(row, 0, title)
            ws.write(row, 1, video_text)
            ws.write(row, 2, description)
            ws.write(row, 3, url)
            print(f"  [IndianExpress Video] {title[:60]}...")
            row += 1
        except Exception as e:
            print(f"  [IndianExpress Video] Error: {e}")

    workbook.close()
    print(f"[IndianExpress Video] Done - {row - 1} videos")


def scrape_zeenews_videos(output_dir):
    """Crawl Zee News video pages and extract text."""
    path = os.path.join(output_dir, "ZeeNews_Video.xlsx")
    csv_path = os.path.join(output_dir, "zeenews_link.csv")
    print(f"\n[ZeeNews Video] Crawling video links...")

    links = _crawl_video_links(
        "https://zeenews.india.com/videos", "zeenews.india.com",
        lambda href: "com/video/" in href, csv_path, max_links=5
    )
    print(f"[ZeeNews Video] Found {len(links)} video links. Processing...")

    workbook = xlsxwriter.Workbook(path)
    ws = workbook.add_worksheet()
    ws.write(0, 0, "Heading"); ws.write(0, 1, "VideoText"); ws.write(0, 2, "Body"); ws.write(0, 3, "URL")
    row = 1

    for video_url in links:
        try:
            title, video_text, description, url = _zeenews_single_video(video_url)
            ws.write(row, 0, title)
            ws.write(row, 1, video_text)
            ws.write(row, 2, description)
            ws.write(row, 3, url)
            print(f"  [ZeeNews Video] {title[:60]}...")
            row += 1
        except Exception as e:
            print(f"  [ZeeNews Video] Error: {e}")

    workbook.close()
    print(f"[ZeeNews Video] Done - {row - 1} videos")


def scrape_all_videos(output_dir):
    """Run all video scrapers. Output goes to output_dir/*.xlsx"""
    os.makedirs(output_dir, exist_ok=True)
    scrape_aajtak_videos(output_dir)
    scrape_indianexpress_videos(output_dir)
    scrape_zeenews_videos(output_dir)
    print("\n=== All video scraping complete ===")


if __name__ == "__main__":
    scrape_all_videos(os.path.join(os.path.dirname(__file__), "..", "data"))
