import spacy
from germanetpy import germanet
from germanetpy.filterconfig import Filterconfig
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.corpus import stopwords, wordnet
import nltk
import re
from pymongo import MongoClient, errors
from datetime import datetime
import logging
import os

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.getLogger('pymongo').setLevel(logging.WARNING)

# Verbindung zur MongoDB und Zugriff auf gespeicherte Artikel
client = MongoClient('mongodb://localhost:27017/')
db = client['scrapy_database']
collection = db['rechterand0510raw']
processed_collection = db['testprocessed']
vocabulary_collection = db['testvocabulary']
daily_summary_collection = db['test_daily']

# Neue Sammlung, um den Fortschritt zu speichern
progress_collection = db['testprocess_progress']

processed_collection.create_index('url')

# Lade deutsche und englische spaCy-Modelle
nlp_de = spacy.load('de_core_news_sm')
nlp_en = spacy.load('en_core_web_sm')

nltk.download('stopwords')
nltk.download('wordnet')

german_stop_words = set(stopwords.words('german'))
english_stop_words = set(stopwords.words('english'))
# Lade GermaNet-Daten
germanet_object = germanet.Germanet("/home/kardelenbilir/Downloads/GN_V180/GN_V180_XML")
# Bestimme das aktuelle Verzeichnis, in dem das Skript ausgeführt wird
current_directory = os.path.dirname(os.path.abspath(__file__))

# Gehe drei Verzeichnisebenen nach oben, um das Verzeichnis 'MASterarbeit' zu erreichen
project_directory = os.path.abspath(os.path.join(current_directory, '..', '..', '..'))

# Lese die Referenzdatei ein (bereinigte Datei)
def read_reference_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        reference_words = [line.strip().lower() for line in f]
    return reference_words


# Funktion, um zu prüfen, ob ein Wort in GermaNet ist, unabhängig von Groß-/Kleinschreibung
def check_word_in_germanet_ignore_case(word):
    # Erstelle eine Filterkonfiguration und ignoriere Groß- und Kleinschreibung
    filterconfig = Filterconfig(word, ignore_case=True)
    synsets = filterconfig.filter_synsets(germanet_object)

    return len(synsets) > 0

# Korrigierte Funktion, um Phrasen zu extrahieren, bei denen die Wörter direkt aufeinander folgen
def extract_phrases_with_noun_as_second(doc, pos_tags=['NOUN'], preceding_tags=['ADJ', 'VERB'], n=2):
    phrases = []
    only_letters = re.compile(r'^[^\W\d_]+$')

    # Hier werden nur Tokens betrachtet, die keine Stopwords sind und alphabetisch sind
    tokens = [token for token in doc if not token.is_stop and only_letters.match(token.text)]

    # Sliding-Window über die Token-Liste, um N-Gramme zu erstellen
    for i in range(len(tokens) - n + 1):
        gram = tokens[i:i + n]

        # Prüfe, ob das zweite Wort ein Substantiv ist und das erste Wort ein Adjektiv oder Verb ist
        # Zusätzlich sicherstellen, dass die Token direkt hintereinander im Originaltext stehen
        if gram[1].pos_ in pos_tags and gram[0].pos_ in preceding_tags:
            # Stelle sicher, dass die Phrasen aufeinanderfolgend im Originaltext vorkommen
            if tokens[i+1].idx == tokens[i].idx + len(tokens[i].text_with_ws):
                phrase = ' '.join([token.text for token in gram])
                phrases.append(phrase)

    return phrases


def extract_keywords_and_phrases(text, language, pos_tags=['NOUN', 'ADJ', 'VERB'], n=2):
    if language == 'de':
        doc = nlp_de(text)
    else:
        doc = nlp_en(text)

    # Einfache Wort-Extraktion (wie zuvor)
    single_keywords = [
        token.text
        for token in doc
        if token.pos_ in pos_tags
           and not token.is_stop
           and re.match(r'^[^\W\d_]+$', token.text)  # Nur alphabetische Wörter
    ]

    # Mehrwortphrasen (z.B. N-Gramme) extrahieren, bei denen das zweite Wort ein Nomen ist
    phrases = extract_phrases_with_noun_as_second(doc, pos_tags=['NOUN'], preceding_tags=['ADJ', 'VERB'], n=n)

    return single_keywords + phrases


# Bestimmt die Sprache eines Textes
def detect_language(text):
    if any(word in german_stop_words for word in text.split()):
        return 'de'
    return 'en'

# Vergleicht die extrahierten Wörter mit der Referenzdatei
# Funktion zum Vergleich der extrahierten Phrasen/Wörter mit dem Wörterbuch
# Vergleicht die extrahierten Wörter mit der Referenzdatei und GermaNet
def compare_phrases_with_reference(new_phrases, reference_words):
    reference_set = set(reference_words)
    updated_new_phrases = []

    for phrase in new_phrases:
        words_in_phrase = phrase.lower().split()  # Zerlege die Phrase in einzelne Wörter und prüfe jedes Wort
        if not all(word in reference_set for word in words_in_phrase):
            # Prüfe, ob das Wort in GermaNet ist (case-insensitive)
            if not check_word_in_germanet_ignore_case(phrase):
                updated_new_phrases.append(
                    phrase)  # Nur hinzufügen, wenn es nicht in der Referenzdatei und nicht in GermaNet ist

    return updated_new_phrases

