from bs4 import BeautifulSoup
import requests
from pprint import pprint
import json
import os
import pymongo
from pymongo.errors import DuplicateKeyError
import hashlib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HOST = '127.0.0.1'
PORT = 27017
DB_NAME = "vacancies"


class MongoDB:
    def __init__(self, db_name, server_addr: tuple):
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

    def filter_by_price(self, collection_name, min_price):
        collection = self.get_collection(collection_name)
        total_list = collection.find({'price': {"$gt": min_price}})
        return VacancyList(total_list)


class VacancyList(list):
    category_list = {
        'min_price': lambda value: value[0] if value[0] is not None else 0,
        'max_price': lambda value: value[1] if value[1] is not None else 0,
        'address': lambda value: value,
        'employer': lambda value: value[0],
        'name': lambda value: value[0]
    }

    def order_by_max_price(self, desc=False):
        return VacancyList(sorted(self, reverse=desc,
                                  key=lambda vacancy: vacancy.get("price")[1] if vacancy.get("price")[
                                                                                     1] is not None else 0))

    def order_by_min_price(self, desc=False):
        return VacancyList(sorted(self, reverse=desc,
                                  key=lambda vacancy: vacancy.get("price")[0] if vacancy.get("price")[
                                                                                     0] is not None else 0))

    def limit_by(self, value: int, start_index: int = None):
        if start_index:
            if value:
                if start_index + value > len(self):
                    value = len(self) - start_index
                return VacancyList(self[start_index:start_index+value])
            else:
                return VacancyList(self[start_index:])
        else:
            if value:
                return VacancyList(self[:value])
            else:
                return self

    def filter_by(self, category: str, value):
        if value is None:
            return self

        filter_vacancy_list = VacancyList()
        if category in VacancyList.category_list:
            for vacancy in self:
                if category == "max_price":
                    info = VacancyList.category_list.get(category)(vacancy.get('price'))
                    if info <= value:
                        filter_vacancy_list.append(vacancy)

                elif category == "min_price":
                    info = VacancyList.category_list.get(category)(vacancy.get('price'))
                    if info >= value:
                        filter_vacancy_list.append(vacancy)

                else:
                    info = VacancyList.category_list.get(category)(vacancy.get(category))
                    if value.lower() in info.lower():
                        filter_vacancy_list.append(vacancy)

        return filter_vacancy_list

    def save_to_file(self, filename):
        with open(f"{BASE_DIR}/{filename}", "w", encoding='utf-8') as vacancies:
            try:
                json.dump(self.copy(), vacancies, ensure_ascii=False)
            except json.JSONDecodeError:
                vacancies.write(str(self))

    def add_to_mongo_collection(self, collection, unique_key: str = None):
        if unique_key is None:
            for vacancy in self:
                collection.insert_one(vacancy)

        else:
            for vacancy in self:
                try:
                    vacancy_value = vacancy.get(unique_key)
                    unique_value = json.dumps(vacancy_value).encode('utf-8')
                    unique_value_hash_id = hashlib.md5(unique_value).hexdigest()
                    _id = {"_id": unique_value_hash_id}
                    vacancy.update(_id)
                    collection.insert_one(vacancy)
                except DuplicateKeyError:
                    print(f"data with this unique data:{unique_key} exists already")


