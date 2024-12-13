# Verbindung zur MongoDB
from pymongo import MongoClient
from datetime import datetime

# MongoDB-Verbindung herstellen
client = MongoClient('mongodb://localhost:27017/')
db = client['scrapy_database']
processed_collection = db['sezessionProcessed']
daily_summary_collection = db['sezessionDaily']
vocabulary_collection = db['sezessionVocab']

# Heutiges Datum festlegen
start_date = '2024-09-03'

# `new_words_today` aus der `vocabulary_collection` abrufen
new_words_today = set()
for entry in vocabulary_collection.find({'first_seen': start_date}):
    new_words_today.add(entry['word'])

# Wiederholte Wörter bestimmen (bleibt leer, da es der erste Tag ist)
repeated_words_today = set()

# Struktur für die tägliche Zusammenfassung erstellen
daily_summary = {
    'date': start_date,
    'new_words_today': list(new_words_today),
    'repeated_words_today': list(repeated_words_today),
    'new_word_count': len(new_words_today),
    'repeated_word_count': len(repeated_words_today)
}

# Eintrag in der `daily_summary_collection` speichern
daily_summary_collection.insert_one(daily_summary)

print(f"Tägliche Zusammenfassung für {start_date} erfolgreich erstellt.")
