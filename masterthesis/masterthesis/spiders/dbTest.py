'''from pymongo import MongoClient
import logging

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Verbindung zu MongoDB herstellen
client = MongoClient('mongodb://localhost:27017/')
db = client['scrapy_database']
collection = db['sezession0510raw']

# Funktion zum Entfernen von URLs, die nicht mit 'https://sezession.de/' beginnen
def remove_invalid_urls():
    base_url = 'https://sezession.de/'

    # Überprüfen, wie viele Dokumente es insgesamt in der Collection gibt
    total_count = collection.count_documents({})
    logging.info(f"Gesamtzahl der Dokumente in der Collection: {total_count}")

    # Zähle die Dokumente, deren URL nicht mit der Basis-URL beginnt
    invalid_count = collection.count_documents({'url': {'$not': {'$regex': f'^{base_url}'}}})
    logging.info(f"Anzahl der zu löschenden Dokumente (ungültige URLs): {invalid_count}")

    # Finde alle Dokumente, deren URL nicht mit der Basis-URL beginnt
    invalid_urls = collection.find({'url': {'$not': {'$regex': f'^{base_url}'}}})

    # Optional: Liste der ungültigen URLs anzeigen (zum Überprüfen)
    for doc in invalid_urls:
        logging.info(f"Ungültige URL gefunden: {doc['url']}")

    # Wenn ungültige URLs gefunden wurden, dann löschen
    if invalid_count > 0:
        confirm = input("Möchtest du diese URLs wirklich löschen? (ja/nein): ")
        if confirm.lower() == 'ja':
            result = collection.delete_many({'url': {'$not': {'$regex': f'^{base_url}'}}})
            logging.info(f"Anzahl der gelöschten Dokumente: {result.deleted_count}")
        else:
            logging.info("Löschung abgebrochen.")
    else:
        logging.info("Keine ungültigen URLs gefunden.")

# Aufruf der Funktion
remove_invalid_urls()
'''
'''
import json
import logging

from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['scrapy_database']
collection = db['antifaInfaBlattNeu']

# Funktion zum Überprüfen auf doppelte URLs
def check_duplicate_urls():
    # Gruppiere nach 'url' und zähle die Anzahl der Einträge pro URL
    pipeline = [
        {"$group": {"_id": "$url", "count": {"$sum": 1}}},
        {"$match": {"count": {"$gt": 1}}}
    ]

    duplicates = list(collection.aggregate(pipeline))

    if duplicates:
        logging.info(f"Anzahl der doppelten URLs: {len(duplicates)}")
        for dup in duplicates:
            logging.info(f"Doppelte URL: {dup['_id']} - Anzahl der Einträge: {dup['count']}")
    else:
        logging.info("Keine doppelten URLs gefunden.")

# Aufruf der Funktion
check_duplicate_urls()

if __name__ == "__main__":
    check_duplicate_urls()
'''
'''
from pymongo import MongoClient

# Verbindung zu MongoDB einrichten
client = MongoClient('mongodb://localhost:27017/')
db = client['scrapy_database']
collection = db['test']

# Funktion, um alle URLs aus der Collection zu extrahieren und auszugeben
def print_all_urls():
    # Finde alle Dokumente, die eine URL enthalten
    documents = collection.find({}, {'url': 1, '_id': 0})  # Nur die URL-Felder zurückgeben

    # Alle URLs ausgeben
    for doc in documents:
        print(doc.get('url'))

# Hauptfunktion
if __name__ == "__main__":
    print_all_urls()
'''
'''
from pymongo import MongoClient
from collections import defaultdict

# Verbindung zu MongoDB herstellen
client = MongoClient('mongodb://localhost:27017/')
db = client['scrapy_database']
collection = db['vocabularySezession']


def check_duplicate_words():
    # Dictionary zum Speichern von Wörtern und den zugehörigen _ids
    word_dict = defaultdict(list)

    # Alle Dokumente aus der Collection abrufen
    documents = collection.find()

    # Jedes Dokument durchsuchen und die Wörter mit ihren _ids sammeln
    for doc in documents:
        word = doc.get('word', None)
        _id = doc.get('_id', None)
        if word and _id:
            word_dict[word].append(_id)

    # Überprüfen, ob Wörter mehrfach vorkommen
    duplicates_found = False
    for word, ids in word_dict.items():
        if len(ids) > 1:
            duplicates_found = True
            print(f"Das Wort '{word}' kommt in mehreren Dokumenten vor, mit den folgenden IDs:")
            for _id in ids:
                print(f" - {_id}")

    if not duplicates_found:
        print("Keine doppelten Wörter gefunden.")


# Funktion aufrufen, um die Prüfung durchzuführen
check_duplicate_words()'''
'''  
from pymongo import MongoClient

# Verbindung zur MongoDB einrichten
client = MongoClient('mongodb://localhost:27017/')
db = client['scrapy_database']
processed_collection = db['sezessionprocessed']  # Beispielhafte Collection

# URL, nach der gesucht werden soll
target_url = 'https://sezession.de/69638/europaeische-notizen-5-gemeinschaft-in-tschechien'

# Dokument aus der Datenbank basierend auf der URL abrufen
article_info = processed_collection.find_one({'url': target_url})

# Überprüfen, ob ein Artikel gefunden wurde
if article_info:
    # Ausgabe der gesamten Informationen des Artikels
    print("Artikel gefunden:")
    print(f"_id: {article_info['_id']}")
    print(f"Title: {article_info['title']}")
    print(f"URL: {article_info['url']}")
    print(f"Full Text: {article_info['full_text']}")
    print(f"Ranked Keywords: {article_info['ranked_keywords']}")
    print(f"New Article Phrases: {article_info['new_article_phrases']}")
    print(f"New Comment Phrases: {article_info['new_comment_phrases']}")
    print(f"First Processed: {article_info['first_processed']}")
    print(f"Last Processed: {article_info['last_processed']}")
else:
    print("Kein Artikel mit der angegebenen URL gefunden.")
'''
'''
from pymongo import MongoClient

# Verbindung zur MongoDB einrichten
client = MongoClient('mongodb://localhost:27017/')
db = client['scrapy_database']
vocabulary_collection = db['vocabularySezession']  # Die Collection, in der die Vokabeln gespeichert sind

# Das Wort, nach dem gesucht werden soll
word_to_check = 'nachhegelianische Geschichtsdenken'

# Suche nach dem Wort in der Collection
word_in_vocabulary = vocabulary_collection.find_one({'word': word_to_check})

# Überprüfen, ob das Wort gefunden wurde
if word_in_vocabulary:
    print(f"Das Wort '{word_to_check}' ist bereits im Vokabular vorhanden.")
else:
    print(f"Das Wort '{word_to_check}' ist noch nicht im Vokabular vorhanden.")
'''
'''
from pymongo import MongoClient

# Verbindung zur MongoDB einrichten
client = MongoClient('mongodb://localhost:27017/')
db = client['scrapy_database']
vocabulary_collection = db['vocabularySezessionWithoutGN']  # Die Collection, in der die Vokabeln gespeichert sind

# Das Wort, nach dem gesucht werden soll
word_to_check = 'Moslemsocke'

# Suche nach dem Wort in der Collection
word_info = vocabulary_collection.find_one({'word': word_to_check})

# Überprüfen, ob das Wort gefunden wurde
if word_info:
    print(f"Das Wort '{word_to_check}' ist im Vokabular vorhanden.")
    print(f"_id: {word_info['_id']}")
    print(f"First Seen: {word_info['first_seen']}")
    print(f"Last Seen: {word_info['last_seen']}")
    print(f"Article Occurrences: {word_info['article_occurrences']}")
    print(f"Comment Occurrences: {word_info['comment_occurrences']}")
else:
    print(f"Das Wort '{word_to_check}' ist nicht im Vokabular vorhanden.")
    '''
