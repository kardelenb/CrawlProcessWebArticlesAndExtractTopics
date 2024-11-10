import spacy
from pymongo import MongoClient

# Lade die deutschen und englischen spaCy-Modelle
nlp_de = spacy.load('de_core_news_sm')
nlp_en = spacy.load('en_core_web_sm')

# Verbindung zu MongoDB herstellen
client = MongoClient('mongodb://localhost:27017/')
db = client['scrapy_database']
vocabulary_collection = db['test0311_vocabulary']

#Lade die Blacklist aus einer Textdatei
#def load_blacklist(filepath='blacklist_AINet.txt'):
#    with open(filepath, 'r', encoding='utf-8') as f:
#        return set(line.strip().lower() for line in f)

#Blacklist laden
#blacklist = load_blacklist()

# Funktion zur Analyse der Top-20-Wörter und -Phrasen ohne Namen
def analyze_top_20_excluding_names():
    # Wörter und Phrasen in Artikeln und Kommentaren
    article_words_counts = {}
    article_phrases_counts = {}
    comment_words_counts = {}
    comment_phrases_counts = {}

    # Zähle die Vorkommen in Artikeln und Kommentaren
    for entry in vocabulary_collection.find():
        word = entry['word'].lower()  # Kleinbuchstaben für Konsistenz bei Blacklist-Überprüfung
        article_occurrences = entry.get('article_occurrences', 0)
        comment_occurrences = entry.get('comment_occurrences', 0)

        # Wende die Blacklist an
        #if word in blacklist:
            #continue

        # Einfache Wörter oder Mehrwortphrasen trennen
        if " " in word:  # Phrasen haben Leerzeichen
            if article_occurrences > 0:
                article_phrases_counts[word] = article_occurrences
            if comment_occurrences > 0:
                comment_phrases_counts[word] = comment_occurrences
        else:  # Einfache Wörter
            if article_occurrences > 0:
                article_words_counts[word] = article_occurrences
            if comment_occurrences > 0:
                comment_words_counts[word] = comment_occurrences

    # Sortiere nach Häufigkeit
    top_article_words = sorted(article_words_counts, key=article_words_counts.get, reverse=True)[:100]
    top_article_phrases = sorted(article_phrases_counts, key=article_phrases_counts.get, reverse=True)[:100]
    top_comment_words = sorted(comment_words_counts, key=comment_words_counts.get, reverse=True)[:100]
    top_comment_phrases = sorted(comment_phrases_counts, key=comment_phrases_counts.get, reverse=True)[:100]

    # Zeige die Top-20 gefilterten Ergebnisse
    print("Top 20 häufigste Wörter in Artikeln (ohne Blacklist-Begriffe):")
    for word in top_article_words[:20]:
        print(f"{word}: {article_words_counts.get(word, 'Häufigkeit nicht gefunden')}")

    print("\nTop 20 häufigste Phrasen in Artikeln (ohne Blacklist-Begriffe):")
    for phrase in top_article_phrases[:20]:
        print(f"{phrase}: {article_phrases_counts.get(phrase, 'Häufigkeit nicht gefunden')}")

    print("\nTop 20 häufigste Wörter in Kommentaren (ohne Blacklist-Begriffe):")
    for word in top_comment_words[:20]:
        print(f"{word}: {comment_words_counts.get(word, 'Häufigkeit nicht gefunden')}")

    print("\nTop 20 häufigste Phrasen in Kommentaren (ohne Blacklist-Begriffe):")
    for phrase in top_comment_phrases[:20]:
        print(f"{phrase}: {comment_phrases_counts.get(phrase, 'Häufigkeit nicht gefunden')}")

# Aufruf der Analysefunktion
analyze_top_20_excluding_names()
