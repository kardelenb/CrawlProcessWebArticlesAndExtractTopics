from bs4 import BeautifulSoup
from pymongo import MongoClient
import html
import logging
import socket
from urllib.parse import urlparse
from selenium.webdriver.common.by import By  # Used to locate elements by their tag name
import time  # Used for sleep pauses in scrolling
import os  # Used to handle paths
import inspect  # Used to inspect the current script's path
import re  # Regular expressions for cleaning up text
import requests  # For handling HTTP requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Verbindung zu MongoDB einrichten
client = MongoClient('mongodb://localhost:27017/')
db = client['scrapy_database']
collection = db['rechteRand']

def crawl(initial_url):
    def create_webdriver():
        try:
            # Setze die Optionen für den Chrome-Browser
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Headless-Modus für Hintergrundausführung
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")

            driver = webdriver.Chrome(options=chrome_options)

            return driver
        except Exception as e:
            print(f"Error initializing WebDriver: {e}")
            return None

    def get_result_meta(url):
        """
        Retrieves metadata for a given URL, including its IP address and main URL.

        Args:
            url (str): The URL to retrieve metadata for.

        Returns:
            dict: A dictionary containing 'ip' (IP address) and 'main' (main URL).
        """
        try:
            parsed_uri = urlparse(url)  # Parse the URL to extract the hostname
            hostname = parsed_uri.netloc
            ip = socket.gethostbyname(hostname)  # Resolve the IP address for the hostname
        except Exception:
            ip = "-1"  # If an error occurs, set IP to "-1"

        main = f'{parsed_uri.scheme}://{parsed_uri.netloc}/' if parsed_uri.netloc else url  # Construct base URL

        return {"ip": ip, "main": main}

    def get_url_header(url):
        """
        Retrieves the HTTP headers and status code for a given URL.

        Args:
            url (str): The URL to retrieve headers for.

        Returns:
            dict: A dictionary containing 'content_type' and 'status_code'.
        """
        driver = create_webdriver()  # Initialize WebDriver
        if driver is None:
            return {}  # Exit if the WebDriver couldn't be initialized

        try:
            # Get metadata such as main URL for filtering requests
            meta = get_result_meta(url)
            main = meta.get("main", "")

            content_type = ""
            status_code = -1

            try:
                # Perform an HTTP GET request to retrieve the status and headers
                response = requests.get(url, verify=False, timeout=10, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
                })
                status_code = response.status_code

                try:
                    headers = requests.head(url, timeout=3).headers
                    content_type = headers.get('Content-Type', "")
                except Exception:
                    if any(tag in response.text.lower() for tag in ["!doctype html", "/html>"]):
                        content_type = "html"  # Assume HTML if tags are detected

            except Exception:
                import mimetypes
                mt = mimetypes.guess_type(url)  # Guess the content type based on URL
                if mt:
                    content_type = mt[0]

            # If status code is a redirect (302) or forbidden (403), treat it as successful (200)
            if status_code in [302, 403]:
                status_code = 200

            # Check if the WebDriver intercepted any network requests matching the URL
            if status_code not in [200, -1]:
                try:
                    for request in driver.requests:
                        if main in request.url:
                            status_code = request.response.status_code
                            content_type = request.response.headers.get('Content-Type', "")
                            if status_code in [200, 302]:
                                break
                except Exception as e:
                    print(f"Error processing requests: {e}")

            # Fallback handling for missing content type
            if not content_type:
                if "binary" in content_type or "json" in content_type or "plain" in content_type:
                    content_type = "html"  # Assume it's HTML if no clear type
                else:
                    content_type = "error"  # Unknown content type

            return {"content_type": content_type, "status_code": status_code}

        finally:
            driver.quit()  # Close the WebDriver instance

    def infinite_scroll(driver, pause_time=2):
        """
        Simulates scrolling to the bottom of a page multiple times to load dynamic content.

        Args:
            driver: The Selenium WebDriver instance.
            pause_time: Time to wait after each scroll for content to load.
        """
        last_height = driver.execute_script("return document.body.scrollHeight")  # Get initial scroll height

        while True:
            # Scroll to the bottom of the page
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            time.sleep(pause_time)  # Wait for new content to load

            new_height = driver.execute_script("return document.body.scrollHeight")  # Check new scroll height

            if new_height == last_height:  # Stop if no new content was loaded
                break
            last_height = new_height  # Update last height for the next scroll

    def get_text(url):
        """
        Extracts all visible text from a given URL after scrolling to the bottom of the page.

        Args:
            url (str): The URL of the page to extract text from.
        """
        driver = create_webdriver()  # Initialize WebDriver
        if driver is None:
            return  # Exit if WebDriver initialization fails

        try:
            driver.get(url)  # Open the URL in the browser
            infinite_scroll(driver)  # Scroll to load dynamic content

            code = driver.page_source  # Get the full HTML of the page
            soup = BeautifulSoup(code, features="lxml")  # Parse the HTML with BeautifulSoup

            text = soup.get_text()  # Extract visible text
            text = re.sub(r'\n\s*\n', r'\n\n', text.strip(), flags=re.M)  # Clean up whitespace

            print(text)  # Output the extracted text
        finally:
            driver.quit()  # Close the WebDriver instance

    def crawl_url(url, dict_request):
        """
        Crawls the given URL and extracts all 'href' attributes from anchor tags.

        Args:
            url (str): The URL of the webpage to crawl.
            dict_request (dict): A dictionary with URL metadata (status code, content type).

        Returns:
            list: A list of unique URLs (hrefs) extracted from the page.
        """
        driver = create_webdriver()  # Initialize WebDriver
        if driver is None:
            return []  # Return empty list if WebDriver initialization fails

        try:
            driver.get(url)  # Open the URL in the browser
            #time.sleep(10)

            if (dict_request["status_code"] == 200 or dict_request["status_code"] == 302) and "html" in dict_request[
                "content_type"]:
                infinite_scroll(driver)  # Scroll to load dynamic content

                meta = get_result_meta(url)  # Get metadata such as main URL
                main = meta['main'].replace("www.", "")  # Normalize URLs by removing 'www.'
                main_www = meta['main']

                anchor_tags = driver.find_elements(By.TAG_NAME, "a")  # Find all anchor tags

                hrefs = [tag.get_attribute('href') for tag in anchor_tags if
                         tag.get_attribute('href')]  # Get 'href' attributes

                # Process and filter valid URLs
                urls = []
                for href in hrefs:
                    if 'http' not in href:
                        href = main + href  # Handle relative URLs
                    if (
                            main in href or main_www in href) and "javascript:void(0)" not in href and "mailto:" not in href:  # Only include URLs from the main domain
                        urls.append(href)

                return list(dict.fromkeys(urls))  # Remove duplicates by converting list to dict then back to list
            else:
                return []
        except Exception as e:
            print(f"Error crawling URL: {e}")
            return []
        finally:
            driver.quit()  # Close the WebDriver instance

    def crawl_sub_urls(urls, crawled_urls):
        """
        Recursively crawls sub-URLs found on a webpage, avoiding duplicates.

        Args:
            urls (list): A list of URLs to crawl.
            crawled_urls (list): A list of already crawled URLs to avoid duplicates.

        Returns:
            tuple: A tuple containing two lists - new result URLs and updated crawled URLs.
        """
        result_urls = []
        for url in urls:
            if url not in crawled_urls and collection.count_documents({'url': url}, limit=1) == 0:

                try:
                    dict_request = get_url_header(url)  # Get URL metadata

                    if (dict_request["status_code"] == 200 or dict_request["status_code"] == 302) and "html" in \
                            dict_request["content_type"]:
                        print(f"Crawling: {url}")

                        result_urls.append(url)  # Add URL to results

                        new_urls = crawl_url(url, dict_request)  # Crawl the URL and get new URLs

                        crawled_urls.append(url)  # Mark URL as crawled

                        result_urls.extend(new_urls)  # Add new URLs to results

                        #save_crawled_url(url)
                        #time.sleep(10)  # Füge Crawl-Delay von 10 Sekunden hinzu

                except Exception as e:
                    print(f"Error crawling sub-URL {url}: {e}")
                    pass

        return list(dict.fromkeys(result_urls)), list(
            dict.fromkeys(crawled_urls))  # Remove duplicates and return results

    # Define the path for configurations and extensions
    currentdir = os.path.dirname(
        os.path.abspath(inspect.getfile(inspect.currentframe())))  # Get the current script directory
    ext_path = os.path.join(currentdir, "i_care_about_cookies_unpacked")  # Path to the cookie consent extension

    url = []
    url.append(initial_url)

    dict_request = get_url_header(url[0])

    # Level 0 URLs: Just the URLs from the given main URL
    level_0_urls = crawl_url(url[0], dict_request)
    crawled_level_0_urls = [url[0]]  # Store the main URL as already crawled

    # Level 1 URLs: Crawl sub-URLs found on level 0 URLs
    level_1_urls, crawled_level_1_urls = crawl_sub_urls(level_0_urls, crawled_level_0_urls)

    # Level 2 URLs: Crawl sub-URLs found on level 1 URLs
    level_2_urls, crawled_level_2_urls = crawl_sub_urls(level_1_urls, crawled_level_1_urls)

    # Um weitere Ebenen zu scrapen, müssen mehr Level hinzugefügt werden. Dafür am besten einfach die obere Zeile kopieren und die Zahlen jeweils um 1 erhöhnen, z. B.:
    # level_3_urls, crawled_level_3_urls = crawl_sub_urls(level_2_urls, crawled_level_2_urls)

    # Combine all URLs across levels, removing duplicates
    return list(dict.fromkeys(url + level_0_urls + level_1_urls + level_2_urls))


