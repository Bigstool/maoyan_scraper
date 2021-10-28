import os
import sys
from urllib import parse
import numpy as np
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup as bs
from typing import List
import pandas as pd

root_url = 'https://maoyan.com'
movie_index_path = 'board/4'


def captcha_handler(driver):
    while '猫眼验证中心' in driver.page_source:  # wait for captcha to be manually solved
        driver.implicitly_wait(5)  # check the webpage once every 5 seconds


def get_movie_index(offset: int = 0):
    driver = webdriver.Firefox(executable_path='./geckodriver')  # Uncomment if using Firefox for Linux x64
    # driver = webdriver.Firefox(executable_path='./geckodriver.exe')  # Uncomment if using Firefox for Windows

    movie_list = []

    while offset < 100:
        driver.get(parse.urljoin(root_url, f'{movie_index_path}?offset={offset}'))
        captcha_handler(driver)
        WebDriverWait(driver, timeout=10).until(lambda d: d.find_element(By.TAG_NAME, 'dd'))  # wait for element to load
        source = driver.page_source
        source = bs(source, 'html.parser')

        movie_entries = source.find_all('dd')
        for entry in movie_entries:
            # acquire values
            rank: int = int(entry.i.get_text().strip())  # strip() removes whitespace
            link: str = entry.a.get('href')
            title: str = entry.a.get('title')
            stars: str = entry.find('p', class_='star').get_text().strip()[3:]
            time: str = entry.find('p', class_='releasetime').get_text().strip()[5:]
            rating_raw: str = entry.find('i', class_='integer').get_text().strip() + \
                              entry.find('i', class_='fraction').get_text().strip()
            rating: float = float(rating_raw)
            # process time information
            if '(' in time:
                time = time[:time.index('(')]
            time: List[str] = time.split('-')
            year: int = int(time[0]) if len(time) > 0 else -1
            month: int = int(time[1]) if len(time) > 1 else -1
            day: int = int(time[2]) if len(time) > 2 else -1
            # store movie entry
            movie = {'rank': rank, 'title': title, 'link': link, 'stars': stars,
                     'year': year, 'month': month, 'day': day, 'rating': rating}
            movie_list.append(movie)

        offset += 10

    for movie in movie_list:
        print(movie)

    frame = pd.DataFrame(movie_list)
    print(frame.head(15))
    frame.to_csv('./movie_index.csv')


    # elements = driver.find_elements(By.TAG_NAME, 'dd')
    # for e in elements:
    #     print(e.get_attribute('innerHTML'))


def main():
    get_movie_index()


if __name__ == '__main__':
    main()
