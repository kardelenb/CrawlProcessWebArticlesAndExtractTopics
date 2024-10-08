import requests
from bs4 import BeautifulSoup
import logging
import time

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Funktion zum Abrufen der Artikel-URLs von der Sitemap
def get_urls_from_sitemap(sitemap_url):
    try:
        logging.info(f"Abrufen der Sitemap: {sitemap_url}")
        response = requests.get(sitemap_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'xml')

        # Finde alle Artikel-URLs in den Sitemaps (loc-Tags)
        urls = [url_loc.text for url_loc in soup.find_all('loc')]

        # Liste der Dateitypen, die wir ausschließen möchten
        excluded_file_types = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.pdf', '.doc', '.docx', '.mp3', '.mp4', '.webp']

        # Filtern: Nur URLs zulassen, die nicht auf Dateien wie Bilder, Videos oder Dokumente verweisen
        filtered_urls = [url for url in urls if not any(url.lower().endswith(ext) for ext in excluded_file_types)]
        logging.info(f"{len(filtered_urls)} Artikel-URLs in der Sitemap gefunden.")

        return filtered_urls
    except requests.RequestException as e:
        logging.error(f"Sitemap konnte nicht abgerufen werden: {sitemap_url} aufgrund von {e}")
        return []

# Funktion zur Extraktion von Titeln aus einer Artikel-URL
def extract_title_from_article(article_url):
    try:
        logging.info(f"Extrahiere Titel von: {article_url}")
        response = requests.get(article_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extrahiere den Titel des Artikels
        title = soup.find('title') or soup.find('h1') or soup.find('meta', property='og:title')
        title_text = title.get_text(strip=True) if title else "Kein Titel gefunden"
        return title_text
    except requests.RequestException as e:
        logging.error(f"Fehler beim Abrufen des Artikels: {article_url} - {e}")
        return None

# Hauptfunktion zum Abrufen der URLs von der Sitemap und Extrahieren der Titel
def main():
    sitemap_url = input("Gib die Sitemap-URL ein (z.B. https://example.com/sitemap.xml): ").strip()

    # Abrufen der URLs aus der Sitemap
    article_urls = get_urls_from_sitemap(sitemap_url)

    # Extrahiere Titel von den gefundenen Artikel-URLs
    for url in article_urls:
        title = extract_title_from_article(url)
        if title:
            logging.info(f"Artikel: {url}")
            logging.info(f"Titel: {title}")
        time.sleep(1)  # Wartezeit zwischen Anfragen, um die Webseite nicht zu überlasten

if __name__ == '__main__':
    main()