# Lädt alle bereits verarbeiteten URLs aus der MongoDB in ein Set
def load_processed_urls(base_url):
    # Lade nur die URLs, die zur aktuellen Seite gehören (basierend auf der base_url)
    return set(doc['url'] for doc in collection.find({'url': {'$regex': f'^{base_url}'}}, {'url': 1}))

def load_crawled_urls(base_url):
    # Lade alle URLs, die bereits verarbeitet wurden, aus der 'test'-Kollektion
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

    if "blauenarzisse" in base_url:
        # Für blauenarzisse.de direkt die Haupt-Sitemap verwenden
        return [f"{base_url}/sitemap-1.xml"]

    if "antifainfoblatt" in base_url:
        # Spezielle Behandlung für antifainfoblatt.de: Nur die Sitemaps für Seite 1 und Seite 2 verwenden
        return [
            f"{base_url}/sitemap.xml?page=1",
            f"{base_url}/sitemap.xml?page=2"
        ]

    possible_sitemaps = [
        f"{base_url}/sitemap.xml",
        f"{base_url}/wp-sitemap.xml",
        f"{base_url}/sitemap_index.xml",
        f"{base_url}/sitemap-1.xml"
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
#or 'sitemap' in link
    ]

    # Dedupliziere die Sitemap-Links, damit jeder Link nur einmal verarbeitet wird
    return list(set(filtered_sitemap_links))  # Verwende ein Set, um Duplikate zu entfernen

