# scrapy_link_extractor.py
import scrapy
from scrapy.linkextractors import LinkExtractor


class QuoteSpider(scrapy.Spider):
    name = "OuoteSpider"
    start_urls = ['https://sezession.de']

    def parse(self, response):
        link_extractor = LinkExtractor()
        links = link_extractor.extract_links(response)

        for link in links:
            yield {"url": link.url}