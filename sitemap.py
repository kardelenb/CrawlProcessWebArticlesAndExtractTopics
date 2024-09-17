import requests
from bs4 import BeautifulSoup
import json

# Funktion zum Zählen und Ausgeben der gesamten Links
def list_links_in_sitemap(sitemap_url):
    try:
        # Sendet eine GET-Anfrage zur Sitemap-URL
        response = requests.get(sitemap_url)
        # Prüfen auf erfolgreichen HTTP-Status
        response.raise_for_status()
        # Erstelle ein BeautifulSoup-Objekt mit dem XML-Parser
        soup = BeautifulSoup(response.content, 'lxml')
        # Finde alle <loc>-Tags in der Sitemap
        urls = soup.find_all('loc')
        # Bereite die Daten für die JSON-Ausgabe vor
        link_data = {
            "sitemap_url": sitemap_url,
            "count": len(urls),
            "links": [url.get_text() for url in urls]
        }
        return link_data
    except requests.RequestException as e:
        print(f"Error fetching sitemap: {e}")
        return None

# Liste der Sitemap-URLs
sitemap_urls = [
       'https://sezession.de/wp-sitemap-posts-post-1.xml',
        'https://sezession.de/wp-sitemap-posts-post-2.xml',
        'https://sezession.de/wp-sitemap-posts-post-3.xml',
        'https://sezession.de/wp-sitemap-posts-post-4.xml',
]

# Speichere die Links in einer JSON-Datei
all_link_data = []
total_link_count = 0

for sitemap_url in sitemap_urls:
    link_data = list_links_in_sitemap(sitemap_url)
    if link_data:
        all_link_data.append(link_data)
        total_link_count += link_data['count']  # Summe der Links erhöhen

# Ausgabe in eine JSON-Datei
with open('masterthesis/masterthesis/sitemap_links.json', 'w', encoding='utf-8') as f:
    json.dump(all_link_data, f, ensure_ascii=False, indent=4)

print("Links wurden in 'sitemap_links.json' gespeichert.")
print(f"Gesamtanzahl der Links: {total_link_count}")