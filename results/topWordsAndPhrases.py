from pymongo import MongoClient
import matplotlib.pyplot as plt
import os

# Verbindung zur MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['scrapy_database']

# Funktion zur Analyse der häufigsten Wörter und Phrasen
def analyze_top_items(collection_name, top_n=30):
    collection = db[collection_name]
    article_words = {}
    article_phrases = {}
    comment_words = {}
    comment_phrases = {}

    # Daten aus der Kollektion abrufen
    for entry in collection.find():
        word = entry['word']
        article_count = entry.get('article_occurrences', 0)
        comment_count = entry.get('comment_occurrences', 0)

        # Trennung zwischen Wörtern und Phrasen
        if " " in word:  # Phrasen enthalten Leerzeichen
            if article_count > 0:
                article_phrases[word] = article_phrases.get(word, 0) + article_count
            if comment_count > 0:
                comment_phrases[word] = comment_phrases.get(word, 0) + comment_count
        else:  # Wörter enthalten keine Leerzeichen
            if article_count > 0:
                article_words[word] = article_words.get(word, 0) + article_count
            if comment_count > 0:
                comment_words[word] = comment_words.get(word, 0) + comment_count

    # Sortiere und wähle die Top-N-Einträge aus
    top_article_words = sorted(article_words.items(), key=lambda x: x[1], reverse=True)[:top_n]
    top_article_phrases = sorted(article_phrases.items(), key=lambda x: x[1], reverse=True)[:top_n]
    top_comment_words = sorted(comment_words.items(), key=lambda x: x[1], reverse=True)[:top_n]
    top_comment_phrases = sorted(comment_phrases.items(), key=lambda x: x[1], reverse=True)[:top_n]

    return top_article_words, top_article_phrases, top_comment_words, top_comment_phrases

# Funktion zur Visualisierung der Ergebnisse
def plot_top_items(data, title, ylabel, output_file, color):
    items = [item[0] for item in data]
    counts = [item[1] for item in data]

    plt.figure(figsize=(12, 8))
    plt.barh(items, counts, color=color)
    plt.xlabel('Anzahl der Vorkommen in Artikeln')
    plt.ylabel(ylabel)
    plt.title(title)
    plt.gca().invert_yaxis()
    plt.tight_layout()

    os.makedirs('output', exist_ok=True)
    plt.savefig(f'output/{output_file}')
    print(f'Diagramm gespeichert: output/{output_file}')
    plt.close()

# Analyse der häufigsten Wörter und Phrasen ohne Filter
# Ersetze mit den tatsächlichen Namen der Kollektionen
(top_article_words, top_article_phrases, top_comment_words, top_comment_phrases) = analyze_top_items(
    'schweizerZeitVocab'
)

# Ergebnisse visualisieren mit unterschiedlichen Farben
plot_top_items(top_article_words, "Top 30 häufigste englische Schlüsselwörter in Artikeln", "Schlüsselwörter",
               "imen_top_article_words.png", "#1f77b4")  # Dunkelblau
plot_top_items(top_article_phrases, "Top 30 häufigste englische Schlüsselphrasen in Artikeln", "Schlüsselphrasen",
               "imen_top_article_phrases.png", "#ff7f0e")  # Orange
plot_top_items(top_comment_words, "Top 30 häufigste englische Schlüsselwörter in Kommentaren", "Schlüsselwörter",
               "imen_top_comment_words.png", "#2ca02c")  # Dunkelgrün
plot_top_items(top_comment_phrases, "Top 30 häufigste englische Schlüsselphrasen in Kommentaren", "Schlüsselphrasen",
               "imen_top_comment_phrases.png", "#d62728")  # Rot
