import scrapy
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

nltk.download('stopwords')
nltk.download('wordnet')

# Stopwords für Deutsch und Englisch
german_stop_words = set(stopwords.words('german'))
english_stop_words = set(stopwords.words('english'))

logging.getLogger('scrapy').propagate = False

# Funktion zum Überprüfen, ob ein Wort in OdeNet existiert
def is_word_in_odenet(word):
    # Prüfe, ob das Wort in OdeNet vorkommt, indem überprüft wird, ob es in irgendeinem Synset enthalten ist
    synonyms = odenet.synonyms_word(word)
    return bool(synonyms)  # Gibt True zurück, wenn das Wort in einem Synset gefunden wurde

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

        # Versuche die Absätze aus dem Artikel zu extrahieren und auch alle verschachtelten Elemente
        paragraphs = response.xpath("//p//text()").getall()
        # Kombiniere alle Absätze und dekodiere HTML-Zeichenreferenzen
        full_text = ' '.join(html.unescape(text.strip()) for text in paragraphs if text.strip())

        full_text = full_text.replace('\u00AD', '')  # \u00AD ist das Unicode für Soft Hyphen
        full_text = full_text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        full_text = ' '.join(full_text.split())  # Entferne doppelte Leerzeichen

        # Textanalyse ohne Umwandlung in Kleinbuchstaben
        words = [word for word in full_text.split() if word.isalnum()]

        # Sprache des Textes erkennen
        language = self.detect_language(full_text)
        stop_words = german_stop_words if language == 'de' else english_stop_words

        # Wörter filtern: keine Stoppwörter und keine Wörter mit Zahlen
        filtered_words = [word for word in words if word.lower() not in stop_words and not self.contains_number(word)]

        # TF-IDF Ranking
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform([' '.join(filtered_words)])
        tfidf_scores = zip(vectorizer.get_feature_names_out(), tfidf_matrix.toarray()[0])
        ranked_keywords = sorted(tfidf_scores, key=lambda x: x[1], reverse=True)

        # Vergleich mit WordNet (Englisch) und deutschem Wörterbuch (OdeNet)
        new_words = []
        for word, score in ranked_keywords:
            if wordnet.synsets(word):
                continue  # Wort ist in WordNet enthalten
            if is_word_in_odenet(word):
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


