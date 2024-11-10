import spacy
from pymongo import MongoClient
import matplotlib.pyplot as plt
from collections import Counter
import os
import textwrap

# Lade die deutschen und englischen spaCy-Modelle mit NER-Funktionalität
nlp_de = spacy.load('de_core_news_sm')
nlp_en = spacy.load('en_core_web_sm')

# Verbindung zur MongoDB herstellen
client = MongoClient('mongodb://localhost:27017/')
db = client['scrapy_database']
vocabulary_collection = db['AI2Vocab']

# Lade die Blacklist aus einer Textdatei
def load_blacklist(filepath='blacklist_AINet.txt'):
    with open(filepath, 'r', encoding='utf-8') as f:
       return set(line.strip().lower() for line in f)

# Blacklist laden
blacklist = load_blacklist()

'''
# Funktion zur Identifizierung und Filterung von Namen
def apply_ner_filter(phrases, language='de'):
    if language == 'de':
        doc = nlp_de(" ".join(phrases))
    else:
        doc = nlp_en(" ".join(phrases))

    # Entitäten nach Typ sammeln
    excluded_phrases = set(ent.text for ent in doc.ents if ent.label_ in {'PER', 'LOC', 'ORG'})

    # Filtere alle Namen und Orte aus den Phrasen heraus
    filtered_phrases = [phrase for phrase in phrases if phrase not in excluded_phrases]
    return filtered_phrases
'''

# Funktion zur Analyse und Visualisierung der Top-20-Wörter und -Phrasen ohne Blacklist-Begriffe
def analyze_and_plot_top_20_excluding_names():
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
        if word in blacklist:
            continue

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
    top_article_words = sorted(article_words_counts, key=article_words_counts.get, reverse=True)[:20]
    top_article_phrases = sorted(article_phrases_counts, key=article_phrases_counts.get, reverse=True)[:20]
    top_comment_words = sorted(comment_words_counts, key=comment_words_counts.get, reverse=True)[:20]
    top_comment_phrases = sorted(comment_phrases_counts, key=comment_phrases_counts.get, reverse=True)[:20]

    # Wrap labels for readability
    def wrap_labels(labels, width=25):
        return ["\n".join(textwrap.wrap(label, width)) for label in labels]

    wrapped_article_words = wrap_labels(top_article_words)
    wrapped_article_phrases = wrap_labels(top_article_phrases)
    wrapped_comment_words = wrap_labels(top_comment_words)
    wrapped_comment_phrases = wrap_labels(top_comment_phrases)

    output_dir = './output/'
    os.makedirs(output_dir, exist_ok=True)

    # Plot for Article Words
    plt.figure(figsize=(14, 10))
    plt.barh(wrapped_article_words, [article_words_counts[word] for word in top_article_words], color='skyblue')
    plt.xlabel("Häufigkeit")
    plt.title("Top 20 häufigste Wörter in Artikeln")
    plt.gca().invert_yaxis()
    plt.xticks(fontsize=10)
    plt.yticks(fontsize=9)
    plt.savefig(os.path.join(output_dir, 'AItop_article_words.png'), bbox_inches='tight')
    plt.close()

    # Plot for Article Phrases
    plt.figure(figsize=(14, 10))
    plt.barh(wrapped_article_phrases, [article_phrases_counts[phrase] for phrase in top_article_phrases],
             color='salmon')
    plt.xlabel("Häufigkeit")
    plt.title("Top 20 häufigste Phrasen in Artikeln")
    plt.gca().invert_yaxis()
    plt.xticks(fontsize=10)
    plt.yticks(fontsize=9)
    plt.savefig(os.path.join(output_dir, 'AItop_article_phrases.png'), bbox_inches='tight')
    plt.close()

    # Plot for Comment Words
    plt.figure(figsize=(14, 10))
    plt.barh(wrapped_comment_words, [comment_words_counts[word] for word in top_comment_words], color='lightgreen')
    plt.xlabel("Häufigkeit")
    plt.title("Top 20 häufigste Wörter in Kommentaren")
    plt.gca().invert_yaxis()
    plt.xticks(fontsize=10)
    plt.yticks(fontsize=9)
    plt.savefig(os.path.join(output_dir, 'AItop_comment_words.png'), bbox_inches='tight')
    plt.close()

    # Plot for Comment Phrases
    plt.figure(figsize=(14, 10))
    plt.barh(wrapped_comment_phrases, [comment_phrases_counts[phrase] for phrase in top_comment_phrases],
             color='lightcoral')
    plt.xlabel("Häufigkeit")
    plt.title("Top 20 häufigste Phrasen in Kommentaren")
    plt.gca().invert_yaxis()
    plt.xticks(fontsize=10)
    plt.yticks(fontsize=9)
    plt.savefig(os.path.join(output_dir, 'AItop_comment_phrases.png'), bbox_inches='tight')
    plt.close()


# Aufruf der Analyse- und Plot-Funktion
analyze_and_plot_top_20_excluding_names()