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
collection = db['raw_articles5']

# Liste der Sitemap-URLs, die gecrawlt werden sollen
sitemap_urls = [
    #'https://www.der-rechte-rand.de/post-sitemap.xml'
    'https://sezession.de/wp-sitemap-posts-post-1.xml'
    #'https://sezession.de/wp-sitemap-posts-post-2.xml',
    #'https://sezession.de/wp-sitemap-posts-post-3.xml',
    #'https://sezession.de/wp-sitemap-posts-post-4.xml'
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


# Funktion zur Extraktion von Titel, Text und Kommentaren aus HTML
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
    article = soup.find('article') or soup.find('div', class_="postcontent") or soup.find('div', class_="singlepost")

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


# Funktion zum Scrapen des Artikels und zum Speichern in der Datenbank
def scrape_article(url):
    try:
        if collection.find_one({'url': url}):
            logging.info(f"Artikel bereits vorhanden: {url}")
            return

        response = requests.get(url)
        response.raise_for_status()

        content = extract_content_from_html(response.content)
        title_text = content['title']
        full_text = content['full_text']
        comments = content['comments']

        logging.info(f"Extrahierter Titel: {title_text}")
        logging.info(f"Anzahl der Kommentare: {len(comments)}")
        if not full_text.strip():
            logging.warning(f"Kein Text extrahiert für URL: {url}")
        else:
            logging.info(f"Extrahierter Text: {full_text[:500]}...")

        collection.insert_one({
            'title': title_text,
            'url': url,
            'full_text': full_text,
            'comments': comments
        })

        logging.info(f"Artikel erfolgreich gespeichert: {url}")

    except requests.RequestException as e:
        logging.error(f"Failed to scrape {url}: {e}")


# Hauptfunktion
def main():
    all_urls = []
    for sitemap_url in sitemap_urls:
        all_urls.extend(get_urls_from_sitemap(sitemap_url))

    for url in all_urls:
        scrape_article(url)
        time.sleep(1)


if __name__ == '__main__':
    main()
