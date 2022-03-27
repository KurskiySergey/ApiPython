import scrapy
from scrapy.http import HtmlResponse
from scrapy.loader import ItemLoader
from lesson7.leryaparser.items import LeryaparserItem
import requests

class LeroymerlinruSpider(scrapy.Spider):
    name = 'leroymerlinru'
    handle_httpstatus_list = [200, 401]
    allowed_domains = ['leroymerlin.ru']

    def __init__(self, **kwargs):
        self.search = kwargs.get('search')
        self.start_urls = [f"https://leroymerlin.ru/search/?q={self.search}"]
        super().__init__(**kwargs)

    def parse(self, response: HtmlResponse):
        if response.status != 401:
            links = response.xpath("//a[@data-qa='product-name']")
            for link in links:
                yield response.follow(url=link, callback=self.item_parser)
        else:
            print("auth problem. look for instructions in settings module in default headers")
            print(response.url)
            print()

    def item_parser(self, response: HtmlResponse):
        # print()
        if response.status != 401:
            loader = ItemLoader(item=LeryaparserItem(), selector=response)
            loader.add_value(field_name='link', value=response.url)
            loader.add_xpath(field_name='name', xpath="//h1[@slot='title']/text()")
            loader.add_xpath(field_name='price', xpath="//uc-pdp-price-view[@slot='primary-price']/span/text()")
            loader.add_xpath(field_name="images", xpath="//picture[@slot='pictures']/img/@src")
            loader.add_xpath(field_name="def_values", xpath="//dl[@class='def-list']/div/dt/text()")
            loader.add_xpath(field_name='def_values', xpath="//dl[@class='def-list']/div/dd/text()")
            yield loader.load_item()
        else:
            print("auth problem. look for instructions in settings module in default headers")
            print(response.url)
            print()

