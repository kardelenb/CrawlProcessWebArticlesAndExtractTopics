import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy.crawler import CrawlerProcess

class TestSpider(scrapy.Spider):
    name = "testspider"

    start_urls = ['https://sezession.de']

    rules = (
        # Regel für die Startseite, um Links zur "Recherche"-Seite und Artikel zu folgen
        Rule(LinkExtractor(allow=r'/recherche'), follow=True),

        # Regel, um Links zu Artikeln zu folgen und die parse_item Methode aufzurufen
        Rule(LinkExtractor(allow=r'/\d{5,}/'), callback='parse_item', follow=True),
    )

    def parse(self, response):
        # Teste die Selektoren
        titles = response.css('a.sez-post-title::text').getall()


        # Gib die Ergebnisse aus
        print("Titel:")
        for title in titles:
            print(title)


# Funktion zum Starten des Crawlers
def start_crawler():
    process = CrawlerProcess()
    process.crawl(TestSpider)
    process.start()

# Starte den Test
start_crawler()