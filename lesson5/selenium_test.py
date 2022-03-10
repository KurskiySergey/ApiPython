from selenium.webdriver import Chrome
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import os
import time

# settings
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DRIVER_NAME = 'chromedriver.exe'
PATH = os.path.join(BASE_DIR, DRIVER_NAME)
options = Options()
options.add_argument("start-maximized")

# set driver
driver = Chrome(executable_path=PATH, options=options)
driver.implicitly_wait(10)

# test run
driver.get("https://www.google.ru/")
window_handle = driver.window_handles[0]
element = driver.find_element(By.XPATH, '//input')
element.send_keys('Гардемарины')
element.send_keys(Keys.ENTER)
element = driver.find_element(By.XPATH, "//div[@id='rso']//a")
element.click()
driver.switch_to.window(driver.window_handles[-1])
driver.execute_script("window.scrollBy(0,document.body.scrollHeight)")
time.sleep(2)
driver.close()
driver.switch_to.window(window_handle)
for _ in range(3):
    element.send_keys(Keys.PAGE_DOWN)
element = driver.find_element(By.ID, 'pnnext')
element.click()
time.sleep(1)
driver.quit()
