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

# API-endpoints för Resume.se
JWT_URL = "https://www.resume.se/api/check-entitlements?userActive=true"
ARTICLE_API_URL = "https://www.resume.se/api/context?articleId={article_id}"

# Sajter att skrapa (utom Resume.se, som hanteras via API)
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

def get_jwt():
    """Hämta en ny JWT-token från Resume.se"""
    response = requests.get(JWT_URL, headers=HEADERS)

    print("🔎 Statuskod för JWT:", response.status_code)  # Skriver ut statuskoden
    print("🔎 Svar från servern:", response.text[:500])  # Skriver ut första 500 tecknen i svaret

    if response.status_code == 200:
        jwt_token = response.json().get("jwt")
        print("✅ Ny JWT hämtad:", jwt_token[:50] + "...")  # Visa en del av tokenen för verifiering
        return jwt_token
    else:
        print("❌ Misslyckades att hämta JWT")
        return None

def get_article(article_id, jwt_token):
    """Hämta en artikel från Resume.se med JWT-token"""
    url = ARTICLE_API_URL.format(article_id=article_id)
    headers = HEADERS.copy()
    headers["Authorization"] = f"Bearer {jwt_token}"

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Misslyckades att hämta artikel {article_id}")
        return None

def extract_article_data(article_json):
    """Extrahera titel, text och metadata från artikelns JSON-data"""
    title = article_json.get("seoTitle", "Okänd titel")
    body_parts = article_json.get("bodyParts", [])

    text = " ".join([part["bodyHtml"] for part in body_parts if part["type"] == "paragraph"])
    
    return {
        "title": title,
        "text": text,
        "date": datetime.now(timezone.utc).isoformat(),
        "source": "resume.se"
    }

def scrape_resume_articles():
    """Hämta artiklar från Resume.se via API istället för att skrapa HTML"""
    
    jwt_token = get_jwt()
    if not jwt_token:
        print("❌ Inget JWT-token, avbryter Resume.se-skrapning.")
        return []

    # Exempel på artikel-ID att testa – byt ut mot dynamisk insamling av ID:n om möjligt
    article_ids = ["38579619-c934-4ddd-9f0e-376d6aea3727"]

    articles = []
    for article_id in article_ids:
        article_json = get_article(article_id, jwt_token)
        if article_json:
            articles.append(extract_article_data(article_json))

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

    # 🔹 Skrapa Resume.se via API
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
