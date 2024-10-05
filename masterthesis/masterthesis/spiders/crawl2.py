import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pymongo import MongoClient
import time
import logging

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Verbindung zu MongoDB einrichten
client = MongoClient('mongodb://localhost:27017/')
db = client['scrapy_database']
collection = db['raw_compact']

# Selenium WebDriver einrichten
def get_selenium_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Headless-Modus für das unsichtbare Browsen
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=chrome_options)
    return driver

# Funktion zum Klicken auf einen Button, um zusätzliche Links sichtbar zu machen
def click_navigation_button(driver):
    try:
        # Warte auf das Vorhandensein und die Klickbarkeit des Buttons
        button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[role="button"]'))
        )
        button.click()
        time.sleep(2)  # Wartezeit, damit die neuen Links geladen werden
        logging.info("Navigations-Button geklickt.")
    except Exception as e:
        logging.error(f"Fehler beim Klicken auf den Button: {e}")

# Funktion zum Abrufen und Extrahieren aller Links auf einer Seite
def get_all_links_from_page_with_selenium(driver):
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # Sammle alle Links von der Seite
    all_links = set()
    a_tags = soup.find_all('a', href=True)
    for a_tag in a_tags:
        href = a_tag['href']
        full_url = requests.compat.urljoin(driver.current_url, href)
        all_links.add(full_url)

    return list(all_links)

# Funktion, um ein <li>-Element anzuklicken und dann auf der neuen Seite Links zu extrahieren
def click_li_and_extract_links(driver, li_element):
    try:
        # Klicke auf das <li>-Element (oder seinen <a>-Tag, wenn es einen gibt)
        li_link = li_element.find_element(By.TAG_NAME, 'a')
        li_link.click()
        time.sleep(3)  # Wartezeit, um die neue Seite zu laden

        # Extrahiere alle Links auf der neu geöffneten Seite
        links = get_all_links_from_page_with_selenium(driver)
        logging.info(f"Extrahierte {len(links)} Links auf der Seite: {driver.current_url}")

        # Gehe zu jedem gefundenen Link und speichere den Artikel
        for link in links:
            logging.info(f"Scrape Artikel von URL: {link}")
            scrape_article(driver, link)

    except Exception as e:
        logging.error(f"Fehler beim Klicken auf <li> und Extrahieren der Links: {e}")

# Funktion zum Scrapen des Artikels und zum Speichern in der Datenbank
def scrape_article(driver, url):
    try:
        if collection.find_one({'url': url}):
            logging.info(f"Artikel bereits vorhanden: {url}")
            return

        driver.get(url)
        time.sleep(2)  # Warte, bis die Seite vollständig geladen ist

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        title = soup.find('title').get_text() if soup.find('title') else "Kein Titel"
        full_text = ' '.join(p.get_text(separator=' ', strip=True) for p in soup.find_all('p'))

        if full_text.strip():
            collection.insert_one({
                'title': title,
                'url': url,
                'full_text': full_text,
            })
            logging.info(f"Artikel erfolgreich gespeichert: {url}")

    except Exception as e:
        logging.error(f"Fehler beim Scrapen des Artikels: {e}")

# Hauptfunktion zum Klicken auf den Button, Durchlaufen der <li> Elemente und Extraktion der Links
def main():
    base_url = input("Gib die Basis-URL der Webseite ein (z.B. https://example.com): ").strip()
    driver = get_selenium_driver()

    try:
        driver.get(base_url)
        time.sleep(2)  # Warte auf das Laden der Seite

        # Klick auf den Button, um die Navigation zu öffnen
        click_navigation_button(driver)

        # Finde alle <li>-Elemente
        li_elements = driver.find_elements(By.CSS_SELECTOR, 'li')
        logging.info(f"{len(li_elements)} <li> Elemente gefunden.")

        # Durchlaufe jedes <li>-Element und klicke es an
        for i, li in enumerate(li_elements):
            logging.info(f"Klick auf <li>-Element {i+1} von {len(li_elements)}")
            click_li_and_extract_links(driver, li)

            # Kehre zur Hauptseite zurück, um das nächste <li>-Element zu klicken
            driver.get(base_url)
            time.sleep(2)

            # Klick auf den Button, um das Menü erneut zu öffnen
            click_navigation_button(driver)

    finally:
        driver.quit()

if __name__ == '__main__':
    main()
