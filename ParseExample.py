import json

import spacy
import requests
from bs4 import BeautifulSoup
import logging
import html
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.corpus import stopwords, wordnet
import nltk
import odenet
import re
from HanTa import HanoverTagger as ht  # Importiere HanTa

# Lade den HanTa-Tagger mit dem deutschen Modell
hannover = ht.HanoverTagger('morphmodel_ger.pgz')

# Lade deutsche und englische spaCy-Modelle
try:
    nlp_de = spacy.load('de_core_news_sm')
    nlp_en = spacy.load('en_core_web_sm')
except:
    import os

    os.system('python -m spacy download de_core_news_sm')
    os.system('python -m spacy download en_core_web_sm')
    nlp_de = spacy.load('de_core_news_sm')
    nlp_en = spacy.load('en_core_web_sm')

nltk.download('stopwords')
nltk.download('wordnet')

# Stopwords für Deutsch und Englisch
german_stop_words = set(stopwords.words('german'))
english_stop_words = set(stopwords.words('english'))

logging.getLogger().setLevel(logging.INFO)


# Funktion zum Überprüfen, ob ein Wort in OdeNet existiert
def is_word_in_odenet(word):
    synonyms = odenet.synonyms_word(word)
    return bool(synonyms)  # Gibt True zurück, wenn das Wort in einem Synset gefunden wurde


# Funktion zur Lemmatisierung mit HanTa
def lemmatize_with_hanta(word):
    lemma = hannover.analyze(word)[0]  # Extrahiere das Lemma mit HanTa
    return lemma


# Funktion zur POS-Tag-Filterung basierend auf der Sprache
def extract_keywords_by_pos(text, language, pos_tags=['NOUN', 'ADJ', 'VERB']):
    if language == 'de':
        doc = nlp_de(text)
        lemmatizer = lemmatize_with_hanta
    else:
        doc = nlp_en(text)
        lemmatizer = lambda token: token.lemma_

    only_letters = re.compile(r'^[^\W\d_]+$')

    return [
        lemmatizer(token.text)  # Verwende den ausgewählten Lemmatisierer
        for token in doc
        if token.pos_ in pos_tags
           and not token.is_stop
           and only_letters.match(token.lemma_)
    ]


def detect_language(text):
    if any(word in german_stop_words for word in text.split()):
        return 'de'
    return 'en'


def process_page(url):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extrahiere den Titel aus dem <a>-Tag mit der Klasse 'sez-post-title'
        title = soup.select('a.sez-post-title')
        title = [t.get_text() for t in title]

        if not title:
            title = soup.select_one("h1.sez-single-post-title")
            title = title.get_text() if title else []

        paragraphs = soup.select("p")
        list_items = soup.select("li")

        # Kombiniere alle Absätze und dekodiere HTML-Zeichenreferenzen
        full_text = ' '.join(
            html.unescape(tag.get_text().strip()) for tag in paragraphs + list_items if tag.get_text().strip())

        full_text = full_text.replace('\u00AD', '')  # \u00AD ist das Unicode für Soft Hyphen
        full_text = full_text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        full_text = ' '.join(full_text.split())  # Entferne doppelte Leerzeichen

        language = detect_language(full_text)

        filtered_words = extract_keywords_by_pos(full_text, language)

        vectorizer = TfidfVectorizer(lowercase=False)
        tfidf_matrix = vectorizer.fit_transform([' '.join(filtered_words)])
        tfidf_scores = zip(vectorizer.get_feature_names_out(), tfidf_matrix.toarray()[0])
        ranked_keywords = sorted(tfidf_scores, key=lambda x: x[1], reverse=True)

        new_words = []
        for word, score in ranked_keywords:
            if wordnet.synsets(word):
                continue
            if is_word_in_odenet(word):
                continue
            new_words.append({
                'word': word,
                'score': score
            })

        result = {
            'title': title,
            'url': url,
            'full_text': full_text,
            'ranked_keywords': [
                {
                    'word': word,
                    'score': score
                }
                for word, score in ranked_keywords
            ],
            'new_words': new_words
        }
        return result


def main():
    sitemap_urls = [
        'https://sezession.de/wp-sitemap-posts-post-1.xml'
    ]
    with open('masterthesis/masterthesis/spiders/results.json', 'w') as f:
        for sitemap_url in sitemap_urls:
            response = requests.get(sitemap_url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'xml')
                urls = [loc.text for loc in soup.find_all('loc')]

                for url in urls:
                    result = process_page(url)
                    if result:
                        f.write(json.dumps(result, ensure_ascii=False, indent=4) + '\n')


if __name__ == "__main__":
    main()

