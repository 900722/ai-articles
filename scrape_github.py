# 📌 Importera nödvändiga bibliotek
import os
import json
import requests
import time
import random
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse
import subprocess

# 🔹 Centraliserad lista över webbplatser att skrapa
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

# 1️⃣ Funktion för att ladda `previous_articles.json` eller skapa filen om den saknas
def load_previous_articles():
    if not os.path.exists("previous_articles.json"):
        print("⚠️ previous_articles.json saknas. Skapar en tom fil...")
        with open("previous_articles.json", "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=4)

    try:
        with open("previous_articles.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print("❌ previous_articles.json var korrupt. Återställer filen...")
        with open("previous_articles.json", "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=4)
        return []

# 2️⃣ Funktion för att spara previous_articles.json utan att ta bort gamla artiklar
def save_previous_articles(new_articles):
    previous_articles = load_previous_articles()
    all_articles = previous_articles + new_articles
    unique_articles = {article["link"]: article for article in all_articles}

    with open("previous_articles.json", "w", encoding="utf-8") as f:
        json.dump(list(unique_articles.values()), f, ensure_ascii=False, indent=4)

    # 🔹 Uppdatera filens timestamp så att Git ser ändringen
    os.utime("previous_articles.json", None)
    print(f"✅ Uppdaterade previous_articles.json med {len(unique_articles)} artiklar totalt.")

# 3️⃣ Funktion för att spara senaste skrapade artiklar i articles.json
def save_new_articles(new_articles):
    with open("articles.json", "w", encoding="utf-8") as f:
        json.dump(new_articles, f, ensure_ascii=False, indent=4)

    # 🔹 Uppdatera filens timestamp så att Git ser ändringen
    os.utime("articles.json", None)
    print(f"✅ {len(new_articles)} nya artiklar sparade i articles.json.")

# 4️⃣ Funktion för att skrapa enskilda webbplatser
def scrape_site(site):
    print(f"🚀 Hämtar artiklar från {site['name']}...")

    headers = {"User-Agent": random.choice([
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ])}

    try:
        response = requests.get(site["url"], headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"❌ Misslyckades att hämta {site['name']}. Statuskod: {response.status_code}")
            return []
    except requests.RequestException as e:
        print(f"❌ Fel vid hämtning av {site['name']}: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    previous_articles = load_previous_articles()
    articles = []

    for article in soup.select(site["article_selector"]):
        title_tag = article.select_one(site["title_selector"])
        link_tag = article.select_one(site["link_selector"])

        title = title_tag.text.strip() if title_tag else "No title available"
        link = urljoin(site["base_url"], link_tag["href"]) if link_tag and "href" in link_tag.attrs else "No link available"
        text = " ".join([p.get_text(strip=True) for p in article.select(site["text_selector"])]) if site["text_selector"] else "No text available"

        if any(prev["link"] == link for prev in previous_articles):
            print(f"⚠️ Skipping redan skrapad artikel: {title}")
            continue  

        print(f"🔍 Hittad ny artikel: {title} ({link})")

        articles.append({
            "title": title,
            "link": link,
            "date": datetime.now(timezone.utc).isoformat(),
            "source": urlparse(link).netloc.replace("www.", ""),
            "text": text
        })

        time.sleep(random.uniform(3, 6))  # Simulera mänskligt beteende

    print(f"✅ Hittade {len(articles)} nya artiklar från {site['name']}!")
    return articles

# 5️⃣ Kör skrapningen
def run_scraper():
    all_articles = []
    for site in SITES:
        all_articles.extend(scrape_site(site))

    previous_articles = load_previous_articles()
    new_articles = [a for a in all_articles if a["link"] not in {p["link"] for p in previous_articles}]

    save_new_articles(new_articles)
    save_previous_articles(new_articles)

# 6️⃣ Hantera Git-commit och push
def commit_and_push_files():
    status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    if not status.stdout.strip():
        print("✅ Inga ändringar att commit:a. Skippar push.")
        return

    subprocess.run(["git", "add", "--force", "articles.json", "previous_articles.json"], check=True)
    subprocess.run(["git", "commit", "-m", "🔄 Automatiskt uppdaterade artiklar"], check=True)
    subprocess.run(["git", "push"], check=True)

    print("✅ Filerna har laddats upp till GitHub via SSH!")

# 7️⃣ Kör skrapning och Git-push
if __name__ == "__main__":
    run_scraper()
    commit_and_push_files()
