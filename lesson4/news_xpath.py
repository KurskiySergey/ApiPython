from lxml import html
import requests
from abc import ABC, abstractmethod
from lesson4.mongo_db import MongoDB
import datetime


def get_today():
    today = datetime.datetime.today()
    return str(today).split(" ")[0]


class Scraper(ABC):

    def __init__(self, base_url):
        self.base_url = base_url
        self.base_response = None
        self.dom = None
        self.user_agent = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                         "AppleWebKit/537.36 (KHTML, like Gecko) "
                                         "Chrome/98.0.4758.102 Safari/537.36",
                           }
        self.news = None

    def get_response(self):
        try:
            self.base_response = requests.get(self.base_url, headers=self.user_agent)
            print(f"Got response from server {self.base_url}")
            return True
        except (ConnectionResetError, ConnectionAbortedError, ConnectionError, requests.exceptions.ConnectionError):
            print(f"No response from server {self.base_url}")
            return False

    def create_dom(self):
        if self.base_response:
            self.dom = html.fromstring(self.base_response.text)

    @abstractmethod
    def parse_news(self):
        pass

    @abstractmethod
    def collect_news(self):
        pass


class YandexScraper(Scraper):
    base_url = "https://yandex.ru/news/"

    def __init__(self):
        super().__init__(base_url=YandexScraper.base_url)

    def parse_news(self):
        sections = self.dom.xpath("//section[@aria-labelledby]")
        section_news_list = []
        today = get_today()
        for section in sections:
            titles = section.xpath(".//h2[@class='mg-card__title']/a/text()")
            links = section.xpath(".//h2[@class='mg-card__title']/a/@href")
            annotations = section.xpath(".//div[@class='mg-card__annotation']/text()")
            sources = section.xpath(".//a[@class='mg-card__source-link']/@aria-label")
            times = section.xpath(".//span[@class='mg-card-source__time']/text()")
            section_data = [
                {'title': titles[i],
                 'annotation': annotations[i],
                 'link': links[i],
                 'source': sources[i],
                 'date': today,
                 'time': times[i]} for i in range(len(titles))
            ]
            section_news_list += section_data
        self.news = section_news_list

    def collect_news(self):

        for news in self.news:
            for key, value in news.items():
                if isinstance(value, str):
                    value = value.replace("\xa0", " ")
                    news[key] = value

        return self.news


class LentaScraper(Scraper):
    base_url = "https://lenta.ru/"

    def __init__(self):
        super().__init__(base_url=LentaScraper.base_url)

    def get_lenta_last24_news_time(self, link):
        try:
            response = requests.get(url=f"{self.base_url}{link}", headers=self.user_agent)
            news_dom = html.fromstring(response.text)
            time = news_dom.xpath("//time[contains(@class, 'topic-header__time')]/text()")[0].split(",")[0]
            return time
        except (ConnectionError, ConnectionAbortedError, ConnectionResetError, requests.exceptions.ConnectionError):
            return None

    def get_response_data(self):
        date = self.dom.xpath("//time[contains(@class, 'header__time')]/text()")
        return date[0].split(",")[0]

    def parse_news(self):
        lenta_list_news = []
        last24_news = self.dom.xpath("//div[@class='last24']/a")
        today = get_today()

        for news in last24_news:
            link, = news.xpath("./@href")
            topic, = news.xpath(".//text()")
            time = self.get_lenta_last24_news_time(link=link)
            news_info = {
                "link": f"{self.base_url}{link}",
                "source": 'Lenta',
                'topic': topic,
                'date': today,
                'time': time
            }

            lenta_list_news.append(news_info)

        lenta_news = self.dom.xpath("//div[contains(@class, 'longgrid-list__box') or "
                                    "contains(@class, 'longgrid-feature-list__box') or "
                                    "@class='topnews__column' ]//a")

        for news in lenta_news:
            link, = news.xpath("./@href")
            try:
                topic, time = news.xpath(".//text()")
            except ValueError:
                topic_title, topic_text, time = news.xpath(".//text()")
                topic = " ".join([topic_title, topic_text])

            news_info = {
                'link': f"{self.base_url}{link}",
                "source": 'Lenta',
                'topic': topic,
                "date": today,
                'time': time
            }
            lenta_list_news.append(news_info)

        self.news = lenta_list_news

    def collect_news(self):
        return self.news


