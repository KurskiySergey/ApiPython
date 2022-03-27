# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from itemloaders.processors import TakeFirst, MapCompose, Join


class LeryaparserItem(scrapy.Item):
    # define the fields for your item here like:
    name = scrapy.Field(output_processor=TakeFirst())
    price = scrapy.Field()
    currency = scrapy.Field()
    link = scrapy.Field(output_processor=TakeFirst())
    images = scrapy.Field()
    def_values = scrapy.Field(input_processor=Join(" ; "), output_processor=MapCompose(lambda v: v.replace("\n", "")))
