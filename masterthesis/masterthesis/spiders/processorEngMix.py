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
collection = db['indyMedia']

processed_collection_de = db['imProcessedGe']
processed_collection_en = db['imProcessedEn']
vocabulary_collection_de = db['imVoc_ge']
vocabulary_collection_en = db['imVoc_en']
daily_summary_collection_de = db['imDailyGe']
daily_summary_collection_en = db['imDailyEn']
progress_collection_de = db['im_progressGe']
progress_collection_en = db['im_progressEn']

vocabulary_growth_collection_de = db['im_growth_ge']
vocabulary_growth_collection_en = db['im_growth_en']
# Neue Sammlung, um den Fortschritt zu speichern
#progress_collection = db['RRprocess_progress']

processed_collection_de.create_index('url')
processed_collection_en.create_index('url')

# Lege das Startdatum beim Start des Programms fest
start_date = datetime.now().strftime('%Y-%m-%d')
#start_date = '2024-10-24'

def detect_language(text):
    german_count = sum(1 for word in text.split() if word.lower() in german_stop_words)
    english_count = sum(1 for word in text.split() if word.lower() in english_stop_words)

    if german_count > english_count:
        return 'de'
    elif english_count > german_count:
        return 'en'
    else:
        return 'mixed'  # Wenn beide Sprachen ähnlich stark vertreten sind

# Speichert den Fortschritt
def save_progress(last_processed_id, progress_collection):
    progress_collection.update_one({}, {'$set': {'last_processed_id': last_processed_id}}, upsert=True)

# Holt den Fortschritt
def get_last_processed_id(progress_collection):
    progress = progress_collection.find_one()
    return progress['last_processed_id'] if progress else None

# Prüft, ob der Artikel bereits verarbeitet wurde
def article_already_processed(url, processed_collection):
    return processed_collection.find_one({'url': url}) is not None

# Holt alle Kommentare eines bereits gespeicherten Artikels
def get_stored_comments(url, processed_collection):
    article = processed_collection.find_one({'url': url}, {'comments': 1})
    if article:
        return set(article.get('comments', []))
    return set()

# Lade deutsche und englische spaCy-Modelle
nlp_de = spacy.load('de_core_news_sm')
nlp_en = spacy.load('en_core_web_sm')

nltk.download('stopwords')
nltk.download('wordnet')

german_stop_words = set(stopwords.words('german'))
english_stop_words = set(stopwords.words('english'))

# Bestimme das aktuelle Verzeichnis, in dem das Skript ausgeführt wird
current_directory = os.path.dirname(os.path.abspath(__file__))

# Gehe drei Verzeichnisebenen nach oben, um das Verzeichnis 'MASterarbeit' zu erreichen
project_directory = os.path.abspath(os.path.join(current_directory, '..', '..', '..'))

# Lese die Referenzdatei ein (bereinigte Datei)
def read_reference_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        reference_words = [line.strip().lower() for line in f]
    return reference_words

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

# Vergleicht die extrahierten Wörter mit der Referenzdatei
def compare_phrases_with_reference(new_phrases, reference_words):
    reference_set = set(reference_words)
    updated_new_phrases = []

    for phrase in new_phrases:
        words_in_phrase = phrase.lower().split()  # Zerlege die Phrase in einzelne Wörter und prüfe jedes Wort
        if not all(word in reference_set for word in words_in_phrase):
                updated_new_phrases.append(
                    phrase)  # Nur hinzufügen, wenn es nicht in der Referenzdatei und nicht in GermaNet ist

    return updated_new_phrases

# Aktualisiert das Vokabular, um sowohl Wörter als auch Phrasen zu speichern
def update_vocabulary(phrase, start_date, source, vocabulary_collection, all_vocabulary_today):
    existing_phrase = vocabulary_collection.find_one({'word': phrase})

    if source == 'article':
        field = 'article_occurrences'
    else:
        field = 'comment_occurrences'

    if existing_phrase:
        vocabulary_collection.update_one(
            {'word': phrase},
            {
                '$inc': {field: 1},
                '$set': {'last_seen': start_date}
            }
        )
        all_vocabulary_today['existing_phrases'].add(phrase)
    else:
        vocabulary_collection.insert_one({
            'word': phrase,
            'first_seen': start_date,
            'last_seen': start_date,
            'article_occurrences': 1 if source == 'article' else 0,
            'comment_occurrences': 1 if source == 'comment' else 0
        })
        all_vocabulary_today['new_phrases'].add(phrase)

