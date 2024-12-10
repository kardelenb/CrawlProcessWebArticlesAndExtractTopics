from pymongo import MongoClient
from collections import Counter

# Verbindung zur MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['scrapy_database']
collection = db['test2710']

# Shingle-Größe und Häufigkeitsschwelle
n = 10  # Lange Shingles zur Identifikation von wiederholten Textblöcken
threshold_percentage = 0.1  # Schwelle für Wiederholung in der Sammlung (10%)


def generate_shingles(text, n):
    """
    Erzeugt n-Gramm-Shingles aus einem Text.
    """
    words = text.split()
    shingles = [' '.join(words[i:i + n]) for i in range(len(words) - n + 1)]
    return shingles


def find_common_shingles(sample_texts, threshold_percentage):
    """
    Findet häufig vorkommende Shingles, die in einer Vielzahl von Texten erscheinen.

    Parameters:
    - sample_texts: Liste aller Textinhalte.
    - threshold_percentage: Der Prozentsatz der Texte, in denen ein Shingle vorkommen muss, um als häufig zu gelten.

    Returns:
    - common_shingles: Liste der häufigen Shingles.
    """
    shingle_counter = Counter()
    num_texts = len(sample_texts)

    # Erzeuge und zähle Shingles in allen Texten
    for text in sample_texts:
        shingles = set(generate_shingles(text, n=n))  # set() zur Vermeidung von Duplikaten innerhalb eines Textes
        shingle_counter.update(shingles)

    # Wähle Shingles aus, die in mindestens threshold_percentage der Texte vorkommen
    threshold = int(threshold_percentage * num_texts)
    common_shingles = [shingle for shingle, count in shingle_counter.items() if count >= threshold]
    return common_shingles


def remove_common_shingles(text, common_shingles):
    """
    Entfernt die häufigen, langen Shingles aus dem Text.
    """
    for shingle in common_shingles:
        text = text.replace(shingle, '')
    return text


def process_and_clean_articles():
    """
    Verarbeitet Artikel und entfernt häufige lange Textsegmente.
    """
    # Sammle alle Texte aus der Sammlung
    sample_texts = [article['full_text'] for article in collection.find()]

    # Identifiziere häufig vorkommende Shingles
    common_shingles = find_common_shingles(sample_texts, threshold_percentage)
    print("Gefundene häufige Shingles:", common_shingles)

    # Entferne diese Shingles aus den Artikeln und speichere die bereinigten Texte
    for article in collection.find():
        original_text = article['full_text']
        cleaned_text = remove_common_shingles(original_text, common_shingles)

        # Aktualisiere den Artikel mit dem bereinigten Text
        collection.update_one(
            {'_id': article['_id']},
            {'$set': {'cleaned_text': cleaned_text}}
        )
        print(f"Bereinigter Artikel gespeichert: {article['url']}")


# Starte die Verarbeitung
process_and_clean_articles()
