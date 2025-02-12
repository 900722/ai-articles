import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

# Filnamn
ARTICLES_FILE = "articles_text.json"
PREVIOUS_ARTICLES_FILE = "previous_articles_text.json"

# 🔹 Cookies för att skrapa Resume.se i inloggat läge
RESUME_COOKIES = {
    "jwt": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6InBldHJvbmVsbGEuYmFydmFldXNAZ21haWwuY29tIiwiZ2l2ZW5fbmFtZSI6IlBldHJvbmVsbGEiLCJmYW1pbHlfbmFtZSI6IkJhcnZhZXVzIiwidmVyaWZpZWRFbWFpbCI6dHJ1ZSwiZW50aXRsZWQiOnRydWUsInBsdXNBbGx0Ijp0cnVlLCJoYXNoZWRVc2VySWQiOiI5NTE2MjhkZGViYjg5NzVmYjdlNTAwNWFkZWVkZDIyYjhmMjM1NDQxOTAxYjAyNGZlNThjYThkOWQ2MTlkMTI5IiwiaWF0IjoxNzM5Mzc5Mjg4LCJpc3MiOiJyZXN1bWUiLCJzdWIiOiJiYm0tcmVzOi8vMDA1MjAxYTMtMzAyYS00MDc2LTllMmEtYjU4MDk4ZWQ4NzVhIn0.tbiyReUyoYw2FPI-n0l0aefHYMVGu-GBy57oERjR7tK7b9XVaWXmYlNQ65ERgKi-j5f2yEQPXhQdlZxlEXXH-pAvQRtkB-dtAIIvz103ZBLL9B7by4Kj9E9yCaARx1A50Mb2ucZjcyweRM3v2EyQxf9c8jngTdR-Z4AtP80XQrte_oL129ZnhrEjrdcOCMW1Il5eH4K1g24NcLs2zfCga7n9VPHlJszrNtGG36bkLrvl6-AcfzgCjgqtC1TxOkrxjsabKX3wrjB8wkafdYXWcsnzwz0C5INwpdL4yxS6N4xcYG2hIzPFWmuqPjMSb0-zJ9Zi6LbK-w8kH5ScCocLvD1HD5NYwofgiezzKxfgRdE6VHGKjcwMORlWsA08Dc0E7DbL1uS44LPTXqyJ5x3tAXyehkVKQ9EttiLgM-LzPwoccqbaD3mT4KpVjE5JtkflSoCR0etNuDqYdOQjWhnA5chrBTlHVBK1CrjBfV6ZeYmkUnyfIMteLcA1zWOjISCa-H1wEK2rQ1p_6MPjxkYykNJxktubFnflj4WqpG9siBQIbAldjk8lV57mU-jkathWDc4AwrxM4v5E2s-EYw0nLjZnR2lOme9BM9OIDMRW5k0EjDWMnT4iJRYDWllRJPs9pInVkdTKSNyUVx_nVl3RRK8dI0kZhxGQb2Iz_TmyeMg",
    "tapet-paywall-session": "s%3AmfB2XE9dhuJhz3Ny8msq3Ofj-e8Y8nNg.f%2BbLNV6cPfSHBs5X4t3KF8bwKhUICEzjDdqVz8eLbYk"
}

# 🔹 Korrekt lista över sajter att skrapa (med text_selector)
SITES = [
    {
        "name": "DI.se",
        "url": "https://www.di.se/amnen/artificiell-intelligens/",
        "article_selector": "article.js_watch-teaser",
        "title_selector": "h2.news-item__heading",
        "link_selector": "a[href]",
        "text_selector": "div.article__lead.global-l-bold p",
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
        "text_selector": "div.entry-content p",
        "base_url": "https://techcrunch.com"
    },
    {
        "name": "Wired",
        "url": "https://www.wired.com/tag/artificial-intelligence/",
        "article_selector": "div.archive-item-component",
        "title_selector": "h2.archive-item-component__title",
        "link_selector": "a.archive-item-component__link",
        "text_selector": "div.body__inner-container p",
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
    """Skrapa artiklar från de angivna sajterna, inklusive brödtext."""
    articles = []
    
    for site in SITES:
        print(f"🔍 Skrapar artiklar från: {site['name']}")
        
        # 🔹 Specialhantering för Resume.se (inloggat läge)
        if site["name"] == "Resume.se":
            session = requests.Session()
            session.cookies.update(RESUME_COOKIES)  # Lägg till cookies
            response = session.get(site["url"], timeout=10)
        else:
            response = requests.get(site["url"], timeout=10)

        if response.status_code != 200:
            print(f"⚠️ Misslyckades att hämta {site['name']}: {response.status_code}")
            continue

        soup = BeautifulSoup(response.text, "html.parser")

        for article in soup.select(site["article_selector"]):
            title_tag = article.select_one(site["title_selector"])
            link_tag = article.select_one(site["link_selector"])
            text_tag = article.select(site["text_selector"])  # Hämta brödtext som en lista av p-taggar

            if not title_tag or not link_tag or "href" not in link_tag.attrs:
                continue

            title = title_tag.text.strip()
            link = urljoin(site["base_url"], link_tag["href"])
            text = " ".join([p.get_text(strip=True) for p in text_tag]) if text_tag else "Ingen brödtext tillgänglig"

            articles.append({
                "title": title,
                "link": link,
                "text": text,
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
