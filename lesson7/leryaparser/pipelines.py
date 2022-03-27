# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.pipelines.images import ImagesPipeline
from scrapy import Request
import hashlib
from lesson5.mongo_db import MongoDB


class LeryaparserPipeline:

    def __init__(self):
        self.db_name = 'leryamerlin'
        self.db = MongoDB(db_name=self.db_name)

    def convert_def_values(self, values):
        titles = values[0].split(" ; ")
        data = values[1].split(" ; ")
        values = {titles[i]: data[i] for i in range(len(titles))}
        return values

    def process_item(self, item, spider):

        collection = f"{spider.name}.{spider.search}"
        self.db.add_collection(collection_name=collection)
        price = item.get('price')
        def_values = self.convert_def_values(item.get("def_values"))
        current_price = None
        currency = []
        for info in price:
            info = info.replace("\xa0", "").replace(" ", "")
            try:
                info = int(info)
                current_price = info
            except:
                currency.append(info)

        currency = "/".join(currency)

        item['price'] = current_price
        item['currency'] = currency
        item['def_values'] = def_values

        self.db.add_to_mongo_collection(data_list=[dict(item)], collection_name=collection, unique_key='link')
        return item


class LeryaImagePipeline(ImagesPipeline):

    def get_media_requests(self, item, info):
        links = item.get("images")
        if links:
            for link in links:
                try:
                    yield Request(url=link)
                except Exception as e:
                    print(e)

    def item_completed(self, results, item, info):
        images = [img[1] for img in results if img[0]]
        item['images'] = images
        return item

    def file_path(self, request, response=None, info=None, *, item=None):
        image_guid = hashlib.sha1(request.url.encode('utf-8')).hexdigest()
        item_path = f"{item.get('name')}/{image_guid}.jpg"

        return item_path