def normalize_domain_with_exception(url):
    """
    Normalisiert die URL nur, wenn sie von 'antifainfoblatt' stammt.
    """
    if 'antifainfoblatt.prod.ifg.io' in url:
        # Normalisiere die URL, wenn sie von 'antifainfoblatt.prod.ifg.io' kommt
        return url.replace('http://antifainfoblatt.prod.ifg.io', 'https://antifainfoblatt.de')
    # Keine Änderung für andere Webseiten
    return url

# Funktion zum Abrufen der Artikel-URLs von der Sitemap
def get_urls_from_sitemap(sitemap_url):
    try:
        response = requests.get(sitemap_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'xml')

        # Finde alle Artikel-URLs in den Sitemaps
        urls = [url_loc.text for url_loc in soup.find_all('loc')]

        # Normalisiere die URLs nur für 'antifainfoblatt'
        normalized_urls = [normalize_domain_with_exception(url) for url in urls]

        # Liste der Dateitypen, die wir ausschließen möchten
        excluded_file_types = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.pdf', '.doc', '.docx', '.mp3', '.mp4',
                               '.webp']

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
    article = soup.find('article') or soup.find('div', class_="postcontent") or soup.find('div',
                                                                                          class_="singlepost") or soup.find(
        'div', class_="article-text")

    if article:
        paragraphs = article.find_all('p')
        list_items = article.find_all('li')
        em_items = article.find_all('em')
    else:
        # Fallback, wenn kein spezifischer Container gefunden wird
        paragraphs = soup.find_all('p')
        list_items = soup.find_all('li')
        em_items = article.find_all('em')


    # Füge den gesamten Text zusammen, aus Paragraphen und Listen
    full_text = ' '.join(html.unescape(tag.get_text(separator=' ', strip=True)) for tag in paragraphs + list_items + em_items)
    full_text = full_text.replace('\u00AD', '').replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    full_text = ' '.join(full_text.split())

    return {
        "title": title_text,
        "full_text": full_text,
        "comments": comments
    }
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
            section.decompose()

        # Extrahiere den Text aus <p>, <li>, <h2>, <h3>, <div> und ähnlichen relevanten Tags
        text_elements = soup.find_all(['p', 'li'])
        full_text = ' '.join(element.get_text(separator=' ', strip=True) for element in text_elements)

        # Bereinige den Text von überflüssigen Leerzeichen
        full_text = ' '.join(full_text.split())

        return {
            'title': title,
            'full_text': full_text,
            'comments': comments  # Füge auch Kommentare hinzu
        }
    except Exception as e:
        logging.error(f"Fehler beim Abrufen des Artikels mit Selenium: {article_url} - {e}")
        return None
    finally:
        driver.quit()

