import json
import os
import time
import feedparser  # 📡 För att hantera RSS-flödet
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin, urlparse

# Selenium konfiguration
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Filnamn
ARTICLES_FILE = "articles_text.json"
PREVIOUS_ARTICLES_FILE = "previous_articles_text.json"

# Sajter att skrapa (med korrekta selektorer)
SITES = [
    {
        "name": "DI.se",
        "url": "https://www.di.se/amnen/artificiell-intelligens/",
        "article_selector": "article.js_watch-teaser",
        "title_selector": "h2.news-item__heading",
        "link_selector": "a[href]",
        "text_selector": "div.article__lead.global-l-bold p",
        "base_url": "https://www.di.se"
    }
]

# Ladda JSON-filer
def load_json_file(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as file:
            return json.load(file)
    return []

# Spara JSON-filer
def save_json_file(filename, data):
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

# Undvik dubbletter
def is_duplicate(new_article, articles_list):
    return any(
        article["title"] == new_article["title"] and article["link"] == new_article["link"]
        for article in articles_list
    )

# 📰 Skrapa Resume-artiklar (inklusive paywalled content)
def scrape_resume_articles():
    base_url = "https://www.resume.se/"
    CHROMEDRIVER_PATH = "/usr/local/bin/chromedriver"
    driver = webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=chrome_options)
    driver.get(base_url)

    articles = []
    soup = BeautifulSoup(driver.page_source, "html.parser")
    links = [a["href"] for a in soup.select("a") if a.has_attr("href") and a["href"].startswith("https://www.resume.se")]

    for link in set(links):
        driver.get(link)
        time.sleep(2)

        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.paywalled p"))
            )
        except:
            print(f"⚠️ Ingen paywall-innehåll hittades på {link}")

        soup = BeautifulSoup(driver.page_source, "html.parser")
        paragraphs = soup.select("div.paywalled p") or soup.find_all("p")
        text = " ".join([p.get_text(strip=True) for p in paragraphs])

        article = {
            "title": soup.find("h1").get_text(strip=True),
            "text": text if text else "Ingen brödtext tillgänglig",
            "link": link,
            "date": datetime.utcnow().isoformat(),
            "source": "resume.se",
        }

        if not is_duplicate(article, articles):
            articles.append(article)

    driver.quit()
    return articles

# 📰 Skrapa TechCrunch-artiklar via RSS
def scrape_techcrunch_articles():
    rss_url = "https://techcrunch.com/category/artificial-intelligence/feed/"
    feed = feedparser.parse(rss_url)

    articles = []
    print(f"📡 Hämtar artiklar från TechCrunch RSS ({len(feed.entries)} hittade)")

    for entry in feed.entries:
        article_url = entry.link

        response = requests.get(article_url)
        if response.status_code != 200:
            print(f"⚠️ Kunde inte hämta {article_url} - Statuskod: {response.status_code}")
            continue

        soup = BeautifulSoup(response.text, "html.parser")

        title_tag = soup.select_one("h2.post-block__title")
        title = title_tag.text.strip() if title_tag else "Ingen titel hittad"

        text_tag = soup.select("div.entry-content p")
        text = " ".join([p.get_text(strip=True) for p in text_tag]) if text_tag else "Ingen brödtext tillgänglig"

        article = {
            "title": title,
            "link": article_url,
            "text": text,
            "date": datetime.utcnow().isoformat(),
            "source": "techcrunch.com"
        }

        if not is_duplicate(article, articles):
            articles.append(article)

    return articles

# 📰 Skrapa Wired-artiklar via RSS
def scrape_wired_articles():
    rss_url = "https://www.wired.com/feed/tag/ai/latest/rss"
    feed = feedparser.parse(rss_url)

    articles = []
    print(f"📡 Hämtar artiklar från Wired RSS ({len(feed.entries)} hittade)")

    for entry in feed.entries:
        article_url = entry.link

        response = requests.get(article_url)
        if response.status_code != 200:
            print(f"⚠️ Kunde inte hämta {article_url} - Statuskod: {response.status_code}")
            continue

        soup = BeautifulSoup(response.text, "html.parser")

        title_tag = soup.select_one("h2.archive-item-component__title")
        title = title_tag.text.strip() if title_tag else "Ingen titel hittad"

        text_tag = soup.select("div.body__inner-container p")
        text = " ".join([p.get_text(strip=True) for p in text_tag]) if text_tag else "Ingen brödtext tillgänglig"

        article = {
            "title": title,
            "link": article_url,
            "text": text,
            "date": datetime.utcnow().isoformat(),
            "source": "wired.com"
        }

        if not is_duplicate(article, articles):
            articles.append(article)

    return articles

# 🔄 Uppdatera JSON-filer och undvik dubbletter
def update_articles():
    previous_articles = load_json_file(PREVIOUS_ARTICLES_FILE)
    new_articles_resume = scrape_resume_articles()
    new_articles_techcrunch = scrape_techcrunch_articles()  
    new_articles_wired = scrape_wired_articles()  # ✅ Wired via RSS
    new_articles_other = scrape_other_sites()

    all_articles = previous_articles + new_articles_resume + new_articles_techcrunch + new_articles_wired + new_articles_other

    unique_articles = {article["link"]: article for article in all_articles}.values()

    save_json_file(ARTICLES_FILE, list(unique_articles))
    save_json_file(PREVIOUS_ARTICLES_FILE, list(unique_articles))

# ✅ Kör endast om detta script körs direkt
if __name__ == "__main__":
    update_articles()
