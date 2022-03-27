# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from lesson5.mongo_db import MongoDB


class BookparserPipeline:

    def __init__(self):
        self.item_proceed_funcs = {
            'labirintru': self.proceed_labirint,
            'book24ru': self.proceed_book24,
        }
        self.db_name = 'books'
        self.db = MongoDB(db_name=self.db_name)

    @staticmethod
    def proceed_price(price: list):
        old_price = 0
        new_price = 0
        currency = None
        for price_elem in price:
            try:
                price_elem = float(price_elem)
                if price_elem > old_price:
                    old_price = price_elem
                else:
                    new_price = price_elem
            except ValueError:
                currency = price_elem
            except TypeError:
                pass
        if new_price == 0:
            new_price = old_price

        return old_price, new_price, currency

    def process_item(self, item, spider):
        # print("hello from pipeline")
        self.db.add_collection(collection_name=spider.name)
        item = self.item_proceed_funcs.get(spider.name)(item)
        self.db.add_to_mongo_collection([dict(item)], collection_name=spider.name, unique_key='link')
        return item

    def proceed_labirint(self, item):
        item['authors'] = " ".join(item.get('authors'))
        price = item.get("price")

        old_price, new_price, currency = self.proceed_price(price)

        item['price'] = f"{old_price} {currency}"
        item['discount_price'] = f"{new_price} {currency}"

        return item

    def proceed_book24(self, item):
        price = item.get("price")

        old_price, new_price, currency = self.proceed_price(price)

        item['price'] = f"{old_price} {currency}"
        item['discount_price'] = f"{new_price} {currency}"

        return item