# Funktion zum Scraping eines Artikels
def scrape_article(url, processed_urls, crawled_urls, sitemap_based=True):
    try:
        # Überprüfe, ob die URL ein Fragment (#) enthält und überspringe sie, falls ja
        if '#' in url:
            logging.info(f"Überspringe URL mit Fragment (#): {url}")
            return

        # Überprüfe, ob der Artikel bereits in der MongoDB existiert
        article = collection.find_one({'url': url})
        stored_comments = get_stored_comments(url) if article else set()

        # Verwende Selenium für bestimmte Webseiten, ansonsten normalen Abruf
        if "zeitschrift-luxemburg.de" in url or "schweizerzeit.ch" in url:
            logging.info(f"Verwende Selenium für URL: {url}")
            content = extract_article_content_with_selenium(url)
        else:
            response = requests.get(url)
            response.raise_for_status()

            # Überprüfe den Content-Type des Headers
            content_type = response.headers.get('Content-Type', '').lower()

            # Liste von Content-Types, die binäre Daten anzeigen und übersprungen werden sollten
            ignored_content_types = [
                'image/png', 'image/jpeg', 'image/gif', 'image/bmp', 'image/tiff', 'image/webp',  # Bildformate
                'application/pdf', 'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # Dokumente
                'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'application/vnd.ms-powerpoint',
                'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                'audio/mpeg', 'audio/wav', 'video/mp4', 'video/avi', 'video/quicktime',  # Multimedia
                'application/zip', 'application/x-rar-compressed', 'application/x-7z-compressed',  # Archivformate
                'application/octet-stream', 'application/x-binary'  # Binäre Daten
            ]

            # Wenn der Content-Type kein HTML ist, überspringe die URL
            if 'text/html' not in content_type and any(
                    ignored_type in content_type for ignored_type in ignored_content_types):
                logging.warning(f"Überspringe nicht-HTML Inhalt: {url} (Content-Type: {content_type})")
                return

            # Nur HTML-Inhalte mit BeautifulSoup parsen
            content = extract_content_from_html(response.content)

        if content:
            title_text = content['title']
            full_text = content['full_text']
            comments = content['comments']

            if article:
                # Prüfe, ob der Artikeltext oder Kommentare aktualisiert werden müssen
                update_fields = {}

                # Vergleiche den Artikeltext
                if article['full_text'] != full_text:
                    update_fields['full_text'] = full_text

                # Neue Kommentare als Differenz bestimmen
                new_comments = set(comments) - stored_comments

                if new_comments:
                    update_fields['comments'] = list(stored_comments | new_comments)  # Union von neuen und gespeicherten Kommentaren

                # Wenn es Änderungen gibt, aktualisiere den Artikel
                if update_fields:
                    collection.update_one(
                        {'url': url},
                        {'$set': update_fields}
                    )
                    logging.info(f"Artikel aktualisiert: {url}")
                else:
                    logging.info(f"Artikel ist bereits aktuell: {url}")
            else:
                # Neuer Artikel, direkt speichern
                collection.insert_one({
                    'title': title_text,
                    'url': url,
                    'full_text': full_text,
                    'comments': list(comments)
                })
                logging.info(f"Neuer Artikel gespeichert: {url}")

            # Füge die URL zur processed_urls hinzu, nachdem sie erfolgreich gespeichert oder aktualisiert wurde
            processed_urls.add(url)
            crawled_urls.add(url)
            #time.sleep(10)  # Füge Crawl-Delay von 10 Sekunden hinzu

    except requests.RequestException as e:
        logging.error(f"Artikel konnte nicht gescraped werden: {url} aufgrund von {str(e)}")

