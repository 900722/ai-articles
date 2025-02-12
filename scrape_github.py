import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

# Filnamn
ARTICLES_FILE = "articles_text.json"
PREVIOUS_ARTICLES_FILE = "previous_articles_text.json"

# 🔹 Korrekt lista över sajter att skrapa (hämtad från ditt script)
SITES = [
    {
        "name": "DI.se",
        "url": "https://www.di.se/amnen/artificiell-intelligens/",
        "article_selector": "article.js_watch-teaser",
        "title_selector": "h2.news-item__heading",
        "link_selector": "a[href]",
        "text_selector": "div.article__lead p",
        "base_url": "https://www.di.se"
    },
    {
        "name": "Resume.se",
        "url": "https://www.resume.se/om/artificiell-intelligens-ai/",
        "article_selector": "article",
        "title_selector": "h2",
        "link_selector": "article a[href]",
        "text_selector": "div.paywalled p",
        "base_url": "https://www.resume.se"
    },
    {
        "name": "TechCrunch",
        "url": "https://techcrunch.com/tag/artificial-intelligence/",
        "article_selector": "article.post-block",
        "title_selector": "h2.post-block__title",
        "link_selector": "a.post-block__title__link",
        "text_selector": "div.article-content p",
        "base_url": "https://techcrunch.com"
    },
    {
        "name": "Wired",
        "url": "https://www.wired.com/tag/artificial-intelligence/",
        "article_selector": "div.archive-item-component",
        "title_selector": "h2.archive-item-component__title",
        "link_selector": "a.archive-item-component__link",
        "text_selector": "div.article-body-component p",
        "base_url": "https://www.wired.com"
    }
]

def load_json_file(filename):
    """Ladda en JSON-fil om den finns, annars returnera en tom lista."""
    try:
        with open(filename, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_json_file(filename, data):
    """Spara data i en JSON-fil."""
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

def scrape_articles():
    """Skrapa artiklar från de angivna sajterna."""
    articles = []
    
    for site in SITES:
        print(f"🔍 Skrapar artiklar från: {site['name']}")
        try:
            response = requests.get(site["url"], timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"⚠️ Misslyckades att hämta {site['name']}: {e}")
            continue

        soup = BeautifulSoup(response.text, "html.parser")

        for article in soup.select(site["article_selector"]):
            title_tag = article.select_one(site["title_selector"])
            link_tag = article.select_one(site["link_selector"])

            if not title_tag or not link_tag or "href" not in link_tag.attrs:
                continue

            title = title_tag.text.strip()
            link = urljoin(site["base_url"], link_tag["href"])

            articles.append({
                "title": title,
                "link": link,
                "date": datetime.now(timezone.utc).isoformat(),
                "source": urlparse(link).netloc.replace("www.", "")
            })
    
    return articles

def update_articles():
    """Uppdatera JSON-filer med nya artiklar och spara historik."""
    
    # Läs in tidigare skrapade artiklar
    previous_articles = load_json_file(PREVIOUS_ARTICLES_FILE)
    previous_titles = {article["title"] for article in previous_articles}
    
    # Skrapa nya artiklar
    new_articles = scrape_articles()
    
    # Filtrera bort dubbletter
    fresh_articles = [article for article in new_articles if article["title"] not in previous_titles]

    if not fresh_articles:
        print("✅ Inga nya artiklar hittades.")
        return

    # Uppdatera JSON-filerna
    save_json_file(ARTICLES_FILE, fresh_articles)
    
    # Lägg till nya artiklar i den historiska filen
    all_articles = previous_articles + fresh_articles
    save_json_file(PREVIOUS_ARTICLES_FILE, all_articles)

    print(f"✅ Sparade {len(fresh_articles)} nya artiklar.")
    
if __name__ == "__main__":
    update_articles()
