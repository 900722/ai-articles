# 📌 Importera nödvändiga bibliotek
from google.colab import drive
import os
import json
import requests
import time
import random
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

# 1️⃣ Koppla Google Drive till Colab
drive.mount('/content/drive')

# 2️⃣ Ange sökvägar till filerna i Google Drive
base_folder = "/content/drive/My Drive/WebScrapingFiler"
os.makedirs(base_folder, exist_ok=True)
previous_articles_path = os.path.join(base_folder, "previous_articles.json")
new_articles_path = os.path.join(base_folder, "articles.json")  # Fil med endast nya artiklar

# 3️⃣ Funktion för att ladda tidigare artiklar
def load_previous_articles():
    if os.path.exists(previous_articles_path):
        with open(previous_articles_path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []  # Returnera tom lista om filen är korrupt
    return []  # Om filen inte finns, returnera tom lista

# 4️⃣ Funktion för att spara previous_articles.json
def save_previous_articles(all_articles):
    unique_articles = {article["link"]: article for article in all_articles}
    with open(previous_articles_path, "w", encoding="utf-8") as f:
        json.dump(list(unique_articles.values()), f, ensure_ascii=False, indent=4)
    print(f"✅ Uppdaterade previous_articles.json med {len(unique_articles)} artiklar.")

# 5️⃣ Funktion för att spara endast nya artiklar i articles.json
def save_new_articles(new_articles):
    # Om inga nya artiklar hittades, skapa en standardpost med "No content available"
    if not new_articles:
        new_articles = [{
            "title": "No content available",
            "link": "No content available",
            "date": "No content available",
            "source": "No content available",
            "text": "No content available"
        }]

    with open(new_articles_path, "w", encoding="utf-8") as f:
        json.dump(new_articles, f, ensure_ascii=False, indent=4)
    print(f"✅ {len(new_articles)} nya artiklar sparade i articles.json.")

# 6️⃣ Webbsajter att skrapa
SITES = {
    "di": "https://www.di.se/amnen/artificiell-intelligens/",
    "resume": "https://www.resume.se/om/artificiell-intelligens-ai/",
    "techcrunch": "https://techcrunch.com/tag/artificial-intelligence/",
    "wired": "https://www.wired.com/tag/artificial-intelligence/"
}

# 7️⃣ Skrapfunktion
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

session = requests.Session()

def scrape_site(site_name, url, article_selector, title_selector, link_selector, text_selector, base_url=""):
    """Generisk funktion för att skrapa en sajt"""
    print(f"🚀 Hämtar artiklar från {site_name}...")

    headers = {"User-Agent": random.choice(USER_AGENTS)}
    try:
        response = session.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"❌ Misslyckades att hämta {site_name}. Statuskod: {response.status_code}")
            return []
    except requests.RequestException as e:
        print(f"❌ Fel vid hämtning av {site_name}: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    previous_articles = load_previous_articles()
    articles = []

    for article in soup.select(article_selector):
        try:
            title_tag = article.select_one(title_selector)
            link_tag = article.select_one(link_selector)

            title = title_tag.text.strip() if title_tag else "No content available"
            link = link_tag["href"] if link_tag and "href" in link_tag.attrs else "No content available"
            full_link = urljoin(base_url, link)
            source_domain = urlparse(full_link).netloc  # Hämta domännamnet från länken

            # Hämta hela brödtexten genom att slå ihop alla <p>-taggar
            if text_selector:
                text_elements = article.select(text_selector)
                text = " ".join([p.text.strip() for p in text_elements]) if text_elements else "No content available"
            else:
                text = "No content available"

            # Kontrollera om artikeln redan finns
            if any(prev["link"] == full_link for prev in previous_articles):
                print(f"⚠️ Skipping redan skrapad artikel: {title}")
                continue  

            print(f"🔍 Hittad ny artikel: {title} ({full_link}) från {source_domain}")

            articles.append({
                "title": title,
                "link": full_link,
                "date": datetime.now(timezone.utc).isoformat(),
                "source": source_domain,  # Lägg till källans domän
                "text": text  # Lägg till hela artikeltexten
            })

            time.sleep(random.uniform(3, 6))

        except Exception as e:
            print(f"❌ Fel vid skrapning av artikel: {e}")

    print(f"✅ Hittade {len(articles)} nya artiklar från {site_name}!")
    return articles

# 8️⃣ Skrapa från specifika sajter
def scrape_di():
    return scrape_site("DI.se", SITES["di"], "article.js_watch-teaser", "h2.news-item__heading", "a[href]", "div.article__lead.global-l-bold p", base_url="https://www.di.se")

def scrape_resume():
    return scrape_site("Resume.se", SITES["resume"], "article", "h2", "article a[href]", "div.paywalled p", base_url="https://www.resume.se")

def scrape_techcrunch():
    return scrape_site("TechCrunch", SITES["techcrunch"], "article.post-block", "h2.post-block__title", "a.post-block__title__link", "div.article-content p", base_url="https://techcrunch.com")

def scrape_wired():
    return scrape_site("Wired", SITES["wired"], "div.archive-item-component", "h2.archive-item-component__title", "a.archive-item-component__link", "div.article-body-component p", base_url="https://www.wired.com")

# 9️⃣ Huvudfunktion för att köra allt
def run_scraper():
    all_articles = scrape_di() + scrape_resume() + scrape_techcrunch() + scrape_wired()
    
    # Ladda tidigare artiklar
    previous_articles = load_previous_articles()

    # Filtrera ut endast nya artiklar
    new_articles = [article for article in all_articles if article["link"] not in {a["link"] for a in previous_articles}]

    # Spara nya artiklar i articles.json
    save_new_articles(new_articles)

    # Uppdatera previous_articles.json med alla artiklar
    save_previous_articles(previous_articles + new_articles)

# 🔟 Kör skraparen
if __name__ == "__main__":
    run_scraper()
