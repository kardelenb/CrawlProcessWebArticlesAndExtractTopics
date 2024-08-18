import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import XMLFeedSpider


class SitemapSpider(XMLFeedSpider):
    name = "SitemapSpider"
    start_urls = [
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
    itertag = 'url'  # Das Tag, das jede URL enthält

    def parse_node(self, response, node):
        # Extrahieren der URL aus dem <loc>-Tag in jeder <url>-Gruppe
        page_url = node.xpath('loc/text()').get()

        if page_url:
            yield scrapy.Request(page_url, callback=self.parse_page)

    def parse_page(self, response):
        # Hier verwenden wir den LinkExtractor, um Links von jeder Seite zu extrahieren
        link_extractor = LinkExtractor()
        links = link_extractor.extract_links(response)

        for link in links:
            yield {"url": link.url}