'''
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['scrapy_database']
collection = db['sezession0510raw']

def searchUrl(url_to_search):
    result = collection.find_one({"url": url_to_search})

    if result:
        print(f"Url gefunden: {result}")

if __name__ == '__main__':
    url_to_search = 'https://sezession.de/68309/hinter-den-linien-tagebuch'
    searchUrl(url_to_search)
    '''

import json
from pymongo import MongoClient
from bson import ObjectId

# Verbindung zu MongoDB herstellen
client = MongoClient('mongodb://localhost:27017/')
db = client['scrapy_database']
collection = db['sezession0510raw']  # Beispielhafte Collection

# Funktion, um den ObjectId-Typ zu serialisieren
class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)  # ObjectId in einen String umwandeln
        return super(JSONEncoder, self).default(o)

# Funktion, um den Eintrag mit einer bestimmten URL zu finden und in eine JSON-Datei zu speichern
def get_article_by_url_and_save(url, json_file):
    article = collection.find_one({'url': url})  # Sucht nach dem Dokument mit der URL
    if article:
        print("Artikel gefunden:")
        #print(article)  # Gibt das gesamte Dokument aus
        # Speichern des Artikels in einer JSON-Datei
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(article, f, cls=JSONEncoder, ensure_ascii=False, indent=4)
        print(f"Artikel wurde in {json_file} gespeichert.")
    else:
        print("Kein Artikel mit dieser URL gefunden.")

