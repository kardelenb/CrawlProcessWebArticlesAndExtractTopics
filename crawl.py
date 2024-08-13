import scrapy
from scrapy.signalmanager import dispatcher
from scrapy import signals
from scrapy.crawler import CrawlerProcess
import logging
import html
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.corpus import stopwords, wordnet
import os
import tempfile

# Initial Setup
import nltk

nltk.download('stopwords')
nltk.download('wordnet')


# Stopwords für Deutsch und Englisch
german_stop_words = set(stopwords.words('german'))
english_stop_words = set(stopwords.words('english'))

logging.getLogger('scrapy').propagate = False

# Funktion zum Parsen der openthesaurus.txt Datei
def parse_openthesaurus(file_path):
    openthesaurus_set = set()
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            parts = line.strip().split('\t')  # Zeile anhand von Tabulatorzeichen aufteilen
            if len(parts) > 1:  # Sicherstellen, dass die Zeile das erwartete Format hat
                word = parts[1]  # Das Wort ist das zweite Element
                openthesaurus_set.add(word.lower())  # Wort in Kleinbuchstaben in das Set einfügen
    return openthesaurus_set

# Beispiel wie man die Datei einbindet
openthesaurus_file = 'openthesaurus.txt'
if os.path.exists(openthesaurus_file):
    openthesaurus_data = parse_openthesaurus(openthesaurus_file)
else:
    openthesaurus_data = set()

# Funktion zum Überprüfen, ob ein Wort in openthesaurus.txt existiert
def is_word_in_openthesaurus(word):
    return word.lower() in openthesaurus_data

# Scrapy Spider Definition
class BlogSpider(scrapy.Spider):
    name = 'blogspider'
    start_urls = ['https://sezession.de/']

    def parse(self, response):
        for post in response.css('a.sez-post-title'):
            title = post.css('::attr(title)').get()
            url = post.css('::attr(href)').get()
            yield response.follow(url, self.parse_post, meta={'title': title})

    def parse_post(self, response):
        title = response.meta['title']

        # Extrahiere den gesamten Text der <p>-Tags
        paragraphs = response.css('p::text').getall()
        # Kombiniere alle Absätze und dekodiere HTML-Zeichenreferenzen
        full_text = ' '.join(html.unescape(text.strip()) for text in paragraphs if text.strip())

        # Textanalyse
        words = [word.lower() for word in full_text.split() if word.isalnum()]
        filtered_words = [word for word in words if word not in german_stop_words and word not in english_stop_words]

        # TF-IDF Ranking
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform([' '.join(filtered_words)])
        tfidf_scores = zip(vectorizer.get_feature_names_out(), tfidf_matrix.toarray()[0])
        ranked_keywords = sorted(tfidf_scores, key=lambda x: x[1], reverse=True)

        # Vergleich mit WordNet (Englisch) und deutschem Wörterbuch
        new_words = []
        for word, score in ranked_keywords:
            if wordnet.synsets(word):
                continue  # Wort ist in WordNet enthalten
            if is_word_in_openthesaurus(word):
                continue  # Wort ist in openthesaurus.txt enthalten
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


# Funktion zum Starten des Crawlers
def start_crawler():
    # Erstellen eines einzigartigen Dateinamens im temporären Verzeichnis
    output_file = os.path.join(tempfile.gettempdir(), 'output.json')

    if os.path.exists(output_file):
        os.remove(output_file)  # Leert die Datei vor jedem Crawlen

    print(f"Starting crawler. Output file: {output_file}")

    process = CrawlerProcess(settings={
        "FEEDS": {
            output_file: {"format": "json", "overwrite": True},
        },
        "REQUEST_FINGERPRINTER_IMPLEMENTATION": '2.7',
    })

    dispatcher.connect(lambda s, i, r, sp: print(f"Scraped item: {i}"), signal=signals.item_scraped)

    process.crawl(BlogSpider)
    process.start()

    print(f"Crawling completed. Output file located at: {output_file}")


# Start the crawling process
start_crawler()