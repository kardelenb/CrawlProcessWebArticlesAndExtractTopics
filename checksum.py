from collections import Counter
import spacy
from germanetpy import germanet
from germanetpy.filterconfig import Filterconfig
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.corpus import stopwords, wordnet
import nltk
import re
import hashlib
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
collection = db['sezession0510raw']
processed_collection = db['sezessionProcessed']
vocabulary_collection = db['sezessionVocab']
daily_summary_collection = db['sezessionDaily']
progress_collection = db['sezessionProgress']
vocabulary_growth_collection = db['sezessionGrowth']

processed_collection.create_index('url')

# Lege das Startdatum beim Start des Programms fest
#start_date = datetime.now().strftime('%Y-%m-%d')
start_date = '2024-12-12'

# Lade deutsche und englische spaCy-Modelle
nlp_de = spacy.load('de_core_news_sm')
nlp_en = spacy.load('en_core_web_sm')

nltk.download('stopwords')
nltk.download('wordnet')

german_stop_words = set(stopwords.words('german'))
english_stop_words = set(stopwords.words('english'))

project_directory = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))


# Diese Methode kombiniert den Artikeltext und die Kommentare und erzeugt daraus eine Checksumme.
def generate_static_checksum(content, comments):
    combined_content = content + " ".join(comments)  # Kombiniert den Artikeltext und die Kommentare
    return hashlib.sha256(combined_content.encode('utf-8')).hexdigest()


def get_new_content(old_text, new_text):
    if old_text in new_text:
        return new_text.replace(old_text, '').strip()
    return new_text  # Wenn der alte Text nicht enthalten ist, den gesamten neuen Text zurückgeben


# Funktion zur Extraktion generischer Sätze
def create_generic_sentence_list(threshold=5):
    sentence_counter = Counter()
    for article in collection.find({}, {"full_text": 1}):
        sentences = split_into_sentences(article['full_text'])
        sentence_counter.update(sentences)
    return {sentence for sentence, count in sentence_counter.items() if count >= threshold}


# Funktion zum Aufteilen in Sätze
def split_into_sentences(text):
    return re.split(r'(?<=[.!?]) +', text)


# Kommentarfunktionen
def is_short_comment(comment):
    name_pattern = re.compile(r"^[A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)?(?:\s+[A-ZÄÖÜ][a-zäöüß]+)?$")
    WORD_COUNT_THRESHOLD = 4
    return bool(name_pattern.match(comment.strip())) or len(comment.split()) < WORD_COUNT_THRESHOLD


def filter_comments(comments):
    return [comment for comment in comments if not is_short_comment(comment)]

# Lese die Referenzdatei ein (bereinigte Datei)
def read_reference_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        reference_words = [line.strip().lower() for line in f]
    return reference_words


# Sprache erkennen
def detect_language(text):
    if any(word in german_stop_words for word in text.split()):
        return 'de'
    return 'en'


# Korrigierte Funktion, um Phrasen zu extrahieren, bei denen die Wörter direkt aufeinander folgen
def extract_phrases_with_noun_as_second(doc, pos_tags=['NOUN'], preceding_tags=['ADJ', 'VERB'], n=2):
    phrases = []
    only_letters_or_hyphen = re.compile(r'^[A-Za-zäöüÄÖÜß]+(-[A-Za-zäöüÄÖÜß]+)*$')  # Erlaubt nur Buchstaben und Bindestriche  # Keine führenden/abschließenden Bindestriche

    # Hier werden nur Tokens betrachtet, die keine Stopwords sind und alphabetisch sind
    tokens = [
        token for token in doc
        if not token.is_stop
           and only_letters_or_hyphen.match(token.text)
           and not token.text.startswith('-')  # Keine führenden Bindestriche
           and not token.text.endswith('-')  # Keine abschließenden Bindestriche
    ]

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
           and re.match(r'^[A-Za-zäöüÄÖÜß]+(-[A-Za-zäöüÄÖÜß]+)*$', token.text)  # Nur alphabetische Zeichen und Bindestriche
           and not token.text.startswith('-')  # Keine führenden Bindestriche
           and not token.text.endswith('-')  # Keine abschließenden Bindestriche
    ]

    # Mehrwortphrasen (z.B. N-Gramme) extrahieren, bei denen das zweite Wort ein Nomen ist
    phrases = extract_phrases_with_noun_as_second(doc, pos_tags=['NOUN'], preceding_tags=['ADJ', 'VERB'], n=n)

    return single_keywords + phrases

def compare_phrases_with_reference(new_phrases, reference_words):
    reference_set = set(reference_words)
    updated_new_phrases = []

    for phrase in new_phrases:
        words_in_phrase = phrase.lower().split()  # Zerlege die Phrase in einzelne Wörter und prüfe jedes Wort
        if not all(word in reference_set for word in words_in_phrase):
            updated_new_phrases.append(
                phrase)  # Nur hinzufügen, wenn es nicht in der Referenzdatei und nicht in GermaNet ist

    return updated_new_phrases