# Speichert die tägliche Zusammenfassung (Eintrag wird nur einmal pro Tag erstellt oder aktualisiert)
def save_daily_summary(new_article_phrases, new_comment_phrases, start_date, daily_summary_collection, vocabulary_growth_collection, vocabulary_collection):
    article_word_frequencies = {}
    comment_word_frequencies = {}

    # Zähle die Häufigkeit der neuen Wörter in Artikeln
    for word in new_article_phrases:
        article_word_frequencies[word] = article_word_frequencies.get(word, 0) + 1

    # Zähle die Häufigkeit der neuen Wörter in Kommentaren
    for word in new_comment_phrases:
        comment_word_frequencies[word] = comment_word_frequencies.get(word, 0) + 1

    new_words_today = []
    repeated_words_today = []

    # Überprüfe, ob Wörter neu oder wiederholt sind, basierend auf der ersten Sichtung
    for word in new_article_phrases + new_comment_phrases:
        word_entry = vocabulary_collection.find_one({'word': word})  # Nutzung der korrekten Sprachsammlung (Deutsch oder Englisch)

        if word_entry and word_entry['first_seen'] == start_date:
            new_words_today.append(word)
        elif word_entry:
            repeated_words_today.append(word)

    # Prüfe, ob es bereits eine tägliche Zusammenfassung gibt
    existing_entry = daily_summary_collection.find_one({'date': start_date})

    if existing_entry:
        # Aktualisiere die bestehende tägliche Zusammenfassung
        daily_summary_collection.update_one(
            {'date': start_date},
            {
                '$set': {
                    'article_word_frequencies': {**existing_entry.get('article_word_frequencies', {}),
                                                 **article_word_frequencies},
                    'comment_word_frequencies': {**existing_entry.get('comment_word_frequencies', {}),
                                                 **comment_word_frequencies},
                    'new_words_today': list(set(existing_entry.get('new_words_today', []) + new_words_today)),
                    'repeated_words_today': list(
                        set(existing_entry.get('repeated_words_today', []) + repeated_words_today)),
                    'new_word_count': len(set(existing_entry.get('new_words_today', []) + new_words_today)),
                    'repeated_word_count': len(set(existing_entry.get('repeated_words_today', []) + repeated_words_today))
                }
            }
        )
    else:
        # Erstelle eine neue tägliche Zusammenfassung
        daily_summary_collection.insert_one({
            'date': start_date,
            'article_word_frequencies': article_word_frequencies,
            'comment_word_frequencies': comment_word_frequencies,
            'new_words_today': new_words_today,
            'repeated_words_today': repeated_words_today,
            'new_word_count': len(new_words_today),
            'repeated_word_count': len(repeated_words_today)
        })

    # Aktualisiere das Vokabelwachstum
    vocabulary_growth_collection.update_one(
        {'date': start_date},
        {
            '$set': {
                'new_words_count': len(new_words_today),
                'repeated_words_count': len(repeated_words_today)
            }
        },
        upsert=True
    )



def process_comments(comments, language, url, processed_collection):
    # Verarbeite neue Kommentare getrennt für jede Sprache
    stored_comments = get_stored_comments(url, processed_collection)
    new_comments = [comment for comment in comments if comment not in stored_comments]
    if new_comments:
        processed_collection.update_one(
            {'url': url},
            {'$addToSet': {'comments': {'$each': new_comments}}}
        )
        logging.info(f"Neue Kommentare hinzugefügt: {len(new_comments)} für Artikel {url}")


