from pymongo import MongoClient
import random

# Verbindung zur MongoDB herstellen
client = MongoClient('mongodb://localhost:27017/')
db = client['scrapy_database']
collection = db['raw_articles']

# Schritt 1: Zufällig 100 Dokumente auswählen
documents = list(collection.find().limit(1000))  # Zuerst eine größere Anzahl von Dokumenten abrufen
sample_docs = random.sample(documents, min(10, len(documents)))  # Zufällige Auswahl von 100 Dokumenten

# Schritt 2: Die ausgewählten Dokumente löschen
ids_to_delete = [doc['_id'] for doc in sample_docs]
collection.delete_many({'_id': {'$in': ids_to_delete}})

print(f"Gelöschte Dokumente: {ids_to_delete}")