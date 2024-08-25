import scrapy
from scrapy.spiders import SitemapSpider
from scrapy.crawler import CrawlerProcess
import logging
import html
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.corpus import stopwords, wordnet
import nltk
import odenet  # OdeNet importieren

nltk.download('stopwords')
nltk.download('wordnet')

# Stopwords für Deutsch und Englisch
german_stop_words = set(stopwords.words('german'))
english_stop_words = set(stopwords.words('english'))

logging.getLogger('scrapy').propagate = False

# Funktion zum Überprüfen, ob ein Wort in OdeNet existiert
def is_word_in_odenet(word):
    synsets = odenet.words_in_synset(word)
    return bool(synsets)

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

    max_pages = 1  # Setze die maximale Anzahl der Seiten auf 1
    pages_crawled = 0

    def __init__(self, *args, **kwargs):
        super(MyCombinedSpider, self).__init__(*args, **kwargs)
        self.link_count = 0

    def parse_post(self, response):
        # Check if the maximum number of pages has been reached
        if self.pages_crawled >= self.max_pages:
            return  # Stop further crawling

        # Zähle die gefundenen Links
        self.link_count += 1
        self.pages_crawled += 1  # Inkrementiere die gecrawlte Seitenanzahl

        # Extrahiere den Titel aus dem <a>-Tag mit der Klasse 'sez-post-title'
        title = response.css('a.sez-post-title::text').getall()

        # Versuche die Absätze aus dem Artikel zu extrahieren und auch alle verschachtelten Elemente
        paragraphs = response.xpath("//p//text()").getall()
        full_text = ' '.join(html.unescape(text.strip()) for text in paragraphs if text.strip())

        full_text = full_text.replace('\u00AD', '')  # \u00AD ist das Unicode für Soft Hyphen
        full_text = full_text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        full_text = ' '.join(full_text.split())  # Entferne doppelte Leerzeichen

        # Textanalyse
        words = [word.lower() for word in full_text.split() if word.isalnum()]
        filtered_words = [word for word in words if word not in german_stop_words and word not in english_stop_words]

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

    def closed(self, reason):
        self.log(f"Total number of links found: {self.link_count}")