# Verarbeitet den Artikel basierend auf der Sprache (deutsch oder englisch)
def process_article_language(language, article, comments, full_text, reference_words,
                             processed_collection, vocabulary_collection_de,
                             vocabulary_collection_en, all_vocabulary_today_de,
                             all_vocabulary_today_en, progress_collection):
    url = article['url']

    # Überprüfe, ob der Artikel bereits verarbeitet wurde
    if article_already_processed(url, processed_collection):
        logging.info(f"Artikel {url} wurde bereits verarbeitet. Überspringe.")
        process_comments(comments, language, url, processed_collection)
        return

    # Extrahiere Schlüsselwörter und Phrasen aus dem Artikel
    filtered_article_phrases = extract_keywords_and_phrases(full_text, language, n=2)

    # Extrahiere Phrasen aus den Kommentaren, falls vorhanden
    filtered_comment_phrases = []
    if comments:
        for comment in comments:
            filtered_comment_phrases.extend(extract_keywords_and_phrases(comment, language, n=2))

    # Wenn weder Artikel- noch Kommentarphrasen vorhanden sind, überspringe den Artikel
    if not filtered_article_phrases and not filtered_comment_phrases:
        logging.warning(f"Artikel {url} enthält keine relevanten Phrasen. Überspringe.")
        return

    # Vergleiche die extrahierten Phrasen mit der Referenzdatei (für Deutsch) oder WordNet (für Englisch)
    new_article_phrases = []
    new_comment_phrases = []

    if language == 'de':
        # Vergleich der deutschen Phrasen mit der Referenzdatei
        new_article_phrases = compare_phrases_with_reference(filtered_article_phrases, reference_words)
        new_comment_phrases = compare_phrases_with_reference(filtered_comment_phrases, reference_words)

        # Aktualisiere nur das deutsche Vokabular
        for phrase in new_article_phrases:
            update_vocabulary(phrase, start_date, 'article', vocabulary_collection_de, all_vocabulary_today_de)
        for phrase in new_comment_phrases:
            update_vocabulary(phrase, start_date, 'comment', vocabulary_collection_de, all_vocabulary_today_de)

    elif language == 'en':
        # Überprüfung der englischen Phrasen mit WordNet
        new_article_phrases = [
            phrase for phrase in filtered_article_phrases
            if not any(wordnet.synsets(word) for word in phrase.split())
        ]
        new_comment_phrases = [
            phrase for phrase in filtered_comment_phrases
            if not any(wordnet.synsets(word) for word in phrase.split())
        ]

        # Aktualisiere nur das englische Vokabular
        for phrase in new_article_phrases:
            update_vocabulary(phrase, start_date, 'article', vocabulary_collection_en, all_vocabulary_today_en)
        for phrase in new_comment_phrases:
            update_vocabulary(phrase, start_date, 'comment', vocabulary_collection_en, all_vocabulary_today_en)

    # Speichere den Artikel in der 'processed_collection'
    processed_collection.insert_one({
        'title': article['title'],
        'url': article['url'],
        'full_text': full_text,
        'new_article_phrases': new_article_phrases,
        'new_comment_phrases': new_comment_phrases,
        'first_processed': start_date,
        'last_processed': start_date
    })

    # Speichere den Fortschritt
    save_progress(article['_id'], progress_collection)


