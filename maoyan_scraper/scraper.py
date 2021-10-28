import os
import sys
from urllib import parse
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup as bs

# sys.path.append('./geckodriver.exe')  # Uncomment if using Firefox for Windows, comment otherwise
# sys.path.append('./geckodriver')  # Uncomment if using Firefox for Linux, comment otherwise

root_url = 'https://maoyan.com'
movie_index_path = 'board/4'


def captcha_handler(driver):
    while '猫眼验证中心' in driver.page_source:
        driver.implicitly_wait(5)


def get_movie_index(offset: int = 0):
    # driver = webdriver.Firefox(executable_path='./geckodriver')
    # driver.get(parse.urljoin(root_url, f'{movie_index_path}?offset={offset}'))
    # captcha_handler(driver)
    # WebDriverWait(driver, timeout=10).until(lambda d: d.find_element(By.TAG_NAME, 'dd'))
    # source = driver.page_source
    # source = bs(source, 'html.parser').prettify()
    #
    # with open(file='./dummy.html', mode='w', encoding='utf-8') as f:
    #     f.write(source)

    # Experiment with dummy start
    with open('./dummy.html', encoding='utf-8') as f:
        source = f.read()
    source = bs(source, 'html.parser').prettify()

    # elements = driver.find_elements(By.TAG_NAME, 'dd')
    # for e in elements:
    #     print(e.get_attribute('innerHTML'))


def main():
    get_movie_index()


if __name__ == '__main__':
    main()
