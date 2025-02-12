import json
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse
import time

# Filnamn
ARTICLES_FILE = "articles_text.json"
PREVIOUS_ARTICLES_FILE = "previous_articles_text.json"

# Headers för att simulera en webbläsare
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Cookies från DevTools för Resume.se
RESUME_COOKIES = {
    "jwt": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6InBldHJvbmVsbGEuYmFydmFldXNAZ21haWwuY29tIiwiZ2l2ZW5fbmFtZSI6IlBldHJvbmVsbGEiLCJmYW1pbHlfbmFtZSI6IkJhcnZhZXVzIiwidmVyaWZpZWRFbWFpbCI6dHJ1ZSwiZW50aXRsZWQiOnRydWUsInBsdXNBbGx0Ijp0cnVlLCJoYXNoZWRVc2VySWQiOiI5NTE2MjhkZGViYjg5NzVmYjdlNTAwNWFkZWVkZDIyYjhmMjM1NDQxOTAxYjAyNGZlNThjYThkOWQ2MTlkMTI5IiwiaWF0IjoxNzM5MzgzODI3LCJpc3MiOiJyZXN1bWUiLCJzdWIiOiJiYm0tcmVzOi8vMDA1MjAxYTMtMzAyYS00MDc2LTllMmEtYjU4MDk4ZWQ4NzVhIn0.b0bCGvZun4hk3yIwQbOfDS2Rs-yaVQextcbU6C3TkmM9rMldfrZmGk6j269yacTBOKhvquprn1DZ5AYV7go55EKlcSrG9M1CMsB4Qvj-gtWPTMSovlya5TFGVPAsVnqF_yer-LhZkBx68r1OBfdNiYJ74tnHpp4dxbHUHayaZAFla7GNqOkwsKd--j06QJGMZS8cCGb4puOnc0M35gBYyeIQG0z0r4bDCinzKbFNDxMFC9D_eEXeNUMmpURS9fKwGnkKKXVlcQVCiNmcgee7pRCvF-_04b2mVCgjPjdN1VHRqxGNRNZ-VUUXat2zlDH4A6qdw0CPcW5Nsx1i25ZHfcoW5AxAnoKnNYWwywwXjOS-kEo9xz4d4QiD90Whu0k6b9A0ThgCnvHxYHN3MRxqC_UJk7ZhM6QnvehO9mZVyCJQl6qnQI1MLCvdvIivP73XCo4TaIjZS5BISz-Q_b_fZADteTYRrrUvD01JYyeQ3IDn_mL5ZdcXCKvSstPPvRHgV_xc6_AU2-JnuAGhtNG0_C4lCm4pCTP70jSKm5uw0XxjstNULCzg320PMrrz64I7dVK6p8ZUorZdvPvETlr4MhqsLCzcezculat-wiis4J0qQL0_bTQwL16TNDTf8XeMET9R3mtUSFK7XC3dHoAUzcbB_WwsPPwrCs0HwFmVpuo",
    "tapet-paywall-session": "s%3AmfB2XE9dhuJhz3Ny8msq3Ofj-e8Y8nNg.f%2BbLNV6cPfSHBs5X4t3KF8bwKhUICEzjDdqVz8eLbYk"
}

# URL till Resume.se:s AI-nyheter
RESUME_NEWS_URL = "https://www.resume.se/om/artificiell-intelligens-ai/"

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
        "name": "Breakit",
        "url": "https://www.breakit.se/tag/ai",
        "article_selector": "article.teaser",
        "title_selector": "h2.teaser__heading",
        "link_selector": "a.teaser__link",
        "text_selector": "div.article__body p",
        "base_url": "https://www.breakit.se"
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
        "text_selector": "div.body__inner-container p",
        "base_url": "https://www.wired.com"
    }
]

def get_resume_article_links():
    """Hämta alla artikel-länkar från Resume.se:s AI-sektion."""
    response = requests.get(RESUME_NEWS_URL, headers=HEADERS)

    if response.status_code != 200:
        print(f"❌ Misslyckades att hämta Resume.se: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    # 🔍 Hitta alla artikellänkar
    article_links = []
    for article in soup.select("article a[href]"):
        link = urljoin("https://www.resume.se", article["href"])
        article_links.append(link)

    print(f"✅ Hittade {len(article_links)} artiklar på Resume.se")
    return article_links

def scrape_resume_articles():
    """Skrapa nya Resume.se-artiklar dynamiskt och hämta brödtext med Selenium."""
    
    # Hämta alla artikel-länkar från Resume.se
    article_urls = get_resume_article_links()

    # Läs in tidigare skrapade artiklar
    previous_articles = load_json_file(PREVIOUS_ARTICLES_FILE)
    previous_titles = {article["title"] for article in previous_articles}

    articles = []

    # Konfigurera Selenium WebDriver
    options = Options()
    options.add_argument("--headless")  # Kör utan att öppna fönster
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument(f"user-agent={HEADERS['User-Agent']}")

    from selenium.webdriver.chrome.service import Service

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    chrome_service = Service("/usr/bin/chromedriver")  # ✅ Anger rätt sökväg
    driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

    for url in article_urls:
        driver.get(url)
        time.sleep(5)  # Vänta på att sidan ska ladda

        # 🔍 Hämta titel
        try:
            title_tag = driver.find_element(By.CSS_SELECTOR, "meta[property='og:title']")
            title = title_tag.get_attribute("content") if title_tag else "Okänd titel"
        except:
            title = "Okänd titel"

        # Skippa artiklar vi redan har
        if title in previous_titles:
            print(f"🔄 Artikel redan skrapad: {title}")
            continue

        # 🔍 Hämta brödtext från div.paywalled p
        try:
            paragraphs = driver.find_elements(By.CSS_SELECTOR, "div.paywalled p")
            text = " ".join([p.text.strip() for p in paragraphs]) if paragraphs else "Ingen brödtext tillgänglig"
        except:
            text = "Ingen brödtext tillgänglig"

        articles.append({
            "title": title,
            "text": text,
            "link": url,
            "date": datetime.now(timezone.utc).isoformat(),
            "source": "resume.se"
        })
        print(f"✅ Artikel hämtad: {title}")

    driver.quit()
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

def load_json_file(filename):
    """Ladda en JSON-fil om den finns, annars returnera en tom lista."""
    try:
        with open(filename, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []  # Om filen saknas, returnera en tom lista

def save_json_file(filename, data):
    """Spara data i en JSON-fil."""
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

def update_articles():
    """Uppdatera JSON-filer med nya artiklar och spara historik."""
    
    previous_articles = load_json_file(PREVIOUS_ARTICLES_FILE)
    previous_titles = {article["title"] for article in previous_articles}

    # 🔹 Skrapa Resume.se dynamiskt
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

if __name__ == "__main__":
    update_articles()