# Aktualisiert das Vokabular, um sowohl Wörter als auch Phrasen zu speichern
def update_vocabulary(phrase, current_date, source, all_vocabulary_today):
    """
    Aktualisiert das Vokabular, um sowohl Wörter als auch Phrasen zu speichern.
    'source' gibt an, ob die Phrase aus einem Artikel oder einem Kommentar stammt.
    """
    existing_phrase = vocabulary_collection.find_one({'word': phrase})

    # Bestimme das Feld basierend auf der Quelle (Artikel oder Kommentar)
    if source == 'article':
        field = 'article_occurrences'
    else:
        field = 'comment_occurrences'

    if existing_phrase:
        # Wenn das Wort bereits existiert, aktualisiere das Vorkommen
        vocabulary_collection.update_one(
            {'word': phrase},
            {
                '$inc': {field: 1},  # Inkrementiere die Häufigkeit im richtigen Feld
                '$set': {'last_seen': current_date}
            }
        )
        all_vocabulary_today['existing_phrases'].add(phrase)
    else:
        # Wenn das Wort noch nicht existiert, füge es neu hinzu
        vocabulary_collection.insert_one({
            'word': phrase,
            'first_seen': current_date,
            'last_seen': current_date,
            'article_occurrences': 1 if source == 'article' else 0,
            'comment_occurrences': 1 if source == 'comment' else 0
        })
        all_vocabulary_today['new_phrases'].add(phrase)


# Speichert die tägliche Zusammenfassung
# Speichert die tägliche Zusammenfassung
def save_daily_summary(new_article_phrases, new_comment_phrases, current_date):
    # Berechne die Häufigkeit der neuen Wörter für den Tag
    article_word_frequencies = {}
    comment_word_frequencies = {}

    # Zähle die Häufigkeit der Wörter in Artikeln
    for word in new_article_phrases:
        if word in article_word_frequencies:
            article_word_frequencies[word] += 1
        else:
            article_word_frequencies[word] = 1

    # Zähle die Häufigkeit der Wörter in Kommentaren
    for word in new_comment_phrases:
        if word in comment_word_frequencies:
            comment_word_frequencies[word] += 1
        else:
            comment_word_frequencies[word] = 1

        # Liste der bisher gesehenen Wörter (gesamtes Vokabular)
        all_seen_words = set(vocabulary_collection.distinct('word'))

        # Unterscheide zwischen neuen und bereits gesehenen Wörtern
        new_words_today = [word for word in new_article_phrases + new_comment_phrases if word not in all_seen_words]
        repeated_words_today = [word for word in new_article_phrases + new_comment_phrases if word in all_seen_words]

        # Speichere die tägliche Zusammenfassung, inklusive neuer und wiederholter Wörter
        daily_summary_collection.insert_one({
            'date': current_date,
            'article_word_frequencies': article_word_frequencies,
            'comment_word_frequencies': comment_word_frequencies,
            'new_words_today': new_words_today,
            'repeated_words_today': repeated_words_today,
            'new_word_count': len(new_words_today),
            'repeated_word_count': len(repeated_words_today)
        })
        # Füge dies hinzu: Speichere das Vokabelwachstum separat
        vocabulary_growth_collection = db[
            'vocabulary_growth']  # Erstelle oder referenziere eine Sammlung für das Vokabelwachstum
        vocabulary_growth_collection.insert_one({
            'date': current_date,
            'new_words_count': len(new_words_today),  # Anzahl der neuen Wörter an diesem Tag
            'repeated_words_count': len(repeated_words_today)  # Anzahl der wiederholten Wörter an diesem Tag
        })



# Speichert den Fortschritt
def save_progress(last_processed_id):
    progress_collection.update_one({}, {'$set': {'last_processed_id': last_processed_id}}, upsert=True)

# Holt den Fortschritt
def get_last_processed_id():
    progress = progress_collection.find_one()
    return progress['last_processed_id'] if progress else None

