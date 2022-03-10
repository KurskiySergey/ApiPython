from selenium.webdriver import Chrome
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import os
from lesson5.mongo_db import MongoDB

# settings
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DRIVER_NAME = 'chromedriver.exe'
PATH = os.path.join(BASE_DIR, DRIVER_NAME)
options = Options()
options.add_argument("start-maximized")

# set driver
driver = Chrome(executable_path=PATH, options=options)
driver.implicitly_wait(20)


class Mail:
    def __init__(self, driver: Chrome, drop_db=False):
        self.driver = driver
        self.db_name = 'mail'
        self.collection_name = 'letters'
        self.info_collection_name = 'letters_info'
        self.db = MongoDB(db_name=self.db_name)
        if drop_db:
            self.db.drop_db()
        self.db.add_collection(self.collection_name)
        self.db.add_collection(self.info_collection_name)

    def login(self, login, password):
        self.driver.get("https://mail.ru/")
        element = driver.find_element(By.XPATH, "//button[contains(text(), 'Войти')]")
        element.click()
        element = self.driver.find_element(By.XPATH, "//iframe[contains(@src, 'mail.ru/login/')]")
        driver.switch_to.frame(element)
        element = self.driver.find_element(By.NAME, "username")
        element.send_keys(login)
        element.send_keys(Keys.ENTER)
        element = self.driver.find_element(By.NAME, "password")
        element.send_keys(password)
        element.send_keys(Keys.ENTER)
        self.driver.switch_to.parent_frame()

    def __get_msg_info(self, element):
        element.send_keys(Keys.CONTROL + Keys.ENTER)
        window_handlers = self.driver.window_handles
        self.driver.switch_to.window(window_handlers[-1])
        contact = self.driver.find_element(By.CLASS_NAME, 'letter-contact').get_attribute('title')
        date = self.driver.find_element(By.CLASS_NAME, 'letter__date').text
        theme = self.driver.find_element(By.CLASS_NAME, 'thread__header').text
        text = self.driver.find_element(By.CLASS_NAME, 'letter__body').text
        self.driver.close()
        self.driver.switch_to.window(window_handlers[0])

        info = {
            'date': date,
            'contact': contact,
            'theme': theme,
            'text': text
        }

        return info

    def get_letters(self, message_limit=100):
        total_count = 0
        while total_count < message_limit:
            letters = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/inbox/0')]")
            add_letters = []
            letters_info = []
            for letter in letters:
                href = letter.get_attribute('href')
                if not self.db.check_data(key='href', data=href, collection_name=self.collection_name):
                    add_letters.append(href)
                    info = self.__get_msg_info(letter)
                    info.update({'href': href})
                    letters_info.append(info)
                    total_count += 1
                    if total_count == message_limit:
                        break

            self.db.add_to_mongo_collection(data_list=[{'href': letter} for letter in add_letters],
                                            collection_name=self.collection_name, unique_key='href')
            self.db.add_to_mongo_collection(data_list=letters_info,
                                            collection_name=self.info_collection_name, unique_key='href')

            self.driver.find_element(By.XPATH, "//a[contains(@href, '/inbox/0')]").send_keys(Keys.PAGE_DOWN)


if __name__ == "__main__":
    login = "study.ai_172@mail.ru"
    password = "NextPassword172#"
    message_limit = 10

    mail = Mail(driver=driver, drop_db=True)
    mail.login(login=login, password=password)
    mail.get_letters(message_limit=message_limit)
