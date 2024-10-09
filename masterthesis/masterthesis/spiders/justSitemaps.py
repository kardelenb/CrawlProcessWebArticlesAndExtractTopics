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
collection = db['luxemburg_raw']

# Lädt alle bereits verarbeiteten URLs aus der MongoDB in ein Set
def load_processed_urls(base_url):
    # Lade nur die URLs, die zur aktuellen Seite gehören (basierend auf der base_url)
    return set(doc['url'] for doc in collection.find({'url': {'$regex': f'^{base_url}'}}, {'url': 1}))


# Funktion zum Abrufen von bereits gespeicherten Kommentaren für eine URL
def get_stored_comments(url):
    article = collection.find_one({'url': url}, {'comments': 1})
    if article:
        return set(article.get('comments', []))
    return set()
# Prüft, ob eine Sitemap vorhanden ist, und sucht nach Sitemaps wie 'post-sitemap' oder 'sitemap.xml'
def get_all_sitemap_links(base_url):
    if "zeitschrift-luxemburg" in base_url:
        # Für zeitschrift-luxemburg.de direkt die Haupt-Sitemap verwenden
        return [f"{base_url}/sitemap.xml"]

    possible_sitemaps = [
        f"{base_url}/sitemap.xml",
        f"{base_url}/wp-sitemap.xml",
        f"{base_url}/sitemap_index.xml"
    ]

    sitemap_links = []
    for sitemap_url in possible_sitemaps:
        try:
            response = requests.get(sitemap_url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'xml')
                # Finde alle <loc>-Tags (in XML sind das die Links zu weiteren Sitemaps oder Artikeln)
                loc_tags = soup.find_all('loc')
                for loc in loc_tags:
                    sitemap_links.append(loc.text)
            else:
                logging.warning(f"Sitemap nicht gefunden: {sitemap_url}")
        except requests.RequestException as e:
            logging.error(f"Fehler beim Abrufen der Sitemap: {sitemap_url} - {e}")

    # Filter: Nur Sitemaps verarbeiten, die 'posts-post' oder 'post-sitemap' im Link haben
    filtered_sitemap_links = [
        link for link in sitemap_links
        if 'posts-post' in link or 'post-sitemap' in link
    ]

    # Dedupliziere die Sitemap-Links, damit jeder Link nur einmal verarbeitet wird
    return list(set(filtered_sitemap_links))  # Verwende ein Set, um Duplikate zu entfernen

# Funktion zum Abrufen der Artikel-URLs von der Sitemap
def get_urls_from_sitemap(sitemap_url):
    try:
        response = requests.get(sitemap_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'xml')

        # Finde alle Artikel-URLs in den Sitemaps
        urls = [url_loc.text for url_loc in soup.find_all('loc')]

        # Liste der Dateitypen, die wir ausschließen möchten
        excluded_file_types = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.pdf', '.doc', '.docx', '.mp3', '.mp4', '.webp']

        # Filtern: Nur URLs zulassen, die nicht auf Dateien wie Bilder, Videos oder Dokumente verweisen
        filtered_urls = [url for url in urls if not any(url.lower().endswith(ext) for ext in excluded_file_types)]

        return filtered_urls
    except requests.RequestException as e:
        logging.error(f"Sitemap konnte nicht abgerufen werden: {sitemap_url} aufgrund von {e}")
        return []

# Funktion zur Extraktion von Titel, Text und Kommentaren aus HTML für die Webseiten mit Sitemaps
def extract_content_from_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extrahiere den Titel
    title = soup.find('title') or soup.find('h1') or soup.find('meta', property='og:title')
    title_text = title.get_text(strip=True) if title else "No Title"

    # Zuerst alle Kommentare extrahieren
    comments = []
    possible_comment_sections = soup.find_all(['div', 'section', 'article'],
                                              class_=lambda x: x and 'comment' in x.lower())

    for section in possible_comment_sections:
        comment_paragraphs = section.find_all('p')
        for p in comment_paragraphs:
            comment_text = p.get_text(separator=' ', strip=True)
            if comment_text:
                comments.append(html.unescape(comment_text))

        # Entferne den Kommentarbereich aus dem HTML, um doppelte Einträge zu vermeiden
        section.decompose()

    # Extrahiere den Text aus dem bereinigten HTML (nach dem Entfernen der Kommentare)
    article = soup.find('article') or soup.find('div', class_="postcontent") or soup.find('div', class_="singlepost") or soup.find('div', class_="article-text")


    if article:
        paragraphs = article.find_all('p')
        list_items = article.find_all('li')
    else:
        # Fallback, wenn kein spezifischer Container gefunden wird
        paragraphs = soup.find_all('p')
        list_items = soup.find_all('li')

    # Füge den gesamten Text zusammen, aus Paragraphen und Listen
    full_text = ' '.join(html.unescape(tag.get_text(separator=' ', strip=True)) for tag in paragraphs + list_items)
    full_text = full_text.replace('\u00AD', '').replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    full_text = ' '.join(full_text.split())

    return {
        "title": title_text,
        "full_text": full_text,
        "comments": comments
    }
# Funktion zum Scraping eines Artikels
def scrape_article(url, processed_urls, sitemap_based=True):
    try:
        # Überprüfe, ob der Artikel bereits gespeichert wurde
        article_exists = url in processed_urls
        stored_comments = get_stored_comments(url) if article_exists else set()

        if sitemap_based:
            response = requests.get(url)
            response.raise_for_status()
            content = extract_content_from_html(response.content)

        if content:
            title_text = content['title']
            full_text = content['full_text']
            comments = content['comments']

            # Neue Kommentare identifizieren
            new_comments = [comment for comment in comments if comment not in stored_comments]

            if new_comments:
                # Wenn es neue Kommentare gibt, aktualisieren wir nur die Kommentare
                collection.update_one(
                    {'url': url},
                    {'$addToSet': {'comments': {'$each': new_comments}}},
                )
                logging.info(f"Artikel aktualisiert: {url}, neue Kommentare: {len(new_comments)}")

            if not article_exists:
                # Wenn der Artikel noch nicht existiert, speichern wir den gesamten Artikel
                collection.insert_one({
                    'title': title_text,
                    'url': url,
                    'full_text': full_text,
                    'comments': comments
                })
                logging.info(f"Artikel erfolgreich gespeichert: {url}")

            # Füge die URL zur processed_urls hinzu, nachdem sie erfolgreich gespeichert wurde
            processed_urls.add(url)

    except requests.RequestException as e:
        logging.error(f"Artikel konnte nicht gescraped werden: {url} aufgrund von {str(e)}")

# Hauptfunktion zum Finden und Scrapen von Artikeln
def main():
    base_url = input("Gib die Basis-URL der Webseite ein (z.B. https://example.com): ").strip()

    # Lade die bereits verarbeiteten URLs
    processed_urls = load_processed_urls(base_url)

    # Prüfe, ob die Webseite eine Sitemap hat
    sitemap_links = get_all_sitemap_links(base_url)

    if sitemap_links:
        logging.info("Verarbeite Artikel von Sitemaps.")
        all_urls = []
        for sitemap_url in sitemap_links:
            all_urls.extend(get_urls_from_sitemap(sitemap_url))

        new_urls = [url for url in all_urls if url not in processed_urls]
        # Scrape die Artikel von URLs, die aus der Sitemap extrahiert wurden
        for url in new_urls:
            scrape_article(url, processed_urls, sitemap_based=True)
            time.sleep(1)
    else:
        logging.error(f"Keine Sitemaps gefunden für: {base_url}")

if __name__ == '__main__':
    main()