# Funktion zum erneuten Crawlen von bereits gespeicherten URLs
def crawl_stored_urls():
    """
    Crawlt URLs, die bereits in der Datenbank gespeichert sind, um den Artikeltext und die Kommentare zu aktualisieren.
    """
    # Alle bereits gespeicherten URLs aus der MongoDB abrufen
    stored_urls = collection.find({}, {'url': 1})

    for doc in stored_urls:
        url = doc['url']
        logging.info(f"Neues Crawlen der gespeicherten URL: {url}")
        scrape_article(url, processed_urls=set(), crawled_urls=set())  # Re-crawl jede URL und verarbeite sie erneut

def re_crawl_single_url(url):
    """
    Crawlt nur die angegebene URL erneut, um den Artikeltext und die Kommentare zu aktualisieren.
    """
    try:
        # Aufruf der bestehenden `scrape_article`-Funktion für die spezifische URL
        logging.info(f"Starte das Re-Crawling für die spezifische URL: {url}")
        scrape_article(url, processed_urls=set(), crawled_urls=set())  # Re-crawle nur die bestimmte URL
    except Exception as e:
        logging.error(f"Fehler beim Re-Crawling der URL {url}: {e}")

# Hauptfunktion zum Finden und Scrapen von Artikeln
def main():
    base_url = input("Gib die Basis-URL der Webseite ein (z.B. https://example.com): ").strip()

    # Lade die bereits verarbeiteten URLs
    processed_urls = load_processed_urls(base_url)

    # Lade die bereits gecrawlten URLs
    crawled_urls = load_crawled_urls(base_url)

    # Prüfe, ob die Webseite eine Sitemap hat
    sitemap_links = get_all_sitemap_links(base_url)

    all_urls = []  # Liste für alle gesammelten URLs

    # 1. URLs aus der Sitemap sammeln, wenn vorhanden
    if sitemap_links:
        logging.info("Verarbeite Artikel von Sitemaps.")
        for sitemap_url in sitemap_links:
            all_urls.extend(get_urls_from_sitemap(sitemap_url))

    # 2. Wenn keine Sitemaps gefunden wurden, crawlen wir die Webseite
    if not sitemap_links or not all_urls:
        logging.info(f"Keine Sitemap gefunden, Crawling für: {base_url}")
        crawled_urls_in_crawl = crawl(base_url)
        all_urls.extend(crawled_urls_in_crawl)

    # 3. Nun verarbeiten wir alle gesammelten URLs
    new_urls = [url for url in all_urls if normalize_domain_with_exception(url) not in processed_urls and normalize_domain_with_exception(url) not in crawled_urls]  # Filtere bereits verarbeitete und gecrawlte URLs

    for url in new_urls:
        scrape_article(url, processed_urls, crawled_urls, sitemap_based=False)  # Sitemap-basierte Logik auf False setzen
        time.sleep(1)  # Füge eine Pause zwischen den Anfragen hinzu

    #Optional: Crawle schnell bestimmte URLs, um schnell zu sein, weil sonst Re-Crawling unten sehr lange dauert
    #target_url = "https://antifainfoblatt.de/aib144/veranstaltungsreihe-winter-coming"
    #re_crawl_single_url(target_url)

    # 4. Optional: Crawle alle bereits gespeicherten URLs erneut
    #logging.info("Starte das Re-Crawling aller gespeicherten URLs.")
    #crawl_stored_urls()  # Re-crawlen der bereits gespeicherten Artikel


if __name__ == '__main__':
    main()