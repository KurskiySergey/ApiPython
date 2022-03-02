from pprint import pprint
import pymongo
from pymongo.errors import DuplicateKeyError
import hashlib
import json


class MongoDB:
    def __init__(self, db_name, server_addr: tuple = ('127.0.0.1', 27017)):
        self.host = server_addr[0]
        self.port = server_addr[1]
        self.db_name = db_name
        self.__client = pymongo.MongoClient(host=self.host, port=self.port)
        self.db = self.__client[self.db_name]
        self.db_collections = self.db.list_collection_names()

    def add_collection(self, collection_name):
        if collection_name not in self.db_collections:
            self.db.create_collection(name=collection_name)
            self.db_collections.append(collection_name)

    def get_collection(self, collection_name):
        if collection_name in self.db_collections:
            return self.db.get_collection(collection_name)
        return self.db.get_collection(self.db_collections[0])

    def drop_db(self):
        self.__client.drop_database(self.db_name)

    def show_all(self):
        for collection in self.db_collections:
            print(f'Collection {collection}')
            info = self.get_collection(collection).find({})
            pprint(list(info))
            print()

    def add_to_mongo_collection(self, data_list, collection_name, unique_key: str = None):
        collection = self.get_collection(collection_name=collection_name)
        if data_list:
            if unique_key is None:
                for data in data_list:
                    collection.insert_one(data)

            else:
                for data in data_list:
                    try:
                        data_value = data.get(unique_key)
                        unique_value = json.dumps(data_value).encode('utf-8')
                        unique_value_hash_id = hashlib.md5(unique_value).hexdigest()
                        _id = {"_id": unique_value_hash_id}
                        data.update(_id)
                        collection.insert_one(data)
                    except DuplicateKeyError:
                        print(f"data with this unique data:{unique_key} exists already")

