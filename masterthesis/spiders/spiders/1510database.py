import json
from pymongo import MongoClient

# Verbindung zur MongoDB herstellen
client = MongoClient('mongodb://localhost:27017/')
db = client['scrapy_database']
collection = db['luxemburg_raw']

# Abfrage, um die ersten 100 Dokumente aus der Sammlung abzurufen
first_100_entries = collection.find().limit(100)

# Die abgerufenen Dokumente in eine Liste umwandeln
first_100_entries_list = list(first_100_entries)

# Speichern der ersten 100 Einträge in eine JSON-Datei
with open('first_100_entries.json', 'w', encoding='utf-8') as file:
    json.dump(first_100_entries_list, file, ensure_ascii=False, indent=4)

print("Die ersten 100 Einträge wurden erfolgreich in der Datei 'first_100_entries.json' gespeichert.")