# Datenbankaktualisierungen für neue Phrasen
def update_vocabulary(phrase, start_date, source, all_vocabulary_today):
    existing_phrase = vocabulary_collection.find_one({'word': phrase})
    field = 'article_occurrences' if source == 'article' else 'comment_occurrences'
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


def save_daily_summary(new_article_phrases, new_comment_phrases, start_date):
    # Berechne die Häufigkeit der neuen Wörter für den Tag
    article_word_frequencies = {}
    comment_word_frequencies = {}

    # Zähle die Häufigkeit der Wörter in Artikeln
    for word in new_article_phrases:
        article_word_frequencies[word] = article_word_frequencies.get(word, 0) + 1

    # Zähle die Häufigkeit der Wörter in Kommentaren
    for word in new_comment_phrases:
        comment_word_frequencies[word] = comment_word_frequencies.get(word, 0) + 1

    # Unterscheide zwischen neuen und bereits gesehenen Wörtern
    new_words_today = set()
    repeated_words_today = set()

    for word in article_word_frequencies.keys() | comment_word_frequencies.keys():
        word_entry = vocabulary_collection.find_one({'word': word})

        # Wort ist neu, wenn es heute zum ersten Mal gesehen wurde
        if word_entry and word_entry['first_seen'] == start_date:
            new_words_today.add(word)
        elif word_entry:
            repeated_words_today.add(word)

    # Prüfe, ob es bereits einen Eintrag für das aktuelle Datum gibt
    existing_entry = daily_summary_collection.find_one({'date': start_date})

    if existing_entry:
        # Aktualisiere den bestehenden Eintrag
        daily_summary_collection.update_one(
            {'date': start_date},
            {
                '$set': {
                    'article_word_frequencies': {**existing_entry.get('article_word_frequencies', {}),
                                                 **article_word_frequencies},
                    'comment_word_frequencies': {**existing_entry.get('comment_word_frequencies', {}),
                                                 **comment_word_frequencies},
                    'new_words_today': list(new_words_today | set(existing_entry.get('new_words_today', []))),
                    'repeated_words_today': list(repeated_words_today | set(existing_entry.get('repeated_words_today', []))),
                    'new_word_count': len(new_words_today | set(existing_entry.get('new_words_today', []))),
                    'repeated_word_count': len(repeated_words_today | set(existing_entry.get('repeated_words_today', [])))
                }
            }
        )
        logging.info(f"Tägliche Zusammenfassung für {start_date} wurde aktualisiert.")
    else:
        # Erstelle einen neuen Eintrag
        daily_summary_collection.insert_one({
            'date': start_date,
            'article_word_frequencies': article_word_frequencies,
            'comment_word_frequencies': comment_word_frequencies,
            'new_words_today': list(new_words_today),
            'repeated_words_today': list(repeated_words_today),
            'new_word_count': len(new_words_today),
            'repeated_word_count': len(repeated_words_today)
        })
        logging.info(f"Neue tägliche Zusammenfassung für {start_date} erstellt.")

    # Speichere das Vokabelwachstum
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


