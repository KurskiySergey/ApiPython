import scrapy
from scrapy.http import HtmlResponse
from lesson6.bookparser.items import BookparserItem


class LabirintruSpider(scrapy.Spider):
    name = 'labirintru'
    allowed_domains = ['labirint.ru']
    start_urls = ['https://www.labirint.ru/books/?order=date&way=back&paperbooks=1&ebooks=1&otherbooks=1&available=1&preorder=1&wait=1&no=1&price_min=&price_max=']

    def parse(self, response: HtmlResponse):
        # print("hello from scrapy")
        next_page = response.xpath("//div[@class='pagination-next']/a/@href").get()
        if next_page:
            yield response.follow(url=next_page, callback=self.parse)

        links = response.xpath("//div[@class='products-row ']//a[@class='product-title-link' or @class='b-product-block-link']/@href").getall()
        for link in links:
            yield response.follow(url=link, callback=self.book_parser)

    def book_parser(self, response: HtmlResponse):
        # print('hello from callback')
        book_link = response.url
        book_title = response.xpath("//div[@id='product-title']/h1/text()").get()
        book_rating = response.xpath("//div[@id='rate']/text()").get()
        book_price = response.xpath("//span[contains(@class, 'buying-price')]/text()").getall()
        authors = response.xpath("//div[@class='authors']//text()").getall()
        book = BookparserItem(title=book_title, authors=authors, price=book_price,
                              rating=book_rating, link=book_link)

        yield book

