from bs4 import BeautifulSoup
import requests
from pprint import pprint
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


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

    def limit_by(self, value: int):
        return self[:value]

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


if __name__ == "__main__":
    search = input("Введите критерий поиска: ")
    till_page = input("Введите ограничение по страницам (Если не важно нажмите enter): ")
    wish_address = input("Введите желаемый город (Если не важно нажмите enter): ")
    wish_min_price = input("Минимальный порог (Если не важно нажмите enter): ")

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

    hh = HeadHunter()
    find_vacancies = hh.find_vacancy(search=search, till_page=till_page)
    find_vacancies.save_to_file(filename="result.json")
    filter_vacancies = \
        find_vacancies.filter_by(category="address", value=wish_address).order_by_max_price(desc=True). \
            filter_by(category="min_price", value=wish_min_price).limit_by(5)
    pprint(filter_vacancies)