# Verarbeitet Artikel
def process_articles():
    reference_file_path = os.path.join(project_directory, 'output3.txt')
    reference_words = read_reference_file(reference_file_path)
    current_date = datetime.now().strftime('%Y-%m-%d')

    all_vocabulary_today = {
        'new_phrases': set(),  # Neue Wörter/Phrasen, die heute zum ersten Mal gesehen wurden
        'existing_phrases': set()  # Bereits bekannte Wörter/Phrasen, die erneut aufgetreten sind
    }
    processed_articles = 0

    # Hole die zuletzt verarbeitete ID
    last_processed_id = get_last_processed_id()

    query = {}
    if last_processed_id:
        query = {'_id': {'$gt': last_processed_id}}

    try:
        with client.start_session() as session:
            cursor = collection.find(query, no_cursor_timeout=True, session=session).batch_size(100)

            try:
                for article in cursor:
                    full_text = article['full_text']
                    comments = article.get('comments', [])  # Hole die Kommentare oder setze sie als leere Liste
                    language = detect_language(full_text)

                    # Extrahiere Phrasen aus dem Artikeltext
                    filtered_article_phrases = extract_keywords_and_phrases(full_text, language, n=2)

                    # Extrahiere Phrasen aus den Kommentaren (falls vorhanden)
                    filtered_comment_phrases = []
                    if comments:
                        for comment in comments:
                            filtered_comment_phrases.extend(extract_keywords_and_phrases(comment, language, n=2))

                    # Falls der Artikel nur Stopwords oder keinen Text enthält
                    if not filtered_article_phrases and not filtered_comment_phrases:
                        logging.warning(f"Artikel {article['url']} enthält nur Stopwords oder ist leer. Überspringe.")
                        continue

                    # Füge die WordNet-Überprüfung für englische Wörter hinzu
                    new_article_phrases = []
                    new_comment_phrases = []

                    # Überprüfe Artikel-Phrasen mit WordNet für englische Wörter
                    for phrase in filtered_article_phrases:
                        if language == 'en' and any(wordnet.synsets(word) for word in phrase.split()):
                            continue  # Überspringe englische Wörter/Phrasen, die in WordNet definiert sind
                        new_article_phrases.append(phrase)

                    # Überprüfe Kommentar-Phrasen mit WordNet für englische Wörter
                    for phrase in filtered_comment_phrases:
                        if language == 'en' and any(wordnet.synsets(word) for word in phrase.split()):
                            continue  # Überspringe englische Wörter/Phrasen, die in WordNet definiert sind
                        new_comment_phrases.append(phrase)

                    # Vergleiche die übriggebliebenen Phrasen mit der Referenzdatei
                    new_article_phrases = compare_phrases_with_reference(new_article_phrases, reference_words)
                    new_comment_phrases = compare_phrases_with_reference(new_comment_phrases, reference_words)

                    # Falls keine neuen Phrasen vorhanden sind, Artikel trotzdem speichern
                    if not new_article_phrases and not new_comment_phrases:
                        logging.info(f"Keine neuen Wörter oder Phrasen in Artikel {article['url']}.")
                        processed_collection.insert_one({
                            'title': article['title'],
                            'url': article['url'],
                            'full_text': full_text,
                            'ranked_keywords': [],  # Keine neuen Phrasen
                            'new_article_phrases': [],  # Keine neuen Phrasen
                            'new_comment_phrases': [],  # Keine neuen Phrasen
                            'first_processed': current_date,
                            'last_processed': current_date
                        })
                        continue

                    # Aktualisiere das Vokabular für neue Phrasen im Artikeltext
                    for phrase in new_article_phrases:
                        update_vocabulary(phrase, current_date, 'article', all_vocabulary_today)  # Speichere als Artikelphrase

                    # Aktualisiere das Vokabular für neue Phrasen in den Kommentaren (falls vorhanden)
                    for phrase in new_comment_phrases:
                        update_vocabulary(phrase, current_date, 'comment', all_vocabulary_today)  # Speichere als Kommentarphrase

                    # Berechne TF-IDF (optional, falls benötigt)
                    try:
                        all_phrases = new_article_phrases + new_comment_phrases
                        if all_phrases:
                            vectorizer = TfidfVectorizer(lowercase=False, ngram_range=(1, 2))
                            tfidf_matrix = vectorizer.fit_transform([' '.join(all_phrases)])
                            tfidf_scores = zip(vectorizer.get_feature_names_out(), tfidf_matrix.toarray()[0])
                            ranked_keywords = sorted(tfidf_scores, key=lambda x: x[1], reverse=True)
                        else:
                            ranked_keywords = []
                    except Exception as e:
                        logging.error(f"Fehler beim Berechnen der TF-IDF für Artikel {article['url']}: {e}")
                        continue

                    # Speichere die neuen Phrasen und Kommentare in der Datenbank
                    processed_collection.insert_one({
                        'title': article['title'],
                        'url': article['url'],
                        'full_text': full_text,
                        'ranked_keywords': [{'word': word, 'score': score} for word, score in ranked_keywords],
                        'new_article_phrases': new_article_phrases,  # Neue Phrasen aus dem Artikeltext
                        'new_comment_phrases': new_comment_phrases,  # Neue Phrasen aus den Kommentaren (falls vorhanden)
                        'first_processed': current_date,
                        'last_processed': current_date
                    })

                    processed_articles += 1
                    logging.info(f"Neuer Artikel verarbeitet: {processed_articles}")

                    # Speichere den Fortschritt nach jedem Artikel
                    save_progress(article['_id'])

            except errors.CursorNotFound as e:
                logging.error(f"CursorNotFound-Fehler: {e}")
                process_articles()  # Rekursiver Neustart

            finally:
                cursor.close()

    except Exception as e:
        logging.error(f"Fehler beim Starten der MongoDB-Sitzung: {e}")

    save_daily_summary(list(all_vocabulary_today['new_phrases']), list(all_vocabulary_today['existing_phrases']), current_date)




if __name__ == '__main__':
    process_articles()
