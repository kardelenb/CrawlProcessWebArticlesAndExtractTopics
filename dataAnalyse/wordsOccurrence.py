from pymongo import MongoClient
import re

# Verbindung zur MongoDB herstellen
client = MongoClient('mongodb://localhost:27017/')
db = client['scrapy_database']
# Ersetze mit den tatsächlichen Namen der Kollektionen
collection = db['sezessionProcessed']

def find_texts_containing_partial_word(partial_word):
    # Unscharfer Regex-Ausdruck, um das Wort als Teil eines längeren Textes zu suchen
    regex = re.compile(rf"{re.escape(partial_word)}", re.IGNORECASE)
    results = collection.find({
        "$or": [
            {"full_text": regex},  # Suche im Artikeltext nach Teilworten
            {"new_comment_phrases": {"$elemMatch": {"$regex": regex}}}  # Suche in den Kommentarphrasen
        ]
    })

    # Ausgabe der Ergebnisse
    found = False
    for result in results:
        found = True
        print("Artikel gefunden:")
        print(f"URL: {result.get('url', 'Keine URL')}")
        print(f"Title: {result.get('title', 'Kein Titel')}")

        # Gebe den Artikeltext aus, wenn das Teilwort darin vorkommt
        if regex.search(result.get("full_text", "")):
            print("Textinhalt:")
            print(result.get("full_text"))

        # Gebe die Kommentarphrasen aus, falls das Teilwort dort vorkommt
        comment_phrases = result.get("new_comment_phrases", [])
        relevant_phrases = [phrase for phrase in comment_phrases if regex.search(phrase)]
        if relevant_phrases:
            print("\nRelevante Kommentar-Phrasen:")
            for phrase in relevant_phrases:
                print(f"- {phrase}")

        print("\n" + "-" * 80 + "\n")

    if not found:
        print(f"Kein Artikel oder Kommentar mit dem Wort '{partial_word}' gefunden.")

# Eingabeaufforderung für das Teilwort
word_to_search = input("Geben Sie das Teilwort ein, nach dem gesucht werden soll: ")
find_texts_containing_partial_word(word_to_search)
