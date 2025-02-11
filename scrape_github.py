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

# 1️⃣ Definiera fil-URL:er på GitHub
GITHUB_RAW_ARTICLES = "https://raw.githubusercontent.com/900722/ai-articles/refs/heads/main/articles.json"
GITHUB_RAW_PREVIOUS = "https://raw.githubusercontent.com/900722/ai-articles/refs/heads/main/previous_articles.json"

# 2️⃣ Funktion för att ladda `previous_articles.json` eller skapa filen om den saknas
def load_previous_articles():
    if not os.path.exists("previous_articles.json"):
        print("⚠️ previous_articles.json saknas. Skapar en tom fil...")
        with open("previous_articles.json", "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=4)

    try:
        with open("previous_articles.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print("❌ Fel vid läsning av previous_articles.json. Återställer filen...")
        with open("previous_articles.json", "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=4)
        return []

# 3️⃣ Funktion för att spara previous_articles.json utan att ta bort gamla artiklar
def save_previous_articles(new_articles):
    if not os.path.exists("previous_articles.json"):
        print("⚠️ previous_articles.json saknas. Skapar en ny...")
        with open("previous_articles.json", "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=4)

    try:
        with open("previous_articles.json", "r", encoding="utf-8") as f:
            previous_articles = json.load(f)
    except json.JSONDecodeError:
        print("❌ previous_articles.json var korrupt. Återställer filen...")
        previous_articles = []

    all_articles = previous_articles + new_articles
    unique_articles = {article["link"]: article for article in all_articles}

    with open("previous_articles.json", "w", encoding="utf-8") as f:
        json.dump(list(unique_articles.values()), f, ensure_ascii=False, indent=4)

    print(f"✅ Uppdaterade previous_articles.json med {len(unique_articles)} artiklar totalt.")

# 4️⃣ Funktion för att spara endast nya artiklar i articles.json
def save_new_articles(new_articles):
    if not new_articles:
        new_articles = [{
            "title": "No content available",
            "link": "No content available",
            "date": "No content available",
            "source": "No content available",
            "text": "No content available"
        }]

    with open("articles.json", "w", encoding="utf-8") as f:
        json.dump(new_articles, f, ensure_ascii=False, indent=4)
    print(f"✅ {len(new_articles)} nya artiklar sparade i articles.json.")

# 5️⃣ Skrapfunktion och sajter
SITES = {
    "di": "https://www.di.se/amnen/artificiell-intelligens/",
    "resume": "https://www.resume.se/om/artificiell-intelligens-ai/",
    "techcrunch": "https://techcrunch.com/tag/artificial-intelligence/",
    "wired": "https://www.wired.com/tag/artificial-intelligence/"
}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

session = requests.Session()

def scrape_site(site_name, url, article_selector, title_selector, link_selector, text_selector, base_url=""):
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
            source_domain = urlparse(full_link).netloc.replace("www.", "")

            text = " ".join([p.get_text(strip=True) for p in article.select(text_selector)]) if text_selector else "No content available"

            if any(prev["link"] == full_link for prev in previous_articles):
                print(f"⚠️ Skipping redan skrapad artikel: {title}")
                continue  

            print(f"🔍 Hittad ny artikel: {title} ({full_link}) från {source_domain}")

            articles.append({
                "title": title,
                "link": full_link,
                "date": datetime.now(timezone.utc).isoformat(),
                "source": source_domain,
                "text": text
            })

            time.sleep(random.uniform(3, 6))

        except Exception as e:
            print(f"❌ Fel vid skrapning av artikel: {e}")

    print(f"✅ Hittade {len(articles)} nya artiklar från {site_name}!")
    return articles

# 6️⃣ Skrapa och hantera data
def run_scraper():
    all_articles = (
        scrape_site("DI.se", SITES["di"], "article.js_watch-teaser", "h2.news-item__heading", "a[href]", "div.article__lead.global-l-bold, div.article__lead.global-l-bold p", base_url="https://www.di.se") +
        scrape_site("Resume.se", SITES["resume"], "article", "h2", "article a[href]", "div.paywalled p", base_url="https://www.resume.se") +
        scrape_site("TechCrunch", SITES["techcrunch"], "article.post-block", "h2.post-block__title", "a.post-block__title__link", "div.article-content p", base_url="https://techcrunch.com") +
        scrape_site("Wired", SITES["wired"], "div.archive-item-component", "h2.archive-item-component__title", "a.archive-item-component__link", "div.article-body-component p", base_url="https://www.wired.com")
    )

    previous_articles = load_previous_articles()
    new_articles = [article for article in all_articles if article["link"] not in {a["link"] for a in previous_articles}]
    save_new_articles(new_articles)
    save_previous_articles(new_articles)

# 7️⃣ Commit och push via SSH
def commit_and_push_files():
    try:
        # Konfigurera användaridentitet för Git
        subprocess.run(["git", "config", "--global", "user.email", "lisa@maniola.se"], check=True)
        subprocess.run(["git", "config", "--global", "user.name", "900722"], check=True)

        # Kontrollera om det finns ändringar
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if not status.stdout.strip():
            print("✅ Inga ändringar att commit:a. Skippar push.")
            return

        # Lägg till och commit:a filer
        subprocess.run(["git", "add", "articles.json", "previous_articles.json"], check=True)
        subprocess.run(["git", "commit", "-m", "🔄 Automatiskt uppdaterade artiklar"], check=True)

        # Pusha via SSH
        subprocess.run(["git", "push"], check=True)

        print("✅ Filerna har laddats upp till GitHub via SSH!")

    except subprocess.CalledProcessError as e:
        print(f"❌ Fel vid commit eller push: {e}")

if __name__ == "__main__":
    run_scraper()
    commit_and_push_files()
