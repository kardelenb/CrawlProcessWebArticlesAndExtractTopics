'''from pymongo import MongoClient
import json

# Verbindung zur MongoDB herstellen
client = MongoClient('mongodb://localhost:27017/')
db = client['scrapy_database']
collection = db['luxemburg_raw']

# Die ersten 150 Dokumente aus der MongoDB-Datenbank holen
documents = collection.find().limit(220)

# Alle Dokumente in eine Liste umwandeln (MongoDB Cursor in Python-Datenstruktur)
docs_list = []
for doc in documents:
    # MongoDB-Dokumente direkt der Liste hinzufügen (bereits in Dict-Format)
    docs_list.append(doc)

# Die Liste der Dokumente in eine JSON-Datei schreiben
with open('luxemburg_documents.json', 'w', encoding='utf-8') as json_file:
    json.dump(docs_list, json_file, default=str, ensure_ascii=False, indent=4)

print("Erfolgreich 150 Dokumente exportiert und in der JSON-Datei gespeichert.")
'''

from pymongo import MongoClient
from collections import Counter
import logging

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Verbindung zur MongoDB aufbauen
client = MongoClient('mongodb://localhost:27017/')
db = client['scrapy_database']
collection = db['antifaInfaBlattNeu']

def find_duplicate_urls_in_db():
    # Hole alle URLs aus der Datenbank
    urls = [doc['url'] for doc in collection.find({}, {'url': 1})]

    # Zähle, wie oft jede URL vorkommt
    url_counter = Counter(urls)

    # Finde alle URLs, die mehr als einmal vorkommen
    duplicates = {url: count for url, count in url_counter.items() if count > 1}

    if duplicates:
        logging.info("Doppelte URLs gefunden:")
        for url, count in duplicates.items():
            logging.info(f"URL: {url} - {count} mal")
    else:
        logging.info("Keine doppelten URLs gefunden.")

if __name__ == '__main__':
    find_duplicate_urls_in_db()

'''
from pymongo import MongoClient

# Verbindung zur MongoDB aufbauen
client = MongoClient('mongodb://localhost:27017/')
db = client['scrapy_database']
collection = db['antifaRaw']


def search_and_delete_url_in_db(url_to_search):
    # Sucht nach einem Dokument, das die angegebene URL enthält
    result = collection.find_one({"url": url_to_search})

    if result:
        print(f"URL gefunden: {result}")

        # Lösche das gefundene Dokument
        delete_result = collection.delete_one({"url": url_to_search})

        if delete_result.deleted_count > 0:
            print(f"URL '{url_to_search}' erfolgreich gelöscht.")
        else:
            print(f"URL '{url_to_search}' konnte nicht gelöscht werden.")
    else:
        print(f"URL '{url_to_search}' wurde nicht gefunden.")


if __name__ == '__main__':
    # Beispiel-URL, die gesucht und gelöscht werden soll
    url_to_search = 'https://sezession.de/69722/vor-tausend-jahren-starb-heinrich-ii'
    search_and_delete_url_in_db(url_to_search)
'''
from pymongo import MongoClient
'''
# Verbindung zur MongoDB aufbauen
client = MongoClient('mongodb://localhost:27017/')
db = client['scrapy_database']
collection = db['vocabularySezessionWithoutGN']

def search_word_or_phrase(word_or_phrase):
    # Sucht nach dem Wort oder der Phrase im 'vocabulary'-Dokument
    result = collection.find_one({"word": word_or_phrase})  # Hier "word" als Beispielfeld verwenden, anpassen falls notwendig

    if result:
        print(f"Wort/Phrase gefunden: {result}")
    else:
        print(f"Wort/Phrase '{word_or_phrase}' wurde nicht gefunden.")

if __name__ == '__main__':
    # Beispielwort/-phrase, nach dem gesucht werden soll
    word_or_phrase = "Merkel-Bibel"  # Ersetze "Beispielwort" durch das tatsächliche Wort oder die Phrase
    search_word_or_phrase(word_or_phrase)
'''
'''
from pymongo import MongoClient

# Verbindung zur MongoDB aufbauen
client = MongoClient('mongodb://localhost:27017/')
db = client['scrapy_database']
collection = db['schweizerZeitVocab']


def search_words_containing(substring):
    # Sucht nach Dokumenten, die die Teilzeichenkette im Feld 'word' enthalten
    results = collection.find({"word": {"$regex": substring, "$options": "i"}})

    # Überprüfe, ob Ergebnisse gefunden wurden
    matching_words = [doc["word"] for doc in results]

    if matching_words:
        print("Gefundene Wörter/Phrasen:")
        for word in matching_words:
            print(word)
    else:
        print(f"Keine Wörter/Phrasen gefunden, die '{substring}' enthalten.")


if __name__ == '__main__':
    # Beispiel-Teilzeichenkette, nach der gesucht werden soll
    substring = "Merkel"  # Ersetze "Beispiel" durch die tatsächliche Zeichenkette, die du suchen möchtest
    search_words_containing(substring)
'''
'''
import spacy

# Lade das deutsche und englische spaCy-Modell (z. B. "de_core_news_sm" und "en_core_web_sm")
nlp_de = spacy.load("de_core_news_sm")
nlp_en = spacy.load("en_core_web_sm")

# Liste der zu filternden Wörter/Phrasen
phrases = [
    "Merkelzeit", "entmerkelten", "entmerkelten Union", "Merkelpropaganda",
    "Merkelpolitik", "Vormerkelära", "ausgemerkelten", "Merkelfront",
    "Merkelpresse", "merkeltreue", "merkeltreue Ostpolitik", "Merkelokratie",
    "humanitären Merkelokratie", "weltweiten Merkelisten", "Merkelgegner"
    # Füge weitere Wörter/Phrasen nach Bedarf hinzu
]

def apply_ner_filter(phrases, language='de'):
    # Wähle das Sprachmodell basierend auf der Eingabesprache
    if language == 'de':
        doc = nlp_de(" ".join(phrases))
    else:
        doc = nlp_en(" ".join(phrases))

    # Sammle Entitäten, die vom Typ 'PER', 'LOC', oder 'ORG' sind
    excluded_phrases = set(ent.text for ent in doc.ents if ent.label_ in {'PER', 'LOC', 'ORG'})

    # Filtere die ursprünglichen Phrasen, um nur jene zurückzugeben, die keine dieser Entitäten enthalten
    filtered_phrases = [phrase for phrase in phrases if phrase not in excluded_phrases]

    return filtered_phrases

# Wenden die Funktion auf die Phrasen an und geben das Ergebnis aus
filtered_phrases = apply_ner_filter(phrases, language='de')
print("Gefilterte Phrasen ohne 'PER', 'LOC', oder 'ORG' Entitäten:")
print(filtered_phrases)
'''