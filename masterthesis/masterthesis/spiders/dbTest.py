from pymongo import MongoClient
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