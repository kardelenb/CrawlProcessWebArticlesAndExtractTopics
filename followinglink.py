import scrapy
from scrapy.signalmanager import dispatcher
from scrapy import signals
from scrapy.crawler import CrawlerProcess
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
import logging

logging.getLogger('scrapy').propagate = False

class SipSpider(CrawlSpider):
    name = 'blogspider'
    start_urls = ['https://sezession.de/']
    rules = (
        Rule(LinkExtractor(allow='', deny=['']))
    )

    def parse_item(self, response):
        for post in response.css('a.sez-post-title'):
            title = post.css('::attr(title)').get()
            url = post.css('::attr(href)').get()

            yield {
                'title': title,
                'url': url
            }
        # Weiteren Seiten folgen (z.B. Links in der Navigation)
        next_pages = response.css('a::attr(href)').getall()
        for next_page in next_pages:
            if next_page is not None:
                yield response.follow(next_page, self.parse)


# Funktion, um Signale zu empfangen und am Ende das Crawling abzuschließen
def crawler_results(signal, sender, item, response, spider):
    print(f"Scraped Item: {item}")


# Scrapy-Signal zum Sammeln von Ergebnissen nutzen
dispatcher.connect(crawler_results, signal=signals.item_scraped)

# Crawler-Prozess initialisieren und Spider starten
process = CrawlerProcess(settings={
    "FEEDS": {
        "output.json": {"format": "json"},  # Ergebnis wird in output.json gespeichert
    },
})

process.crawl(BlogSpider)
process.start()