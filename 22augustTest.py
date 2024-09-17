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
from iwnlp.iwnlp_wrapper import IWNLPWrapper


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

logging.getLogger('scrapy').propagate = False

# Initialisiere den IWNLPWrapper mit dem Pfad zur entpackten JSON-Datei
lemmatizer = IWNLPWrapper(lemmatizer_path='C:/Users/karde/Downloads/IWNLP.Lemmatizer_20181001/IWNLP.Lemmatizer_20181001.json')

# Funktion zum Überprüfen, ob ein Wort in OdeNet existiert
def is_word_in_odenet(word):
    # Prüfe, ob das Wort in OdeNet vorkommt, indem überprüft wird, ob es in irgendeinem Synset enthalten ist
    synonyms = odenet.synonyms_word(word)
    return bool(synonyms)  # Gibt True zurück, wenn das Wort in einem Synset gefunden wurde

# Funktion zur Lemmatisierung mit HanTa
def lemmatize_with_hanta(word):
    lemma = hannover.analyze(word)[0]  # Extrahiere das Lemma mit HanTa
    return lemma

# Funktion zur Lemmatisierung mit IWNLP
def lemmatize_with_iwnlp(word, pos):
    lemmas = lemmatizer.lemmatize(word, pos_universal_google=pos)
    return lemmas[0] if lemmas else word

# Funktion zur Überprüfung der Lemmata mit allen Methoden
def check_consistent_lemma(word, pos):
    lemma_spacy = nlp_de(word)[0].lemma_
    lemma_hanta = lemmatize_with_hanta(word)
    lemma_iwnlp = lemmatize_with_iwnlp(word, pos)
    return lemma_spacy == lemma_hanta == lemma_iwnlp, lemma_spacy

# Funktion zur POS-Tag-Filterung basierend auf der Sprache
def extract_keywords_by_pos(text, language, pos_tags=['NOUN', 'ADJ', 'VERB']):
    if language == 'de':
        doc = nlp_de(text)
    else:
        doc = nlp_en(text)

    # Regex zur Überprüfung, ob ein Wort nur aus Buchstaben besteht
    only_letters = re.compile(r'^[^\W\d_]+$')

    # Extrahiere und prüfe Tokens
    consistent_lemmas = []
    for token in doc:
        if token.pos_ in pos_tags and not token.is_stop and only_letters.match(token.lemma_):
            is_consistent, lemma = check_consistent_lemma(token.text, token.pos_)
            if is_consistent:
                consistent_lemmas.append(lemma)
            else:
                consistent_lemmas.append(token.lemma_)
    return consistent_lemmas

# Funktion zum Filtern von Wörtern basierend auf TF-IDF-Scores
def filter_new_words(tfidf_results, threshold=0.1):
    """
    Filtert die TF-IDF-Ergebnisse, um nur Wörter mit niedrigeren Punktzahlen zu behalten.
    """
    filtered_words = [item for item in tfidf_results if item['score'] <= threshold]
    return filtered_words


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

        # TF-IDF Ranking
        vectorizer = TfidfVectorizer(lowercase=False)
        tfidf_matrix = vectorizer.fit_transform([' '.join(filtered_words)])
        tfidf_scores = zip(vectorizer.get_feature_names_out(), tfidf_matrix.toarray()[0])
        ranked_keywords = sorted(tfidf_scores, key=lambda x: x[1], reverse=True)

        # Definiere einen Schwellenwert für die TF-IDF-Scores
        threshold = 0.1  # Dieser Wert kann je nach Bedarf angepasst werden

        # Ausschließen der am höchsten gerankten Wörter, um mögliche Neologismen herauszufiltern
        top_keywords = {word for word, score in ranked_keywords[:10]}  # Die Top-10 Wörter ausschließen

        # Vergleich mit WordNet (Englisch) und deutschem Wörterbuch (OdeNet)
        new_words = []
        for word, score in ranked_keywords:
            if word not in top_keywords and not is_word_in_odenet(word) and score > threshold:
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

    def closed(self, reason):
        # Ausgabe der Gesamtanzahl der gefundenen Links
        self.log(f"Total number of links found: {self.link_count}")