# Beispiel-URL und der Name der JSON-Datei
url_to_search = 'https://sezession.de/69850/parteijugend-und-strukturelle-macht'  # Setze hier die richtige URL ein
json_file_name = 'article_data4.json'

# Aufruf der Funktion mit der Beispiel-URL
get_article_by_url_and_save(url_to_search, json_file_name)

'''
from pymongo import MongoClient
import logging
# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Verbindung zu MongoDB herstellen
client = MongoClient('mongodb://localhost:27017/')
db = client['scrapy_database']
collection = db['indyMedia']


# Funktion zum Löschen eines bestimmten Eintrags anhand der URL
def delete_specific_url(url):
    """
    Diese Funktion löscht ein Dokument mit einer bestimmten URL aus der MongoDB-Collection.
    """
    # Versuche, das Dokument mit der angegebenen URL zu löschen
    result = collection.delete_one({'url': url})

    if result.deleted_count > 0:
        logging.info(f"URL erfolgreich gelöscht: {url}")
    else:
        logging.info(f"Kein Dokument mit der URL {url} gefunden.")


# Beispielaufruf der Funktion
url_to_delete = 'https://de.indymedia.org/node/474384'  # Gib hier die URL ein, die du löschen möchtest

delete_specific_url(url_to_delete)
'''
'''
import json
from pymongo import MongoClient
from bson import ObjectId

# Verbindung zu MongoDB herstellen
client = MongoClient('mongodb://localhost:27017/')
db = client['scrapy_database']
collection = db['sezessionProcessed']  # Beispielhafte Collection


# Funktion, um den ObjectId-Typ zu serialisieren
class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)  # ObjectId in einen String umwandeln
        return super(JSONEncoder, self).default(o)


# Funktion, um die letzten zwei Einträge zu holen und in eine JSON-Datei zu speichern
def get_last_two_entries_and_save(json_file):
    # Holen der letzten zwei Einträge nach ObjectId sortiert (neuste zuerst)
    articles = list(collection.find().sort('_id', -1).limit(3))

    if articles:
        print("Letzte zwei Artikel gefunden:")
        for article in articles:
            print(article)  # Gibt jeden Eintrag aus

        # Speichern der Artikel in einer JSON-Datei
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(articles, f, cls=JSONEncoder, ensure_ascii=False, indent=4)
        print(f"Artikel wurden in {json_file} gespeichert.")
    else:
        print("Keine Artikel in der Sammlung gefunden.")


# Name der JSON-Datei
json_file_name = 'last_articles.json'

# Aufruf der Funktion
get_last_two_entries_and_save(json_file_name)
'''
'''
from pymongo import MongoClient
import json

# Verbindung zur MongoDB herstellen
client = MongoClient('mongodb://localhost:27017/')
db = client['scrapy_database']
collection = db['vocabularySezessionWithoutGN']  # Ersetze dies durch den tatsächlichen Namen der Collection


# Funktion zum Abfragen und Speichern der Dokumente, bei denen 'first_seen' und 'last_seen' unterschiedlich sind
def get_documents_with_different_dates():
    documents = collection.find({"$expr": {"$ne": ["$first_seen", "$last_seen"]}})

    # Speichern der Dokumente in einer JSON-Datei
    with open("documents_with_different_dates.json", "w", encoding="utf-8") as file:
        json.dump([doc for doc in documents], file, default=str, ensure_ascii=False, indent=4)
    print("Dokumente wurden in 'documents_with_different_dates.json' gespeichert.")


# Aufruf der Funktion
get_documents_with_different_dates()
'''
'''
import requests
from bs4 import BeautifulSoup
from datetime import datetime

def count_urls_by_date_range(sitemap_url, start_date, end_date):
    try:
        # Lade die Sitemap herunter
        response = requests.get(sitemap_url)
        response.raise_for_status()  # Überprüft auf HTTP-Fehler
        sitemap_content = response.text

        # Parse die XML-Inhalte
        soup = BeautifulSoup(sitemap_content, 'xml')

        # Konvertiere die Datumsgrenzen in datetime-Objekte
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")

        # Finde alle <url>-Einträge und filtere nach Datum
        urls = soup.find_all('url')
        count = 0  # Zähler für URLs

        for url in urls:
            lastmod = url.find('lastmod')
            if lastmod:
                # Extrahiere das Datum und ignoriere den Zeitanteil
                url_date = datetime.strptime(lastmod.text.strip()[:10], "%Y-%m-%d")
                if start_date <= url_date <= end_date:
                    count += 1

        # Anzahl der URLs zurückgeben
        print(f"Anzahl der URLs zwischen {start_date.date()} und {end_date.date()}: {count}")
        return count

    except requests.exceptions.RequestException as e:
        print(f"Fehler beim Laden der Sitemap: {e}")
        return 0
    except ValueError as e:
        print(f"Fehler beim Verarbeiten des Datums: {e}")
        return 0

# URL der Sitemap
sitemap_url = "https://www.der-rechte-rand.de/post-sitemap.xml"

# Definiere den Datumsbereich
start_date = "2016-01-01"
end_date = "2024-09-02"

# Funktion aufrufen
count_urls_by_date_range(sitemap_url, start_date, end_date)
'''
'''
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from pymongo import MongoClient

def compare_urls_with_collection(sitemap_url, start_date, end_date, collection_name, db_name="your_database"):
    try:
        # Verbindung zur MongoDB herstellen
        client = MongoClient("mongodb://localhost:27017/")  # Passe die URL an, falls nötig
        db = client['scrapy_database']
        collection = db['sezession0510raw']

        # Lade die Sitemap herunter
        response = requests.get(sitemap_url)
        response.raise_for_status()  # Überprüft auf HTTP-Fehler
        sitemap_content = response.text

        # Parse die XML-Inhalte
        soup = BeautifulSoup(sitemap_content, 'xml')

        # Konvertiere die Datumsgrenzen in datetime-Objekte
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")

        # Finde alle <url>-Einträge und filtere nach Datum
        urls = soup.find_all('url')
        sitemap_urls = []

        for url in urls:
            lastmod = url.find('lastmod')
            loc = url.find('loc').text.strip()
            if lastmod:
                # Extrahiere das Datum und ignoriere den Zeitanteil
                url_date = datetime.strptime(lastmod.text.strip()[:10], "%Y-%m-%d")
                if start_date <= url_date <= end_date:
                    sitemap_urls.append(loc)

        # URLs aus der Datenbank abrufen
        db_urls = [doc['url'] for doc in collection.find({}, {'url': 1})]

        # Finde fehlende URLs
        missing_urls = [url for url in sitemap_urls if url not in db_urls]

        print(f"Anzahl der fehlenden URLs: {len(missing_urls)}")
        print("Fehlende URLs:")
        for url in missing_urls:
            print(url)

        return missing_urls

    except requests.exceptions.RequestException as e:
        print(f"Fehler beim Laden der Sitemap: {e}")
        return []
    except ValueError as e:
        print(f"Fehler beim Verarbeiten des Datums: {e}")
        return []
    except Exception as e:
        print(f"Ein Fehler ist aufgetreten: {e}")
        return []

# URL der Sitemap
sitemap_url = "https://sezession.de/wp-sitemap-posts-post-1.xml"

# Datumsbereich definieren
start_date = "2000-01-01"
end_date = "2024-09-03"

# Name der MongoDB-Collection
collection_name = "sezession0510raw"

# Funktion aufrufen
compare_urls_with_collection(sitemap_url, start_date, end_date, collection_name)
'''
'''
from pymongo import MongoClient
from collections import Counter

# Verbindung zur MongoDB herstellen
client = MongoClient('mongodb://localhost:27017/')
db = client['scrapy_database']
daily_summary_collection = db['SchweizerZeitDaily']

# Datum des Eintrags, den du prüfen möchtest
start_date = "2024-09-02"

# Hole den Eintrag für den ersten Tag
daily_summary = daily_summary_collection.find_one({'date': start_date})

if daily_summary:
    # Extrahiere die Liste der neuen Wörter
    new_words_today = daily_summary.get('new_words_today', [])

    # Finde Duplikate
    word_counter = Counter(new_words_today)
    duplicates = [word for word, count in word_counter.items() if count > 1]

    print(f"Gesamte neue Wörter: {len(new_words_today)}")
    print(f"Einzigartige neue Wörter: {len(set(new_words_today))}")
    print(f"Anzahl Duplikate: {len(duplicates)}")

    if duplicates:
        print("Liste der Duplikate:")
        for word in duplicates:
            print(f"- {word}: {word_counter[word]} Mal")
    else:
        print("Keine Duplikate gefunden.")
else:
    print(f"Kein Eintrag für das Datum {start_date} in der Sammlung gefunden.")
'''
'''
import json
from pymongo import MongoClient
from bson import ObjectId

# Verbindung zu MongoDB herstellen
client = MongoClient('mongodb://localhost:27017/')
db = client['scrapy_database']
collection = db['sezessionVocab']  # Setze hier den Namen der Collection ein


# Funktion, um den ObjectId-Typ zu serialisieren
class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)  # ObjectId in einen String umwandeln
        return super(JSONEncoder, self).default(o)


# Funktion, um die Häufigkeit eines Wortes zu erhalten
def get_word_frequency(word, json_file=None):
    result = collection.find_one({'word': word})  # Suche das Dokument mit dem spezifischen Wort
    if result:
        print(f"Wort gefunden: {result['word']}")
        print(f"Erst gesehen: {result['first_seen']}")
        print(f"Zuletzt gesehen: {result['last_seen']}")
        print(f"Vorkommen in Artikeln: {result['article_occurrences']}")
        print(f"Vorkommen in Kommentaren: {result['comment_occurrences']}")

        # Speichern der Ergebnisse in einer JSON-Datei
        if json_file:
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, cls=JSONEncoder, ensure_ascii=False, indent=4)
            print(f"Ergebnisse wurden in {json_file} gespeichert.")
    else:
        print(f"Das Wort '{word}' wurde nicht gefunden.")


# Beispielaufruf
word_to_search = "exterme"  # Das Wort, dessen Häufigkeit überprüft werden soll
json_file_name = 'word_frequency.json'  # Name der JSON-Datei, falls benötigt

# Aufruf der Funktion
get_word_frequency(word_to_search, json_file_name)
'''