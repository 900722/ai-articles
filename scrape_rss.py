import feedparser
import json
import os
from datetime import datetime

# Lista med RSS-feeds
RSS_FEEDS = {
    "Resume": "https://www.resume.se/rss.xml",
    "TechCrunch": "https://techcrunch.com/feed/",
    "Wired AI": "https://www.wired.com/feed/tag/ai/latest/rss",
    "The Verge": "https://www.theverge.com/rss/index.xml",
    "Reddit Technology": "https://www.reddit.com/r/technology/.rss",
    "OpenAI News": "https://openai.com/news/rss.xml",
    "Google Gemini Blog": "https://blog.google/products/gemini/rss/",
    "Harvard Business Review": "http://feeds.harvardbusiness.org/harvardbusiness"
}

DATA_FILE = "articles_rss.json"  # Fil där alla nyheter sparas


def fetch_rss(feed_url):
    """ Hämtar och parsar RSS-flödet """
    try:
        feed = feedparser.parse(feed_url)
        if not feed.entries:
            print(f"[VARNING] Inga nyheter hittades för: {feed_url}")
        return feed.entries
    except Exception as e:
        print(f"[FEL] Kunde inte hämta RSS från {feed_url}: {e}")
        return []


def scrape_rss():
    """ Skrapar nyheter från alla RSS-källor och returnerar en lista """
    all_news = []
    
    for source, url in RSS_FEEDS.items():
        print(f"Hämtar nyheter från: {source}...")
        entries = fetch_rss(url)
        
        for entry in entries:
            news_item = {
                "Källa": source,
                "Titel": entry.title,
                "Länk": entry.link,
                "Publicerad": entry.published if "published" in entry else "Okänt",
                "Hämtad": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            all_news.append(news_item)
    
    return all_news


def load_existing_news():
    """ Laddar tidigare sparade nyheter från JSON-filen om den finns """
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                print("[VARNING] JSON-filen kunde inte läsas, skapar en ny.")
                return []
    return []


def save_to_json(news_list):
    """ Sparar nyheter i JSON-filen utan att skriva över gamla nyheter """
    existing_news = load_existing_news()

    # Lägg bara till nya nyheter som inte redan finns
    new_articles = [news for news in news_list if news["Länk"] not in {n["Länk"] for n in existing_news}]

    if not new_articles:
        print("[INFO] Inga nya nyheter att lägga till.")
        return

    updated_news = existing_news + new_articles

    with open(DATA_FILE, mode="w", encoding="utf-8") as file:
        json.dump(updated_news, file, indent=4, ensure_ascii=False)
    
    print(f"[INFO] Nyheterna har sparats i {DATA_FILE}")


if __name__ == "__main__":
    news_data = scrape_rss()
    
    # Skriva ut de senaste 5 nyheterna
    for news in news_data[:5]:
        print(f"\n🔹 {news['Titel']}\n🔗 {news['Länk']}\n📅 {news['Publicerad']}")

    # Spara till JSON (utan att skriva över tidigare nyheter)
    save_to_json(news_data)
