from pymongo import MongoClient
import json
from bson import ObjectId

# Funktion zum Serialisieren von ObjectId
class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return super().default(o)

# Verbindung zu MongoDB herstellen
client = MongoClient('mongodb://localhost:27017/')  # Verwende hier deine MongoDB-Verbindung
db = client['scrapy_database']  # Name deiner Datenbank
collection = db['processed_articles2']  # Name deiner Collection

# Erste 70 Dokumente abrufen
results = collection.find({}).limit(70)

# Ergebnisse in eine JSON-Datei schreiben und sicherstellen, dass UTF-8 korrekt ist
with open('ergebnisse.json', 'w', encoding='utf-8') as file:
    json.dump(list(results), file, cls=JSONEncoder, ensure_ascii=False, indent=4)

print("Die ersten 70 Dokumente wurden erfolgreich in ergebnisse.json gespeichert.")
