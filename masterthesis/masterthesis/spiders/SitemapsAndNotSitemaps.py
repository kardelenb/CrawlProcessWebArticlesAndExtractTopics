import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from pymongo import MongoClient
import html
import time
import logging

# Logging konfigurieren
logging.basicConfig(level=logging.ERROR, format='%(asctime=s - %(levelname)s - %(message)s')

# Verbindung zu MongoDB einrichten
client = MongoClient('mongodb://localhost:27017/')
db = client['scrapy_database']
collection = db['rechterand0510raw']

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

# Funktion zum Abrufen von Artikel-Links auf einer Seite mit Selenium
def get_article_links_from_page_with_selenium(base_url):
    # Selenium WebDriver einrichten
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Headless-Modus für das unsichtbare Browsen
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=chrome_options)

    try:
        # Lade die Webseite mit Selenium
        driver.get(base_url)
        time.sleep(3)  # Warte, bis die Seite vollständig geladen ist

        # Extrahiere den Seitenquellcode
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # Suche nach <article>-Tags, aber auch nach <div> oder <section> mit typischen Klassen für Artikel
        articles = soup.find_all(['article', 'div', 'section'], class_=lambda x: x and 'post' in x.lower())

        links = []
        # Durchsuche jedes gefundene Element nach Links
        for article in articles:
            link = article.find('a', href=True)
            if link:
                href = link['href']
                if href.startswith('/'):
                    # Baue den vollständigen URL aus relativen Links
                    full_url = requests.compat.urljoin(base_url, href)
                    links.append(full_url)
                elif href.startswith('http'):
                    # Falls der Link absolut ist, direkt hinzufügen
                    links.append(href)

        # Zusätzlich alle Links auf der Seite durchsuchen, falls Artikel-Tags nicht erfolgreich sind
        if not links:
            logging.info("Keine spezifischen Artikel-Container gefunden. Suche nach allgemeinen Links.")
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = link['href']
                if href.startswith('/') or href.startswith('http'):
                    full_url = requests.compat.urljoin(base_url, href)
                    links.append(full_url)

        return list(set(links))  # Duplikate entfernen
    except Exception as e:
        logging.error(f"Fehler beim Abrufen der Seite mit Selenium: {base_url} - {e}")
        return []
    finally:
        # Beende den Selenium WebDriver
        driver.quit()


# Gemeinsame Funktion zur Extraktion von Titel, Text und Kommentaren aus HTML
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

# Funktion zur Extraktion von Inhalten mit Selenium für Webseiten ohne Sitemaps
def get_article_content_with_selenium(article_url):
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=chrome_options)

    try:
        # Lade die Webseite mit Selenium
        driver.get(article_url)
        time.sleep(3)  # Warte, bis die Seite vollständig geladen ist

        # Extrahiere den Seitenquellcode
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # Suche nach möglichen Containern mit Text, z.B. <div>, <article>, <section>
        possible_text_containers = soup.find_all(['div', 'article', 'section'])

        full_text = ""

        for container in possible_text_containers:
            paragraphs = container.find_all('p')
            container_text = ' '.join(html.unescape(p.get_text(separator=' ', strip=True)) for p in paragraphs)

            # Nur relevanten Text hinzufügen (z.B. Textlänge über 100 Zeichen)
            if len(container_text) > 100:
                full_text += container_text + " "

        # Bereinigen des gesamten extrahierten Textes
        full_text = full_text.replace('\u00AD', '').replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        full_text = ' '.join(full_text.split())  # Zusätzliche Whitespace entfernen

        # Extrahiere den Titel
        title = soup.find('title') or soup.find('h1') or soup.find('meta', property='og:title')
        title_text = title.get_text(strip=True) if title else "Kein Titel"

        # Extrahiere Kommentare, falls vorhanden
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

        return {
            "title": title_text,
            "full_text": full_text,
            "comments": comments
        }

    except Exception as e:
        logging.error(f"Fehler beim Abrufen des Artikels mit Selenium: {article_url} - {e}")
        return None
    finally:
        driver.quit()


# Funktion zur Überprüfung und Auswahl der passenden Methode
def scrape_article(url, sitemap_based=True):
    try:
        if collection.find_one({'url': url}):
            logging.info(f"Artikel bereits vorhanden: {url}")
            return

        if sitemap_based:
            # Sitemap-basierte Extraktion
            response = requests.get(url)
            response.raise_for_status()
            content = extract_content_from_html(response.content)
        else:
            # Selenium-basierte Extraktion
            content = get_article_content_with_selenium(url)

        if content:
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
        logging.error(f"Artikel konnte nicht gescraped werden: {url} aufgrund von {str(e)}")

# Hauptfunktion zum Finden und Scrapen von Artikeln
def main():
    base_url = input("Gib die Basis-URL der Webseite ein (z.B. https://example.com): ").strip()

    # Prüfe, ob die Webseite eine Sitemap hat
    sitemap_links = get_all_sitemap_links(base_url)

    if sitemap_links:
        logging.info("Verarbeite Artikel von Sitemaps.")
        all_urls = []
        for sitemap_url in sitemap_links:
            all_urls.extend(get_urls_from_sitemap(sitemap_url))

        # Scrape die Artikel von URLs, die aus der Sitemap extrahiert wurden
        for url in all_urls:
            scrape_article(url, sitemap_based=True)
            time.sleep(1)
    else:
        logging.info("Verarbeite Artikel direkt von der Seite ohne Sitemap.")
        all_urls = get_article_links_from_page_with_selenium(base_url)

        if not all_urls:
            logging.error(f"Keine Artikel-URLs gefunden für: {base_url}")
            return

        # Scrape die Artikel direkt von der Seite ohne Sitemap
        for url in all_urls:
            scrape_article(url, sitemap_based=False)
            time.sleep(1)

if __name__ == '__main__':
    main()