# Hauptverarbeitungsfunktion
def process_articles():
    try:
        generic_sentences = create_generic_sentence_list()
        logging.info(f"Generische Sätze identifiziert: {len(generic_sentences)}")

        # Ausgabe der generischen Sätze im Log
        logging.info("Liste der generischen Sätze:")
        for sentence in generic_sentences:
            logging.info(f"- {sentence}")

        reference_file_path = os.path.join(project_directory, 'wortschatzLeipzig.txt')
        reference_words = read_reference_file(reference_file_path)

        all_vocabulary_today = {
            'new_phrases': set(),
            'existing_phrases': set()
        }
        processed_articles = 0

        with client.start_session() as session:
            cursor = collection.find(no_cursor_timeout=True, session=session).batch_size(100)

            try:
                for article in cursor:
                    try:
                        url = article['url']
                        full_text = article['full_text']
                        comments = article.get('comments', [])

                        # Skip articles with neither full_text nor comments
                        if not full_text and not comments:
                            logging.warning(f"Artikel {url} enthält weder Text noch Kommentare. Überspringe.")
                            continue

                        # Berechne die neue statische Checksumme
                        new_static_checksum = generate_static_checksum(full_text, comments)

                        # Prüfe, ob der Artikel bereits in 'processed_collection' existiert
                        processed_article = processed_collection.find_one({'url': url})
                        if processed_article:
                            old_static_checksum = processed_article.get('static_checksum')

                            # Wenn die Checksumme gleich ist, gab es keine Änderungen am Artikel
                            if old_static_checksum == new_static_checksum:
                                logging.info(f"Artikel unverändert: {url}")
                                continue  # Überspringen, wenn keine Änderungen

                            # Nur den neuen Inhalt seit der letzten Verarbeitung berücksichtigen
                            old_text = processed_article.get('full_text', '')
                            new_article_content = get_new_content(old_text, full_text)
                            new_comments = list(set(comments) - set(processed_article.get('comments', [])))

                            # Falls keine neuen Inhalte oder Kommentare vorhanden sind, überspringen
                            if not new_article_content and not new_comments:
                                logging.info(f"Keine neuen Inhalte in Artikel: {url}")
                                continue

                            # Filtere nur die neuen Inhalte durch generische Sätze
                            new_sentences = split_into_sentences(new_article_content)
                            new_filtered_text = " ".join(
                                sentence for sentence in new_sentences if sentence not in generic_sentences
                            )
                        else:
                            # Für neue Artikel den gesamten Inhalt filtern und verarbeiten
                            sentences = split_into_sentences(full_text)
                            new_filtered_text = " ".join(
                                sentence for sentence in sentences if sentence not in generic_sentences
                            )
                            new_article_content = new_filtered_text
                            new_comments = comments

                        # Verarbeite nur den gefilterten neuen Inhalt des Artikels
                        language = detect_language(new_filtered_text)
                        filtered_article_phrases = extract_keywords_and_phrases(new_filtered_text, language, n=2)

                        # Verarbeite die neuen Kommentare
                        filtered_comments = filter_comments(new_comments)
                        filtered_comment_phrases = []
                        for comment in filtered_comments:
                            filtered_comment_phrases.extend(extract_keywords_and_phrases(comment, language, n=2))

                        # Entferne englische Wörter, die in WordNet definiert sind
                        new_article_phrases = [
                            phrase for phrase in filtered_article_phrases if
                            not (language == 'en' and any(wordnet.synsets(word) for word in phrase.split()))
                        ]
                        new_comment_phrases = [
                            phrase for phrase in filtered_comment_phrases if
                            not (language == 'en' and any(wordnet.synsets(word) for word in phrase.split()))
                        ]

                        # Vergleiche Phrasen mit Referenz
                        new_article_phrases = compare_phrases_with_reference(new_article_phrases, reference_words)
                        new_comment_phrases = compare_phrases_with_reference(new_comment_phrases, reference_words)

                        # Bestimme nur tatsächlich neue Phrasen
                        previous_article_phrases = set(
                            processed_article.get('new_article_phrases', [])) if processed_article else set()
                        previous_comment_phrases = set(
                            processed_article.get('new_comment_phrases', [])) if processed_article else set()

                        unique_new_article_phrases = set(new_article_phrases) - previous_article_phrases
                        unique_new_comment_phrases = set(new_comment_phrases) - previous_comment_phrases

                        # Update das Vokabular und berücksichtige nur wirklich neue Phrasen für die Tageszusammenfassung
                        for phrase in unique_new_article_phrases:
                            update_vocabulary(phrase, start_date, 'article', all_vocabulary_today)
                        for phrase in unique_new_comment_phrases:
                            update_vocabulary(phrase, start_date, 'comment', all_vocabulary_today)

                        # Bestimme den vollständigen Text, der gespeichert werden soll
                        if processed_article:
                            old_text = processed_article.get('full_text', '')
                            updated_full_text = old_text + " " + new_article_content.strip()
                        else:
                            updated_full_text = full_text.strip()

                        # Aktualisiere die Datenbank mit den vollständigen Daten und der neuen Checksumme
                        processed_collection.update_one(
                            {'url': url},
                            {'$set': {
                                'title': article['title'],
                                'url': url,
                                'full_text': updated_full_text,  # Speichere den gesamten gefilterten Text
                                'comments': comments,  # Speichere die vollständigen Kommentare
                                'new_article_phrases': list(previous_article_phrases | unique_new_article_phrases),
                                'new_comment_phrases': list(previous_comment_phrases | unique_new_comment_phrases),
                                'static_checksum': new_static_checksum,
                                'first_processed': start_date if not processed_article else processed_article[
                                    'first_processed'],
                                'last_processed': start_date
                            }},
                            upsert=True
                        )

                        processed_articles += 1
                        logging.info(f"Neuer Artikel verarbeitet: {processed_articles}")

                    except Exception as article_error:
                        logging.error(f"Fehler beim Verarbeiten des Artikels mit URL '{url}': {article_error}")

            except errors.CursorNotFound as e:
                logging.error(f"CursorNotFound-Fehler: {e}")
                process_articles()
            finally:
                cursor.close()

            save_daily_summary(list(all_vocabulary_today['new_phrases']),
                               list(all_vocabulary_today['existing_phrases']),
                               start_date)

    except Exception as e:
        logging.error(f"Fehler in der Hauptverarbeitungsfunktion: {e}")


if __name__ == '__main__':
    process_articles()
