from pymongo import MongoClient
from datetime import datetime
import logging

# Verbindung zur MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['scrapy_database']
processed_collection = db['sezessionProcessed']
daily_summary_collection = db['sezessionDaily']
vocabulary_collection = db['sezessionVocab']
vocabulary_growth_collection = db['sezessionGrowth']

# Heutiges Datum
start_date = '2024-09-03'

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def rebuild_daily_and_growth():
    article_word_frequencies = {}
    comment_word_frequencies = {}

    # Alle Artikel durchgehen und Wortfrequenzen sammeln
    for article in processed_collection.find():
        for word in article.get('new_article_phrases', []):
            article_word_frequencies[word] = article_word_frequencies.get(word, 0) + 1
        for word in article.get('new_comment_phrases', []):
            comment_word_frequencies[word] = comment_word_frequencies.get(word, 0) + 1

    # Bestimme alle Wörter aus der Vokabelsammlung
    vocabulary_words = list(vocabulary_collection.find({}, {"word": 1, "first_seen": 1}))
    new_words_today = [word["word"] for word in vocabulary_words if word["first_seen"] == start_date]

    # Tägliche Zusammenfassung in kleinere Teile speichern
    for word, frequency in article_word_frequencies.items():
        daily_summary_collection.insert_one({
            'date': start_date,
            'type': 'article',
            'word': word,
            'frequency': frequency
        })

    for word, frequency in comment_word_frequencies.items():
        daily_summary_collection.insert_one({
            'date': start_date,
            'type': 'comment',
            'word': word,
            'frequency': frequency
        })

    # Wachstumsspeicher in die Datenbank schreiben
    vocabulary_growth_collection.insert_one({
        'date': start_date,
        'new_words_count': len(new_words_today),
        'repeated_words_count': 0,  # Wiederholte Wörter gibt es am ersten Tag nicht
        'total_vocabulary_count': len(vocabulary_words)  # Insgesamt bekannte Wörter
    })

    logging.info(f"Tägliche Zusammenfassung und Vokabelwachstum für {start_date} erfolgreich gespeichert.")

# Funktion ausführen
rebuild_daily_and_growth()
