import scrapy
from scrapy.crawler import CrawlerProcess
import logging
import html
from nltk.corpus import stopwords, wordnet
from nltk.tokenize import word_tokenize
from nltk.corpus import wordnet as wn
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk import download
import odenet
import string
import re
from summa import keywords

# Laden der NLTK-Resourcen
download('stopwords')
download('punkt')
download('wordnet')

# Stopwords für Deutsch und Englisch
german_stop_words = set(stopwords.words('german'))
english_stop_words = set(stopwords.words('english'))

logging.getLogger('scrapy').propagate = False

# Funktion zum Überprüfen, ob ein Wort in OdeNet existiert
def is_word_in_odenet(word):
    # Prüfe, ob das Wort in OdeNet vorkommt, indem überprüft wird, ob es in irgendeinem Synset enthalten ist
    synonyms = odenet.synonyms_word(word)
    return bool(synonyms)  # Gibt True zurück, wenn das Wort in einem Synset gefunden wurde

# Funktion zur Erkennung, ob ein Wort ein Eigenname oder Zahl ist
def is_valid_word(word):
    return word.isalpha() and word[0].islower()  # Keine Zahlen und keine Eigennamen (Großbuchstaben)

# Einfacher Scrapy Spider
class SinglePageSpider(scrapy.Spider):
    name = 'single_page_spider'
    allowed_domains = ['sezession.de']
    start_urls = [
        'https://sezession.de'  # Beispiel-URL, die geändert werden kann
    ]

    def parse(self, response):
        # Extrahiere den Titel aus dem <a>-Tag mit der Klasse 'sez-post-title'
        title = response.css('a.sez-post-title::text').getall()

        # Versuche die Absätze aus dem Artikel zu extrahieren und auch alle verschachtelten Elemente
        paragraphs = response.xpath("//p//text()").getall()
        # Kombiniere alle Absätze und dekodiere HTML-Zeichenreferenzen
        full_text = ' '.join(html.unescape(text.strip()) for text in paragraphs if text.strip())

        # Text bereinigen
        full_text = full_text.replace('\u00AD', '')  # \u00AD ist das Unicode für Soft Hyphen
        full_text = full_text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        full_text = ' '.join(full_text.split())  # Entferne doppelte Leerzeichen

        # TextRank Algorithmus verwenden, um Schlüsselwörter zu extrahieren
        ranked_keywords = keywords.keywords(full_text, words=20, split=True)

        # Filterung der Schlüsselwörter
        new_words = []
        for word in ranked_keywords:
            if not is_valid_word(word):
                continue  # Überspringt Zahlen, Eigennamen und andere ungültige Wörter
            if wordnet.synsets(word):
                continue  # Wort ist in WordNet enthalten
            if is_word_in_odenet(word):
                continue  # Wort ist in OdeNet enthalten
            new_words.append({
                'word': word,
                'score': None  # In TextRank gibt es keinen numerischen Score wie bei TF-IDF
            })

        yield {
            'title': title,
            'url': response.url,
            'full_text': full_text,
            'new_words': new_words
        }
