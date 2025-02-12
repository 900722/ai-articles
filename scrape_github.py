import json
import requests
from bs4 import BeautifulSoup

# Filnamn
ARTICLES_FILE = "articles_text.json"
PREVIOUS_ARTICLES_FILE = "previous_articles_text.json"

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

def scrape_github_articles():
    """Skrapa artiklar från en GitHub-sida (exempel)"""
    url = "https://github.com/trending"
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"Fel vid hämtning av data: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    
    articles = []
    for repo in soup.find_all("article"):
        title = repo.find("h1").get_text(strip=True) if repo.find("h1") else "Okänd titel"
        link = "https://github.com" + repo.find("a")["href"] if repo.find("a") else ""
        description = repo.find("p").get_text(strip=True) if repo.find("p") else "Ingen beskrivning"

        articles.append({
            "title": title,
            "link": link,
            "description": description
        })
    
    return articles

def update_articles():
    """Uppdatera JSON-filer med nya artiklar och spara historik."""
    
    # Läs in tidigare skrapade artiklar
    previous_articles = load_json_file(PREVIOUS_ARTICLES_FILE)
    previous_titles = {article["title"] for article in previous_articles}
    
    # Skrapa nya artiklar
    new_articles = scrape_github_articles()
    
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
