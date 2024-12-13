from pymongo import MongoClient
from collections import Counter
import re

# Verbindung zur MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['scrapy_database']
collection = db['test2710']


def split_into_sentences(text):
    """
    Teilt den Text in Sätze auf.
    """
    sentences = re.split(r'(?<=[.!?]) +', text)
    return sentences


def create_text_profile(text, top_n=10):
    """
    Erstellt ein Textprofil, indem die häufigsten Sätze extrahiert werden.
    """
    sentences = split_into_sentences(text)
    sentence_counter = Counter(sentences)

    # Auswahl der häufigsten Sätze
    most_common_sentences = sentence_counter.most_common(top_n)
    profile = [sentence for sentence, _ in most_common_sentences]

    return profile


def generate_profiles():
    """
    Generiert und speichert Textprofile für alle Artikel in der Sammlung.
    """
    for article in collection.find():
        full_text = article['full_text']
        profile = create_text_profile(full_text)

        # Speichern des Profils in der Datenbank
        collection.update_one(
            {'_id': article['_id']},
            {'$set': {'text_profile': profile}}
        )
        print(f"Profil erstellt für Artikel: {article['url']}")


generate_profiles()


def compare_profiles():
    """
    Vergleicht die Textprofile der Artikel, um generische Sätze zu identifizieren.
    """
    # Lade alle Profile
    profiles = [article['text_profile'] for article in collection.find()]

    # Berechne die Häufigkeit jedes Satzes in allen Profilen
    sentence_counter = Counter()
    for profile in profiles:
        sentence_counter.update(profile)

    # Wähle generische Sätze aus, die in mehreren Artikeln vorkommen
    threshold = 5  # Setze eine Schwelle für die Häufigkeit
    generic_sentences = [sentence for sentence, count in sentence_counter.items() if count >= threshold]

    print("Generische Sätze:", generic_sentences)
    return generic_sentences


generic_sentences = compare_profiles()