class HeadHunter:
    base_url = "https://hh.ru/"
    vacancy_search = "search/vacancy/"
    data_types = {
        "name": ["a", {"data-qa": "vacancy-serp__vacancy-title"}],
        "price": ["span", {"data-qa": "vacancy-serp__vacancy-compensation"}],
        "employer": ["a", {"data-qa": "vacancy-serp__vacancy-employer"}],
        "address": ['div', {"data-qa": "vacancy-serp__vacancy-address"}],
        "vacancy": ['div', {"class": "vacancy-serp-item"}]
    }

    def __init__(self, user_agent=None):
        if user_agent is None:
            self.user_agent = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/98.0.4758.102 Safari/537.36",
            }
        else:
            self.user_agent = user_agent

        self.__dom = None
        self.max_page = None

    @staticmethod
    def __get_anchor(vacancy, type_):
        info_type = HeadHunter.data_types.get(type_)
        anchor = vacancy.find(info_type[0], info_type[1])
        return anchor

    @staticmethod
    def __get_price(vacancy):
        price_anchor = HeadHunter.__get_anchor(vacancy, "price")
        if price_anchor:
            price_anchor = price_anchor.getText()
            price_list = price_anchor.split(" ")
            units = price_list[-1]
            if "до" in price_anchor:
                min_pay = None
                max_pay = float(price_list[1].replace("\u202f", ""))
            elif "от" in price_anchor:
                min_pay = float(price_list[1].replace("\u202f", ""))
                max_pay = None

            else:
                min_pay = float(price_list[0].replace("\u202f", ""))
                max_pay = float(price_list[2].replace("\u202f", ""))

        else:
            min_pay = None
            max_pay = None
            units = None

        return [min_pay, max_pay, units]

    @staticmethod
    def __get_employer(vacancy):
        anchor = HeadHunter.__get_anchor(vacancy, "employer")
        if anchor:
            employer = anchor.getText().replace("\xa0", " ")
            employer_href = f"{HeadHunter.base_url}{anchor['href']}"
        else:
            employer = None
            employer_href = None

        return [employer, employer_href]

    @staticmethod
    def __get_name(vacancy):
        anchor = HeadHunter.__get_anchor(vacancy, "name")

        if anchor:
            name = anchor.getText()
            href = anchor['href']

        else:
            name = None
            href = None

        return [name, href]

    @staticmethod
    def __get_address(vacancy):
        address_anchor = HeadHunter.__get_anchor(vacancy, "address")

        if address_anchor:
            address = address_anchor.getText()
        else:
            address = None

        return address

    def __get_vacancies(self):
        vacancy_type = HeadHunter.data_types.get("vacancy")
        vacancies = self.__dom.find_all(vacancy_type[0], vacancy_type[1])
        return vacancies

    def parse_dom(self):

        vacancies = self.__get_vacancies()
        vacancy_list = VacancyList()

        for vacancy in vacancies:
            vacancy_data = {}
            name = HeadHunter.__get_name(vacancy)
            price = HeadHunter.__get_price(vacancy)
            employer = HeadHunter.__get_employer(vacancy)
            address = HeadHunter.__get_address(vacancy)

            vacancy_data['name'] = name
            vacancy_data['price'] = price
            vacancy_data['employer'] = employer
            vacancy_data['address'] = address
            vacancy_list.append(vacancy_data)

        return vacancy_list

    def get_max_page(self):
        pages = self.__dom.find_all("span", {"class": "pager-item-not-in-short-range"})
        self.max_page = int(pages[-1].getText()) - 1
        return self.max_page

    def send_request(self, url, params, headers):
        response = requests.get(url=url, headers=headers, params=params)
        self.__dom = BeautifulSoup(response.text, "html.parser")

    def find_vacancy(self, search, till_page: int = None) -> VacancyList:
        print("Ваш запрос обрабатывается и фильтруется...")
        vacancy_page_list = VacancyList()
        params = {
            'text': search,
            "page": 0
        }
        url = f"{HeadHunter.base_url}{HeadHunter.vacancy_search}"

        self.send_request(url=url, params=params, headers=self.user_agent)
        vacancy_page_list += self.parse_dom()

        self.get_max_page()

        if till_page is None:
            max_page = self.max_page

        else:
            if isinstance(till_page, int):
                max_page = till_page if till_page <= self.max_page else self.max_page
            else:
                try:
                    max_page = int(till_page)
                except ValueError:
                    max_page = self.max_page

        for page in range(1, max_page):
            self.send_request(url=url, params=params, headers=self.user_agent)
            vacancy_page_list += self.parse_dom()
            params['page'] += 1

        return vacancy_page_list


def start_db(collection_name, drop=False):
    mongo_db = MongoDB(db_name=DB_NAME, server_addr=(HOST, PORT))
    if drop:
        mongo_db.drop_db()
    mongo_db.add_collection(collection_name=collection_name)

    return mongo_db


def scrap_site(mongo_db, collection_name):
    # getting data from user
    search = input("Введите критерий поиска: ")
    till_page = input("Введите ограничение по страницам (Если не важно нажмите enter): ")
    wish_address = input("Введите желаемый город (Если не важно нажмите enter): ")
    wish_min_price = input("Минимальный порог (Если не важно нажмите enter): ")
    limit = input("Ограничить результат до (Если не важно нажмите enter): ")
    save_to_db = input("Сохранить результат в базе данных? y - да, n - нет: ")

    if till_page == "":
        till_page = None
    else:
        till_page = int(till_page)

    if wish_address == "":
        wish_address = None

    if wish_min_price == "":
        wish_min_price = None
    else:
        wish_min_price = float(wish_min_price)

    if limit == "":
        limit = None
    else:
        limit = int(limit)

    # creating headhunter scraper and mongo collection
    hh = HeadHunter()

    # scrap for info
    find_vacancies = hh.find_vacancy(search=search, till_page=till_page)
    # save find result
    find_vacancies.save_to_file(filename="result.json")
    # filter info according to user data
    filter_vacancies = \
        find_vacancies.filter_by(category="address", value=wish_address).order_by_max_price(desc=True). \
            filter_by(category="min_price", value=wish_min_price).limit_by(limit)
    # print filter result
    pprint(filter_vacancies)
    print()
    # add result to mongo
    if save_to_db.lower() == 'y':
        filter_vacancies.add_to_mongo_collection(collection=mongo_db.get_collection(collection_name), unique_key='name')


def mongo_search(mongo_db, collection_name):
    # mongo filter
    print("Посик данных в базе данных...")
    prefer_price = float(input("Введите желаемую заработную плату: "))
    page_limit = int(input("Количество вакансий в одной странице: "))
    filter_data = mongo_db.filter_by_price(collection_name, min_price=prefer_price).order_by_max_price(desc=True)
    print(f"Найдено вакансий - > {len(filter_data)}")
    pages = len(filter_data) // page_limit + 1
    page_count = 0
    start_index = 0
    while page_count < pages:
        pprint(filter_data.limit_by(page_limit, start_index=start_index))
        page_count += 1
        start_index += page_limit
        input(f"page {page_count}/{pages} press enter: \n")


if __name__ == "__main__":
    collection_name = 'vacancies'
    mongo_db = start_db(collection_name, drop=False)

    while True:
        print("Для выхода нажмите q")
        use_db = input("Использовать существующую базу или сделать запрос на сайт? y - да, n - нет: ")
        if use_db.lower() == 'y':
            mongo_search(mongo_db, collection_name)
        elif use_db.lower() == "q":
            break
        else:
            scrap_site(mongo_db, collection_name)

