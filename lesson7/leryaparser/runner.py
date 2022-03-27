from scrapy.settings import Settings
from scrapy.crawler import CrawlerProcess
from lesson7.leryaparser import settings
from lesson7.leryaparser.spiders.leroymerlinru import LeroymerlinruSpider
import os


if __name__ == "__main__":

    search_data = "плитка"

    # change to project folder
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)

    parser_settings = Settings()
    parser_settings.setmodule(settings)
    process = CrawlerProcess(settings=parser_settings)
    process.crawl(LeroymerlinruSpider, search=search_data)
    process.start()
