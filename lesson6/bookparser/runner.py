from scrapy.settings import Settings
from scrapy.crawler import CrawlerProcess
from lesson6.bookparser.spiders.labirintru import LabirintruSpider
from lesson6.bookparser.spiders.book24ru import Book24ruSpider
from lesson6.bookparser import settings


if __name__ == "__main__":

    bookparser_settings = Settings()
    bookparser_settings.setmodule(settings)
    process = CrawlerProcess(settings=bookparser_settings)
    process.crawl(LabirintruSpider)
    # process.crawl(Book24ruSpider)
    process.start()