# Verarbeitet Artikel basierend auf der erkannten Sprache
# Verarbeitet Artikel basierend auf der erkannten Sprache
def process_articles():
    reference_file_path_de = os.path.join(project_directory, 'output3.txt')

    # Lade die deutsche Referenzdatei
    reference_words_de = read_reference_file(reference_file_path_de)

    # Hole die zuletzt verarbeiteten IDs für Deutsch und Englisch
    last_processed_id_de = get_last_processed_id(progress_collection_de)
    last_processed_id_en = get_last_processed_id(progress_collection_en)

    # Separate Abfragen für deutsche und englische Artikel
    query_de = {}
    query_en = {}

    if last_processed_id_de:
        query_de = {'_id': {'$gt': last_processed_id_de}}  # Abfrage für deutsche Artikel

    if last_processed_id_en:
        query_en = {'_id': {'$gt': last_processed_id_en}}  # Abfrage für englische Artikel

    all_vocabulary_today_de = {
        'new_phrases': set(),
        'existing_phrases': set()
    }
    all_vocabulary_today_en = {
        'new_phrases': set(),
        'existing_phrases': set()
    }

    try:
        with client.start_session() as session:
            # Verarbeite deutsche Artikel
            cursor_de = collection.find(query_de, no_cursor_timeout=True, session=session).batch_size(100)

            try:
                for article in cursor_de:
                    url = article['url']
                    full_text = article['full_text']

                    # Überspringe Artikel, wenn 'full_text' leer ist
                    if not full_text:
                        logging.warning(f"Artikel {url} hat keinen Text. Überspringe.")
                        continue

                    comments = article.get('comments', [])
                    language = detect_language(full_text)

                    if language == 'de':
                        process_article_language(
                            'de', article, comments, full_text, reference_words_de,
                            processed_collection_de, vocabulary_collection_de, vocabulary_collection_en,
                            all_vocabulary_today_de, all_vocabulary_today_en, progress_collection_de
                        )


                    elif language == 'mixed':
                        # Gemischte Sprache: sowohl Deutsch als auch Englisch verarbeiten
                        process_article_language(
                            'de', article, comments, full_text, reference_words_de,
                            processed_collection_de, vocabulary_collection_de, vocabulary_collection_en,
                            all_vocabulary_today_de, all_vocabulary_today_en, progress_collection_de
                        )

                        process_article_language(
                            'en', article, comments, full_text, None,
                            processed_collection_en, vocabulary_collection_de, vocabulary_collection_en,
                            all_vocabulary_today_de, all_vocabulary_today_en, progress_collection_en
                        )

            except errors.CursorNotFound as e:
                logging.error(f"CursorNotFound-Fehler bei deutschen Artikeln: {e}")
                process_articles()  # Rekursiver Neustart für deutsche Artikel
            finally:
                cursor_de.close()

            # Verarbeite englische Artikel
            cursor_en = collection.find(query_en, no_cursor_timeout=True, session=session).batch_size(100)

            try:
                for article in cursor_en:
                    url = article['url']
                    full_text = article['full_text']

                    # Überspringe Artikel, wenn 'full_text' leer ist
                    if not full_text:
                        logging.warning(f"Artikel {url} hat keinen Text. Überspringe.")
                        continue

                    comments = article.get('comments', [])
                    language = detect_language(full_text)

                    if language == 'en':
                        process_article_language(
                            'en', article, comments, full_text, None,
                            processed_collection_en, vocabulary_collection_de, vocabulary_collection_en,
                            all_vocabulary_today_de, all_vocabulary_today_en, progress_collection_en
                        )

            except errors.CursorNotFound as e:
                logging.error(f"CursorNotFound-Fehler bei englischen Artikeln: {e}")
                process_articles()  # Rekursiver Neustart für englische Artikel
            finally:
                cursor_en.close()

    except Exception as e:
        logging.error(f"Fehler beim Starten der MongoDB-Sitzung: {e}")

    logging.info(f"Neue Phrasen für Deutsch: {list(all_vocabulary_today_de['new_phrases'])}")
    logging.info(f"Bestehende Phrasen für Deutsch: {list(all_vocabulary_today_de['existing_phrases'])}")
    logging.info(f"Neue Phrasen für Englisch: {list(all_vocabulary_today_en['new_phrases'])}")
    logging.info(f"Bestehende Phrasen für Englisch: {list(all_vocabulary_today_en['existing_phrases'])}")

    # Rufe am Ende die Funktion auf, um die tägliche Zusammenfassung zu speichern
    save_daily_summary(
        list(all_vocabulary_today_de['new_phrases']),  # neue Phrasen in deutschen Artikeln
        list(all_vocabulary_today_de['existing_phrases']),  # wiederholte Phrasen in deutschen Artikeln
        start_date,
        daily_summary_collection_de,
        vocabulary_growth_collection_de,
        vocabulary_collection_de
    )

    save_daily_summary(
        list(all_vocabulary_today_en['new_phrases']),  # neue Phrasen in englischen Artikeln
        list(all_vocabulary_today_en['existing_phrases']),  # wiederholte Phrasen in englischen Artikeln
        start_date,
        daily_summary_collection_en,
        vocabulary_growth_collection_en,
        vocabulary_collection_en
    )


if __name__ == '__main__':
    process_articles()