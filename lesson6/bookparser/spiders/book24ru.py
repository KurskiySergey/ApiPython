import scrapy
from scrapy.http import HtmlResponse
from lesson6.bookparser.items import BookparserItem
import re


class Book24ruSpider(scrapy.Spider):
    name = 'book24ru'
    handle_httpstatus_list = [200, 404]
    allowed_domains = ['book24.ru']
    start_urls = ['http://book24.ru/catalog/']

    def parse(self, response: HtmlResponse):
        # print("hello from scrapy")
        if response.status == 200:
            pattern = "-\d*"
            re_result = re.search(pattern=pattern, string=response.url)
            if re_result:
                page = int(re_result.group()[1:])
                follow_url = f"{self.start_urls[0]}page-{page+1}"
            else:
                follow_url = f"{self.start_urls[0]}page-2"
            yield response.follow(url=follow_url, callback=self.parse)

            links = response.xpath("//div[@class='product-card__image-holder']/a/@href").getall()
            for link in links:
                yield response.follow(url=link, callback=self.book_parse)

    def book_parse(self, response: HtmlResponse):
        # print("hello from parser")
        link = response.url
        title = response.xpath("//h1[@itemprop='name']/text()").get()
        rating = response.xpath("//meta[@itemprop='ratingValue']/@content").get()
        price = response.xpath("//meta[@itemprop='price']/@content").get()
        currency = response.xpath("//meta[@itemprop='priceCurrency']/@content").get()
        old_price = response.xpath("//span[contains(@class, 'price-old')]/text()").get()
        authors = response.xpath("//meta[@itemprop='name']/@content").get()

        book = BookparserItem(title=title, rating=rating, price=[price, old_price, currency], authors=authors, link=link)
        yield book
