import requests
from bs4 import BeautifulSoup
import time

# User-Agent einstellen, um als legitimer Browser aufzutreten
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}


# Funktion zum Abrufen des HTML-Inhalts einer Seite
def get_page_content(url):
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Fehler abfangen
        return response.text
    except requests.RequestException as e:
        print(f"Fehler beim Abrufen der Seite: {url} - {e}")
        return None


# Funktion zum Extrahieren von Artikeln (Titel und Text) aus der Seite
def extract_article_content(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # Titel des Artikels finden
    title_tag = soup.find('title') or soup.find('h1')
    title = title_tag.get_text(strip=True) if title_tag else "Kein Titel"

    # Extrahiere den Text aus <p>, <li>, <h2>, <h3>, <div> und ähnlichen relevanten Tags
    text_elements = soup.find_all(['p', 'li', 'h2', 'h3', 'div', 'span'])

    # Hier kannst du anpassen, um nur den relevanten Artikeltext zu extrahieren, z.B. indem du den spezifischen
    # Container des Artikels identifizierst (wie class="article-content" etc.)
    full_text = ' '.join(element.get_text(separator=' ', strip=True) for element in text_elements)

    # Bereinige den Text von überflüssigen Leerzeichen
    full_text = ' '.join(full_text.split())

    return {
        'title': title,
        'full_text': full_text
    }


# Funktion zum Filtern der Artikel-Links
def is_article_link(url):
    # Diese Funktion kann je nach Seitenstruktur angepasst werden
    # Zum Beispiel könnte man nach 'article', 'news', 'post' in der URL suchen
    return 'article' in url or 'news' in url or 'post' in url or 'aib' in url


# Rekursive Funktion zum Crawlen der Webseite
def crawl_website(base_url, visited_urls, max_depth=3):
    if max_depth == 0:
        return

    # Abrufen des Inhalts der Startseite
    page_content = get_page_content(base_url)
    if not page_content:
        return

    # Erstelle ein BeautifulSoup-Objekt für die Seite
    soup = BeautifulSoup(page_content, 'html.parser')

    # Extrahiere alle Links auf der Seite
    links = []
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        if href.startswith('/'):
            full_url = requests.compat.urljoin(base_url, href)
            links.append(full_url)
        elif href.startswith('http'):
            links.append(href)

    # Entferne Duplikate
    links = list(set(links))

    # Verarbeite jeden Link
    for link in links:
        if link in visited_urls:
            continue  # Überspringe bereits besuchte Seiten

        visited_urls.add(link)

        # Prüfen, ob der Link zu einem Artikel führt
        if is_article_link(link):
            print(f"Artikel gefunden: {link}")
            article_content = get_page_content(link)
            if article_content:
                article_data = extract_article_content(article_content)
                print(f"Titel: {article_data['title']}")
                print(f"Text: {article_data['full_text'][:1800]}...")  # Ausgabe der ersten 500 Zeichen des Artikels

        # Falls es keine Artikel-Seite ist, rekursiv weiter crawlen
        else:
            print(f"Crawlen der Seite: {link}")
            crawl_website(link, visited_urls, max_depth - 1)

        # Wartezeit, um die Webseite nicht zu überlasten
        time.sleep(1)


# Start des Crawlers
if __name__ == '__main__':
    base_url = 'https://antifainfoblatt.de'  # Beispiel-URL der Webseite
    visited_urls = set()  # Set zur Vermeidung von doppeltem Besuch
    crawl_website(base_url, visited_urls, max_depth=3)
