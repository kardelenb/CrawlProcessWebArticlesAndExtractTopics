import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.corpus import stopwords, wordnet
import nltk
import re
from pymongo import MongoClient, errors
from datetime import datetime
import logging

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.getLogger('pymongo').setLevel(logging.WARNING)

# Verbindung zur MongoDB und Zugriff auf gespeicherte Artikel
client = MongoClient('mongodb://localhost:27017/')
db = client['scrapy_database']
collection = db['raw_articles']
processed_collection = db['processed_articles']
vocabulary_collection = db['vocabulary']
daily_summary_collection = db['daily_summary']

# Neue Sammlung, um den Fortschritt zu speichern
progress_collection = db['process_progress']

processed_collection.create_index('url')

# Lade deutsche und englische spaCy-Modelle
nlp_de = spacy.load('de_core_news_sm')
nlp_en = spacy.load('en_core_web_sm')

nltk.download('stopwords')
nltk.download('wordnet')

german_stop_words = set(stopwords.words('german'))
english_stop_words = set(stopwords.words('english'))

# Lese die Referenzdatei ein (bereinigte Datei)
def read_reference_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        reference_words = [line.strip().lower() for line in f]
    return reference_words

# Extrahiert Schlüsselwörter nach POS-Tags (ohne Lemmatisierung)
def extract_keywords_by_pos(text, language, pos_tags=['NOUN', 'ADJ', 'VERB']):
    if language == 'de':
        doc = nlp_de(text)
    else:
        doc = nlp_en(text)

    only_letters = re.compile(r'^[^\W\d_]+$')

    return [
        token.text
        for token in doc
        if token.pos_ in pos_tags
           and not token.is_stop
           and only_letters.match(token.text)
    ]

# Bestimmt die Sprache eines Textes
def detect_language(text):
    if any(word in german_stop_words for word in text.split()):
        return 'de'
    return 'en'

# Vergleicht die extrahierten Wörter mit der Referenzdatei
def compare_words_with_reference(new_words, reference_words):
    reference_set = set(reference_words)
    updated_new_words = []
    for word in new_words:
        if word['word'].lower() not in reference_set:
            updated_new_words.append(word)
    return updated_new_words

# Aktualisiert das Vokabular
def update_vocabulary(word, current_date):
    existing_word = vocabulary_collection.find_one({'word': word})

    if existing_word:
        vocabulary_collection.update_one(
            {'word': word},
            {
                '$inc': {'occurrences': 1},
                '$set': {'last_seen': current_date}
            }
        )
    else:
        vocabulary_collection.insert_one({
            'word': word,
            'first_seen': current_date,
            'last_seen': current_date,
            'occurrences': 1
        })

# Speichert die tägliche Zusammenfassung
def save_daily_summary(new_words, current_date):
    # Berechne die Häufigkeit der neuen Wörter für den Tag
    word_frequencies = {}
    for word_data in new_words:
        word = word_data['word']
        if word in word_frequencies:
            word_frequencies[word] += 1
        else:
            word_frequencies[word] = 1

    # Speichere die tägliche Zusammenfassung
    daily_summary_collection.insert_one({
        'date': current_date,
        'new_words': [{'word': word, 'frequency': freq} for word, freq in word_frequencies.items()]
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
    reference_file_path = 'C:/Users/karde/PycharmProjects/pythonProject/output3.txt'
    reference_words = read_reference_file(reference_file_path)
    current_date = datetime.now().strftime('%Y-%m-%d')

    all_new_words = []
    skipped_articles = 0
    processed_articles = 0

    # Hole die zuletzt verarbeitete ID
    last_processed_id = get_last_processed_id()

    query = {}
    if last_processed_id:
        query = {'_id': {'$gt': last_processed_id}}

    try:
        with client.start_session() as session:
            # Verwende `no_cursor_timeout` und `batch_size`
            cursor = collection.find(query, no_cursor_timeout=True, session=session).batch_size(100)

            try:
                for article in cursor:
                    full_text = article['full_text']

                    language = detect_language(full_text)
                    filtered_words = extract_keywords_by_pos(full_text, language)

                    # Überprüfe, ob `filtered_words` leer ist
                    if not filtered_words:
                        logging.warning(f"Artikel {article['url']} enthält nur Stopwords oder ist leer. Überspringe.")
                        continue

                    try:
                        vectorizer = TfidfVectorizer(lowercase=False)
                        tfidf_matrix = vectorizer.fit_transform([' '.join(filtered_words)])
                        tfidf_scores = zip(vectorizer.get_feature_names_out(), tfidf_matrix.toarray()[0])
                        ranked_keywords = sorted(tfidf_scores, key=lambda x: x[1], reverse=True)
                    except Exception as e:
                        logging.error(f"Fehler beim Berechnen der TF-IDF für Artikel {article['url']}: {e}")
                        continue

                    new_words = []
                    for word, score in ranked_keywords:
                        if language == 'en' and wordnet.synsets(word):
                            continue

                        new_words.append({
                            'word': word,
                            'score': score
                        })

                    if language == 'de':
                        new_words = compare_words_with_reference(new_words, reference_words)

                    for word_data in new_words:
                        update_vocabulary(word_data['word'], current_date)

                    existing_article = processed_collection.find_one({'url': article['url']})

                    if existing_article:
                        skipped_articles += 1
                        logging.info(f"Artikel übersprungen: {skipped_articles}")
                        continue

                    else:
                        processed_collection.insert_one({
                            'title': article['title'],
                            'url': article['url'],
                            'full_text': full_text,
                            'ranked_keywords': [{'word': word, 'score': score} for word, score in ranked_keywords],
                            'new_words': new_words,
                            'first_processed': current_date,
                            'last_processed': current_date
                        })

                        processed_articles += 1
                        logging.info(f"Neuer Artikel verarbeitet: {processed_articles}")

                    # Speichere den Fortschritt nach jedem Artikel
                    save_progress(article['_id'])

                    all_new_words.extend(new_words)

            except errors.CursorNotFound as e:
                logging.error(f"CursorNotFound-Fehler: {e}")
                # Versuche, den Cursor neu zu starten oder die Verbindung erneut herzustellen
                process_articles()  # Rekursiver Neustart

            finally:
                cursor.close()  # Stelle sicher, dass der Cursor geschlossen wird

    except Exception as e:
        logging.error(f"Fehler beim Starten der MongoDB-Sitzung: {e}")

    save_daily_summary(all_new_words, current_date)


if __name__ == '__main__':
    process_articles()
