import scrapy
from scrapy.spiders import SitemapSpider

class MySitemapSpider(SitemapSpider):
    name = 'my_sitemap_spider'
    allowed_domains = ['sezession.de']

    # Liste von Sitemap-URLs
    sitemap_urls = [
        'https://sezession.de/wp-sitemap-posts-post-1.xml',
        'https://sezession.de/wp-sitemap-posts-post-2.xml',
        'https://sezession.de/wp-sitemap-posts-post-3.xml',
        'https://sezession.de/wp-sitemap-posts-post-4.xml',
        'https://sezession.de/wp-sitemap-posts-page-1.xml',
        'https://sezession.de/wp-sitemap-posts-books-1.xml',
        'https://sezession.de/wp-sitemap-taxonomies-category-1.xml',
        'https://sezession.de/wp-sitemap-taxonomies-post_tag-1.xml',
        'https://sezession.de/wp-sitemap-taxonomies-post_tag-2.xml',
        'https://sezession.de/wp-sitemap-taxonomies-post_tag-3.xml',
        'https://sezession.de/wp-sitemap-taxonomies-post_tag-4.xml',
        'https://sezession.de/wp-sitemap-taxonomies-post_tag-5.xml',
        'https://sezession.de/wp-sitemap-taxonomies-post_tag-6.xml',
        'https://sezession.de/wp-sitemap-taxonomies-post_tag-7.xml',
        'https://sezession.de/wp-sitemap-users-1.xml'
    ]

    sitemap_rules = [
        (r'/[^"]*', 'parse_item')  # Regex für das Matching der URLs
    ]

    def __init__(self, *args, **kwargs):
        super(MySitemapSpider, self).__init__(*args, **kwargs)
        self.link_count = 0

    def parse_item(self, response):
        # Zähle die gefundenen Links
        self.link_count += 1

    def closed(self, reason):
        # Ausgabe der Gesamtanzahl der gefundenen Links
        self.log(f"Total number of links found: {self.link_count}")