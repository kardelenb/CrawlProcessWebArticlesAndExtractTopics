from pymongo import MongoClient

# Verbindung zur MongoDB herstellen
client = MongoClient('mongodb://localhost:27017/')
db = client['scrapy_database']

# Liste der Kollektionen, die verglichen werden sollen
collection_names = [ 'AntifaBlattVocab', 'AI2Vocab', 'imVoc_ge', 'RechteRandVocab', 'schweizerZeitVocab',
                     'sezessionVocab', 'BNVocab'
]  # Ersetze mit den tatsächlichen Namen der Kollektionen

# Wörterbuch zur Speicherung von Wörtern und ihren Herkunftskollektionen
word_occurrences = {}

# Durch alle Kollektionen iterieren und Wörter extrahieren
for collection_name in collection_names:
    collection = db[collection_name]
    words = set(doc['word'] for doc in collection.find({}, {'word': 1}))

    for word in words:
        if word in word_occurrences:
            word_occurrences[word].append(collection_name)
        else:
            word_occurrences[word] = [collection_name]

# Filtere nur Wörter, die in mehreren Kollektionen vorkommen
common_words = {word: sources for word, sources in word_occurrences.items() if len(sources) > 0}

# Speichere die gemeinsamen Wörter in einer Textdatei
output_filename = "gemeinsame_woerter.txt"

with open(output_filename, "w", encoding="utf-8") as f:
    f.write("Gemeinsame Wörter in mehreren Kollektionen:\n")
    f.write("=" * 50 + "\n")
    for word, sources in common_words.items():
        f.write(f"{word}: {', '.join(sources)}\n")

print(f"Ergebnisse wurden in '{output_filename}' gespeichert.")
