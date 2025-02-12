import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

# Filnamn
ARTICLES_FILE = "articles_text.json"
PREVIOUS_ARTICLES_FILE = "previous_articles_text.json"

# Headers för att simulera en webbläsare
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Cookies från DevTools för Resume.se
RESUME_COOKIES = {
    "jwt": "DITT_JWT_COOKIE_HÄR",
    "tapet-paywall-session": "DITT_SESSION_COOKIE_HÄR"
}

# Sajter att skrapa (utom Resume.se, som hanteras separat)
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

def scrape_resume_articles():
    """Hämta artiklar från Resume.se genom att skrapa HTML istället för API."""
    
    # Lista på artikel-URL:er att hämta
    article_urls = [
        "https://www.resume.se/fordjupning/granskning/hyper-island-student-jag-har-investerat-allt-nu-riskerar-jag-att-forlora-allt/"
    ]

    articles = []

    for url in article_urls:
        response = requests.get(url, headers=HEADERS, cookies=RESUME_COOKIES)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")

            # 🔍 Hämta titel
            title_tag = soup.find("meta", property="og:title")
            title = title_tag["content"] if title_tag else "Okänd titel"

            # 🔍 Hämta artikelns text (paragrafer)
            paragraphs = soup.find_all("p")
            text = " ".join([p.get_text(strip=True) for p in paragraphs])

            articles.append({
                "title": title,
                "text": text,
                "link": url,
                "date": datetime.now(timezone.utc).isoformat(),
                "source": "resume.se"
            })
            print(f"✅ Artikel hämtad: {title}")

        else:
            print(f"❌ Misslyckades att hämta artikel från Resume.se: {url}")

    return articles

def scrape_other_sites():
    """Skrapa artiklar från andra sajter (ej Resume.se)"""
    articles = []

    for site in SITES:
        print(f"🔍 Skrapar artiklar från: {site['name']}")
        response = requests.get(site["url"], headers=HEADERS, timeout=10)

        if response.status_code != 200:
            print(f"⚠️ Misslyckades att hämta {site['name']}: {response.status_code}")
            continue

        soup = BeautifulSoup(response.text, "html.parser")

        for article in soup.select(site["article_selector"]):
            title_tag = article.select_one(site["title_selector"])
            link_tag = article.select_one(site["link_selector"])
            text_tag = article.select(site["text_selector"])

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
    
    previous_articles = load_json_file(PREVIOUS_ARTICLES_FILE)
    previous_titles = {article["title"] for article in previous_articles}

    # 🔹 Skrapa Resume.se via HTML
    new_articles_resume = scrape_resume_articles()

    # 🔹 Skrapa andra sajter via BeautifulSoup
    new_articles_other = scrape_other_sites()

    # 🔄 Kombinera alla skrapade artiklar
    new_articles = new_articles_resume + new_articles_other

    # Filtrera bort dubbletter
    fresh_articles = [article for article in new_articles if article["title"] not in previous_titles]

    if not fresh_articles:
        print("✅ Inga nya artiklar hittades.")
        return

    save_json_file(ARTICLES_FILE, fresh_articles)
    all_articles = previous_articles + fresh_articles
    save_json_file(PREVIOUS_ARTICLES_FILE, all_articles)

    print(f"✅ Sparade {len(fresh_articles)} nya artiklar.")

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

if __name__ == "__main__":
    update_articles()
