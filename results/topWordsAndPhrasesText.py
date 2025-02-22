from pymongo import MongoClient

# Verbindung zur MongoDB herstellen
client = MongoClient('mongodb://localhost:27017/')
db = client['scrapy_database']

# Funktion zur Analyse der häufigsten Wörter und Phrasen
def analyze_top_items_text_output(collection_name, top_n=100):
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
                article_phrases[word] = article_count
            if comment_count > 0:
                comment_phrases[word] = comment_count
        else:  # Wörter enthalten keine Leerzeichen
            if article_count > 0:
                article_words[word] = article_count
            if comment_count > 0:
                comment_words[word] = comment_count

    # Sortiere und wähle die Top-N-Einträge aus
    top_article_words = sorted(article_words.items(), key=lambda x: x[1], reverse=True)[:top_n]
    top_article_phrases = sorted(article_phrases.items(), key=lambda x: x[1], reverse=True)[:top_n]
    top_comment_words = sorted(comment_words.items(), key=lambda x: x[1], reverse=True)[:top_n]
    top_comment_phrases = sorted(comment_phrases.items(), key=lambda x: x[1], reverse=True)[:top_n]

    return top_article_words, top_article_phrases, top_comment_words, top_comment_phrases

# Top 100 extrahieren
# Ersetze mit den tatsächlichen Namen der Kollektionen
top_article_words, top_article_phrases, top_comment_words, top_comment_phrases = analyze_top_items_text_output('imVoc_en')

# Ergebnisse in Textform ausgeben
def output_to_text(filename, data, title):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"{title}\n")
        f.write("=" * len(title) + "\n")
        for rank, (item, count) in enumerate(data, start=1):
            f.write(f"{rank}. {item} ({count} Vorkommen)\n")
        print(f"Ergebnisse in '{filename}' gespeichert.")

# Ausgabe der Ergebnisse in Dateien
output_to_text("top_article_words.txt", top_article_words, "Top 100 Schlüsselwörter in Artikeln")
output_to_text("top_article_phrases.txt", top_article_phrases, "Top 100 Schlüsselphrasen in Artikeln")
output_to_text("top_comment_words.txt", top_comment_words, "Top 100 Schlüsselwörter in Kommentaren")
output_to_text("top_comment_phrases.txt", top_comment_phrases, "Top 100 Schlüsselphrasen in Kommentaren")
