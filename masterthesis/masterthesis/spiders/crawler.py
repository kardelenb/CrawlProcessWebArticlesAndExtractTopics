from scrapy.spiders import SitemapSpider
from scrapy.crawler import CrawlerProcess
import html
from pymongo import MongoClient
import logging

# Verbindung zu MongoDB einrichten
client = MongoClient('mongodb://localhost:27017/')
db = client['scrapy_database']
collection = db['raw_articles']  # Neue Collection für die rohen Artikel

logging.getLogger('scrapy').propagate = False

# Kombinierter SitemapSpider und CrawlSpider
class MyCrawlSpider(SitemapSpider):
    name = 'my_crawl_spider'
    allowed_domains = ['sezession.de']
    sitemap_urls = [
        'https://sezession.de/wp-sitemap-posts-post-1.xml'
    ]
    sitemap_rules = [
        (r'/[^"]*', 'parse_post')
    ]

    def __init__(self, *args, **kwargs):
        super(MyCrawlSpider, self).__init__(*args, **kwargs)
        self.link_count = 0

    def parse_post(self, response):
        self.link_count += 1
        title = response.css('a.sez-post-title::text').getall()

        if not title:
            title = response.xpath("//h1[@class='sez-single-post-title']/text()").getall()

        paragraphs = response.xpath(
            "//p[not(@id='sez-donation-txt') and not(@id='sez-donation-bank')]//text()").getall()

        list_items = response.xpath("//li//text()").getall()

        full_text = ' '.join(html.unescape(text.strip()) for text in paragraphs + list_items if text.strip())

        full_text = full_text.replace('\u00AD', '')
        full_text = full_text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        full_text = ' '.join(full_text.split())

        collection.insert_one({
            'title': title,
            'url': response.url,
            'full_text': full_text
        })

    def closed(self, reason):
        self.log(f"Total number of links found: {self.link_count}")

if __name__ == '__main__':
    collection.delete_many({})
    process = CrawlerProcess()
    process.crawl(MyCrawlSpider)
    process.start()