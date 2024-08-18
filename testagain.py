from scrapy.shell import inspect_response
from scrapy.spiders import CrawlSpider, Rule
from scrapy.crawler import CrawlerProcess
from scrapy.linkextractors import LinkExtractor
import requests
import chardet

class TestSpider(CrawlSpider):
    name = 'testspider'
    allowed_domains = ['sezession.de']
    start_urls = ['https://sezession.de']

    # rules = (
    #     Rule(LinkExtractor(allow='/[0-9]{4}/[0-9]{2}/'), callback='parse_post', follow=True),
    #     Rule(LinkExtractor(), follow=True),
    # )

    # String with unknown encoding
    # data = b'hn &bdquo;Liebhaber&ldquo;, igitt. Zuchthaus bis'
    #
    # # Detect the encoding
    # result = chardet.detect(data)
    # print(result['encoding'])
    # Fetch the web page content
    response = requests.get('https://sezession.de/69397/die-wehrpflicht-und-der-neue-bellizismus')
    html_content = response.content
    #
    # # Detect the encoding
    result = chardet.detect(html_content)
    print(result['encoding'])
   # def parse_post(self, response):
        # inspect_response(response, self)
        # title = response.css('h1::text').getall()  # Titel extrahieren
        # paragraphs = response.css('p::text').getall()  # Text-Absätze extrahieren
        # response.css("p::text").getall()

        # print(f"Title: {title}")
        # print(f"Paragraphs: {paragraphs}")
# Erstellen und Starten des CrawlerProcess
# process = CrawlerProcess()
#
# # Spider hinzufügen und starten
# process.crawl(TestSpider)
# process.start()  # Blockiert den Prozess, bis der Spider fertig ist

print("Scraping abgeschlossen und Prozess beendet.")