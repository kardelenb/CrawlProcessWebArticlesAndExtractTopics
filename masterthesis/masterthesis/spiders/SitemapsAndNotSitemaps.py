import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from pymongo import MongoClient
from urllib.parse import urlparse
from urllib.parse import urljoin
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

# Funktion zum Abrufen von Artikel-Links auf einer Seite mit Selenium
def get_article_links_from_page_with_selenium(base_url):
    # Selenium WebDriver einrichten
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get(base_url)
        time.sleep(3)  # Warte, bis die Seite vollständig geladen ist

        # Extrahiere den Seitenquellcode
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # Extrahiere die Domain der Basis-URL
        base_domain = urlparse(base_url).netloc

        # Suche nach Links auf der Seite
        links = []
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']

            # Verarbeite relative Links (beginnen mit '/')
            if href.startswith('/'):
                full_url = urljoin(base_url, href)  # Wandelt relative in absolute URLs um
                links.append(full_url)

            # Verarbeite Protokoll-relative Links (beginnen mit '//')
            elif href.startswith('//'):
                full_url = urljoin(base_url, href)
                links.append(full_url)

            # Verarbeite absolute URLs
            elif href.startswith('http'):
                links.append(href)

        return list(set(links))  # Entferne Duplikate

    except Exception as e:
        logging.error(f"Fehler beim Abrufen der Seite mit Selenium: {base_url} - {e}")
        return []

    finally:
        driver.quit()
# Prüft, ob der Link zu einem Artikel führt
def is_article_link(url, base_url):
    # Wir verwenden hier einfach die Prüfung, ob die URL zur Basisdomain gehört
    base_domain = urlparse(base_url).netloc
    link_domain = urlparse(url).netloc
    return base_domain == link_domain

# Funktion zur Extraktion von Artikelinhalten mit Selenium
def extract_article_content_with_selenium(article_url):
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get(article_url)
        time.sleep(3)

        # Extrahiere den Seitenquellcode
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # Extrahiere den Titel
        title_tag = soup.find('title') or soup.find('h1')
        title = title_tag.get_text(strip=True) if title_tag else "Kein Titel"

        # Extrahiere den Text aus <p>, <li>, <h2>, <h3>, <div> und ähnlichen relevanten Tags
        text_elements = soup.find_all(['p', 'li'])
        full_text = ' '.join(element.get_text(separator=' ', strip=True) for element in text_elements)

        # Bereinige den Text von überflüssigen Leerzeichen
        full_text = ' '.join(full_text.split())

        return {
            'title': title,
            'full_text': full_text
        }
    except Exception as e:
        logging.error(f"Fehler beim Abrufen des Artikels mit Selenium: {article_url} - {e}")
        return None
    finally:
        driver.quit()
# Funktion zur Rekursion und zum Crawlen der Webseite
def crawl_website_with_selenium(base_url, visited_urls, processed_urls, max_depth=3):
    if max_depth == 0:
        return

    # Artikel-Links von der Seite holen
    all_links = get_article_links_from_page_with_selenium(base_url)

    for link in all_links:
        # Überspringe bereits besuchte Seiten oder Links, die nicht zur Basis-URL gehören
        if link in visited_urls or link in processed_urls or not is_article_link(link, base_url):
            continue

        visited_urls.add(link)

        # Prüfen, ob der Link zu einem Artikel führt
        if is_article_link(link, base_url):
            logging.info(f"Artikel gefunden: {link}")
            article_content = extract_article_content_with_selenium(link)
            if article_content:
                logging.info(f"Titel: {article_content['title']}")
                logging.info(f"Text: {article_content['full_text'][:1800]}...")  # Ausgabe der ersten 1800 Zeichen

                # Füge die URL zu processed_urls hinzu
                processed_urls.add(link)

                # Speichere den Artikel in der Datenbank
                collection.insert_one({
                    'title': article_content['title'],
                    'url': link,
                    'full_text': article_content['full_text'],
                    'comments': []  # Hier können Kommentare eingefügt werden, falls vorhanden
                })

        # Falls es keine Artikel-Seite ist, rekursiv weiter crawlen
        else:
            logging.info(f"Crawlen der Seite: {link}")
            crawl_website_with_selenium(link, visited_urls, processed_urls, max_depth - 1)

        # Wartezeit zwischen den Anfragen, um die Webseite nicht zu überlasten
        time.sleep(1)

# Funktion zur Überprüfung und Auswahl der passenden Methode
def scrape_article(url, processed_urls, sitemap_based=True):
    try:
        # Überprüfe, ob der Artikel bereits gespeichert wurde
        article_exists = url in processed_urls
        stored_comments = get_stored_comments(url) if article_exists else set()

        if sitemap_based:
            response = requests.get(url)
            response.raise_for_status()
            content = extract_content_from_html(response.content)
        else:
            content = extract_article_content_with_selenium(url)

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
        logging.info("Verarbeite Artikel direkt von der Seite ohne Sitemap.")
        visited_urls = set()
        crawl_website_with_selenium(base_url, visited_urls, processed_urls, max_depth=3)

if __name__ == '__main__':
    main()
