import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
import html
import time
import logging

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Verbindung zu MongoDB einrichten
client = MongoClient('mongodb://localhost:27017/')
db = client['scrapy_database']
collection = db['raw_articles']  # Neue Collection für die rohen Artikel

# Liste der Sitemap-URLs, die gecrawlt werden sollen
sitemap_urls = [
    'https://sezession.de/wp-sitemap-posts-post-1.xml',
    'https://sezession.de/wp-sitemap-posts-post-2.xml',
    'https://sezession.de/wp-sitemap-posts-post-3.xml',
    'https://sezession.de/wp-sitemap-posts-post-4.xml'
]

# Funktion zum Abrufen der URLs von der Sitemap
def get_urls_from_sitemap(sitemap_url):
    try:
        response = requests.get(sitemap_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'xml')
        urls = [url_loc.text for url_loc in soup.find_all('loc')]
        return urls
    except requests.RequestException as e:
        logging.error(f"Failed to fetch sitemap: {sitemap_url} due to {e}")
        return []

# Funktion zum Scrapen des Artikels
def scrape_article(url):
    try:
        # Überprüfe, ob der Artikel bereits in der Datenbank existiert
        if collection.find_one({'url': url}):
            logging.info(f"Artikel bereits vorhanden: {url}")
            return  # Überspringe, wenn der Artikel bereits existiert

        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Entfernen der spezifischen <div>-Elemente
        for div in soup.select("div.sez-single-author-description"):
            div.decompose()  # Entfernt das gesamte div-Element und seinen Inhalt

        # Titel des Artikels extrahieren
        title = soup.select_one(".sez-post-title") or soup.select_one(".sez-single-post-title")
        title_text = title.get_text(strip=True) if title else "No Title"

        # Paragraphen und Listenelemente extrahieren und filtern
        paragraphs = soup.select(
            "p:not(#sez-donation-txt):not(#sez-donation-bank):not(.sez-socials-shariff p):not(nav p):not(#sez-comment-form p)"
        )
        list_items = soup.select(
            "li:not(#sez-donation-txt):not(#sez-donation-bank):not(.sez-socials-shariff li):not(nav li):not(#sez-comment-form li)"
        )

        # Alle relevanten Texte zusammenführen
        full_text = ' '.join(html.unescape(text.get_text(separator=' ', strip=True)) for text in paragraphs + list_items)
        full_text = full_text.replace('\u00AD', '').replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        full_text = ' '.join(full_text.split())

        # In MongoDB speichern
        collection.insert_one({
            'title': title_text,
            'url': url,
            'full_text': full_text
        })

        logging.info(f"Artikel erfolgreich gespeichert: {url}")

    except requests.RequestException as e:
        logging.error(f"Failed to scrape {url}: {e}")

# Hauptfunktion
def main():
    all_urls = []

    # URLs von jeder Sitemap abrufen
    for sitemap_url in sitemap_urls:
        all_urls.extend(get_urls_from_sitemap(sitemap_url))

    # Durch die URLs iterieren und jeden Artikel scrapen
    for url in all_urls:
        scrape_article(url)
        time.sleep(1)  # Wartezeit zwischen Anfragen, um Blockierungen zu vermeiden

if __name__ == '__main__':
    main()