class MailScraper(Scraper):
    base_url = "https://news.mail.ru/"

    def __init__(self):
        super().__init__(base_url=MailScraper.base_url)

    def get_news_date_and_source(self, url: str):
        try:
            if url.startswith("http"):
                response = requests.get(url=url)
            else:
                response = requests.get(url=f"{self.base_url}{url}")
            news_dom = html.fromstring(response.text)
            info = news_dom.xpath("//span[@class='note']")
            date_info = info[0].xpath("./span/@datetime")
            source = info[1].xpath(".//text()")
            return [date_info, source]
        except (ConnectionError, ConnectionResetError, ConnectionAbortedError, requests.exceptions.ConnectionError, IndexError):
            return None, None

    def parse_news(self):
        news_list = []
        main_news = self.dom.xpath("//td[contains(@class, 'daynews__')]//a[contains(@class, 'js-topnews__item')]")

        for main in main_news:
            link, = main.xpath('./@href')
            text = " ".join(main.xpath('.//text()'))
            link_info = self.get_news_date_and_source(url=link)

            main_data = {
                'title': text,
                'link': link,
                'date': link_info[0],
                'time': link_info[1]
            }

            news_list.append(main_data)

        main_links = self.dom.xpath("//ul[@data-module='TrackBlocks']/li[@class='list__item']")

        for main_link in main_links:
            link, = main_link.xpath("./a/@href")
            title = " ".join(main_link.xpath(".//text()"))
            link_info = self.get_news_date_and_source(url=link)

            link_data = {
                'title': title,
                'link': link,
                'date': link_info[0],
                'time': link_info[1]
            }

            news_list.append(link_data)

        news_sections = self.dom.xpath("//div[contains(@data-logger, 'news__Main')]")[1:-1]
        for section in news_sections:
            links = section.xpath(".//div[@class='cols__wrapper' or @class='collections__card']"
                                  "//a[not(contains(@class, 'hdr__text'))]/@href")
            titles = section.xpath(".//div[@class='cols__wrapper' or @class='collections__card']"
                                   "//a[not(contains(@class, 'hdr__text'))]"
                                   "//span[not(contains(@class,'collections__param'))]//text()")

            links_info = [self.get_news_date_and_source(url=link) for link in links]
            section_data = [
                {'title': titles[i],
                 'link': links[i],
                 'date': links_info[i][0],
                 'source': links_info[i][1]
                 } for i in range(len(titles))
            ]

            news_list += section_data

        self.news = news_list

    def collect_news(self):
        for news in self.news:

            for key, value in news.items():
                if isinstance(value, str):
                    value = value.replace("\xa0", " ")
                    news[key] = value

                if key == "link":
                    if not value.startswith("http"):
                        value = f"{self.base_url}{value}"
                        news[key] = value

                if key == "date":
                    if value:
                        date = value[0]
                        date = date.split("T")
                        time = date[1].split("+")[0]
                        value = " ".join([date[0], time])

                    else:
                        value = get_today()
                    news[key] = value

                if key == "source":
                    if not value:
                        value = "mail.ru"
                    else:
                        value = value[1]
                    news[key] = value
        return self.news


class NewsScraper:

    def __init__(self):
        self.__scraper = None
        self.__news = None

    def set_scraper(self, scraper: Scraper):
        self.__scraper = scraper

    def scrap_news(self):
        self.__news = None
        if self.__scraper.get_response():
            self.__scraper.create_dom()
            self.__scraper.parse_news()
            self.__news = self.__scraper.collect_news()

    def get_news(self):
        return self.__news


if __name__ == "__main__":
    db_name = "news"
    mongo_db = MongoDB(db_name=db_name)

    data_list = [
        {
            "collection_name": 'yandex_news',
            'scraper': YandexScraper(),
            'unique_key': 'link'
        },

        {
            'collection_name': 'mail_news',
            'scraper': MailScraper(),
            'unique_key': 'link'
        },

        {
            "collection_name": 'lenta_news',
            'scraper': LentaScraper(),
            'unique_key': 'link'
        },
    ]

    builder = NewsScraper()

    for data in data_list:
        collection_name = data.get("collection_name")
        scraper = data.get("scraper")
        unique_key = data.get('unique_key')

        mongo_db.add_collection(collection_name=collection_name)
        builder.set_scraper(scraper=scraper)
        builder.scrap_news()
        news = builder.get_news()
        mongo_db.add_to_mongo_collection(data_list=news, collection_name=collection_name, unique_key=unique_key)
