import os
import sys
from urllib import parse
from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup as bs

sys.path.append('./geckodriver.exe')

root_url = 'https://maoyan.com'
movie_index_path = 'board/4'


def get_movie_index(offset: int = 0):
    browser = webdriver.Firefox()
    browser.get(parse.urljoin(root_url, f'{movie_index_path}?offset={offset}'))
    elements = browser.find_elements(By.TAG_NAME, 'dd')
    for e in elements:
        print(e.source)


def main():
    get_movie_index()


if __name__ == '__main__':
    main()
