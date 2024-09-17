import spacy
from scrapy.spiders import SitemapSpider
from scrapy.crawler import CrawlerProcess
import logging
import html
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.corpus import stopwords, wordnet
import os
import tempfile
import nltk
import odenet
import re
from HanTa import HanoverTagger as ht  # Importiere HanTa
import multiprocessing  # Import für parallele Verarbeitung
from collections import defaultdict  # Für Caching

# Lade den HanTa-Tagger mit dem deutschen Modell
hannover = ht.HanoverTagger('morphmodel_ger.pgz')

# Lade deutsche und englische spaCy-Modelle
try:
    nlp_de = spacy.load('de_core_news_sm')
    nlp_en = spacy.load('en_core_web_sm')
except:
    os.system('python -m spacy download de_core_news_sm')
    os.system('python -m spacy download en_core_web_sm')
    nlp_de = spacy.load('de_core_news_sm')
    nlp_en = spacy.load('en_core_web_sm')

nltk.download('stopwords')
nltk.download('wordnet')

# Stopwords für Deutsch und Englisch
german_stop_words = set(stopwords.words('german'))
english_stop_words = set(stopwords.words('english'))

logging.getLogger('scrapy').propagate = False

# Optimierter TF-IDF Vektorizer
vectorizer = TfidfVectorizer(lowercase=False, max_features=5000, ngram_range=(1, 2))

# Cache für Wörterbuchvergleiche
wordnet_cache = {}
odenet_cache = {}

# Optimierte Funktion zur Überprüfung, ob ein Wort in WordNet existiert
def is_word_in_wordnet_cache(word):
    if word in wordnet_cache:
        return wordnet_cache[word]
    result = wordnet.synsets(word)
    wordnet_cache[word] = result
    return result

# Optimierte Funktion zur Überprüfung, ob ein Wort in OdeNet existiert
def is_word_in_odenet_cache(word):
    if word in odenet_cache:
        return odenet_cache[word]
    result = is_word_in_odenet(word)
    odenet_cache[word] = result
    return result

# Funktion zum Überprüfen, ob ein Wort in OdeNet existiert
def is_word_in_odenet(word):
    # Prüfe, ob das Wort in OdeNet vorkommt, indem überprüft wird, ob es in irgendeinem Synset enthalten ist
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
        # Verwende HanTa zur Lemmatisierung, da spaCy manchmal Fehler macht
        lemmatizer = lemmatize_with_hanta
    else:
        doc = nlp_en(text)
        lemmatizer = lambda token: token.lemma_

    # Regex zur Überprüfung, ob ein Wort nur aus Buchstaben besteht
    only_letters = re.compile(r'^[^\W\d_]+$')

    # Extrahiere und lemmatisiere Tokens
    return [
        lemmatizer(token.text)  # Verwende den ausgewählten Lemmatisierer
        for token in doc
        if token.pos_ in pos_tags
           and not token.is_stop
           and only_letters.match(token.lemma_)
    ]
def compute_tfidf(words):
    local_vectorizer = TfidfVectorizer(lowercase=False, max_features=5000, ngram_range=(1, 2))
    tfidf_matrix = local_vectorizer.fit_transform([' '.join(words)])
    return tfidf_matrix, local_vectorizer.get_feature_names_out()
# Kombinierter SitemapSpider und CrawlSpider
class MyCombinedSpider(SitemapSpider):
    name = 'my_combined_spider'
    allowed_domains = ['sezession.de']

    # Liste von Sitemap-URLs
    sitemap_urls = [
        'https://sezession.de/wp-sitemap-posts-post-1.xml'
    ]

    sitemap_rules = [
        (r'/[^"]*', 'parse_post')  # Regex für das Matching der URLs
    ]

    def __init__(self, *args, **kwargs):
        super(MyCombinedSpider, self).__init__(*args, **kwargs)
        self.link_count = 0

    def parse_post(self, response):
        # Zähle die gefundenen Links
        self.link_count += 1

        # Extrahiere den Titel aus dem <a>-Tag mit der Klasse 'sez-post-title'
        title = response.css('a.sez-post-title::text').getall()

        # Falls kein Titel aus dem <a>-Tag gefunden wird, suche im <h1>-Tag
        if not title:
            title = response.xpath("//h1[@class='sez-single-post-title']/text()").getall()

        # Versuche die Absätze aus dem Artikel zu extrahieren und auch alle verschachtelten Elemente
        paragraphs = response.xpath("//p//text()").getall()
        list_items = response.xpath("//li//text()").getall()

        # Kombiniere alle Absätze und dekodiere HTML-Zeichenreferenzen
        full_text = ' '.join(html.unescape(text.strip()) for text in paragraphs + list_items if text.strip())

        full_text = full_text.replace('\u00AD', '')  # \u00AD ist das Unicode für Soft Hyphen
        full_text = full_text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        full_text = ' '.join(full_text.split())  # Entferne doppelte Leerzeichen

        # Sprache des Textes erkennen
        language = self.detect_language(full_text)

        # Keywords extrahieren basierend auf Wortarten (nur NOUN, PROPN, ADJ. VERB)
        filtered_words = extract_keywords_by_pos(full_text, language)

        if filtered_words:
            with multiprocessing.Pool() as pool:
                tfidf_result = pool.apply_async(compute_tfidf, (filtered_words,))
                tfidf_matrix, feature_names = tfidf_result.get()

            tfidf_scores = zip(feature_names, tfidf_matrix.toarray()[0])
            ranked_keywords = sorted(tfidf_scores, key=lambda x: x[1], reverse=True)
        else:
            ranked_keywords = []

        # Optimierter Wörterbuchvergleich
        new_words = []
        for word, score in ranked_keywords:
            if is_word_in_wordnet_cache(word):
                continue  # Wort ist in WordNet enthalten
            if is_word_in_odenet_cache(word):
                continue  # Wort ist in OdeNet enthalten
            new_words.append({
                'word': word,
                'score': score
            })

        yield {
            'title': title,
            'url': response.url,
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

    def detect_language(self, text):
        # Einfache Heuristik zur Sprachekennung
        if any(word in german_stop_words for word in text.split()):
            return 'de'
        return 'en'

    def contains_number(self, word):
        # Überprüft, ob ein Wort eine Zahl enthält
        return bool(re.search(r'\d', word))

    def closed(self, reason):
        # Ausgabe der Gesamtanzahl der gefundenen Links
        self.log(f"Total number of links found: {self.link_count}")
# Prozess starten
# process = CrawlerProcess()
# process.crawl(MyCombinedSpider)
# process.start()
