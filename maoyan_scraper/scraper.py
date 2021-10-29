import io
from urllib import parse
import math
import requests
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup as bs
from typing import List, Tuple
import pandas as pd
from fontTools.ttLib import TTFont
import re

root_url = 'https://maoyan.com'
movie_index_path = 'board/4'


def main():
    # driver = webdriver.Firefox(executable_path='./geckodriver')  # Uncomment if using Firefox for Linux x64
    driver = webdriver.Firefox(executable_path='./geckodriver.exe')  # Uncomment if using Firefox for Windows

    movie_index = get_movie_index(driver)
    movie_detail = get_movie_detail(driver, movie_index)
    driver.close()

    movie_info = combine_movie_info(movie_index, movie_detail)
    movie_info.to_csv('./movie_info.csv')
    movie_info.to_excel('./movie_info.xlsx')


def get_movie_index(driver, offset: int = 0):
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
            stars: List[str] = entry.find('p', class_='star').get_text().strip()[3:].split(',')
            stars = [star.strip() for star in stars]
            rating_raw: str = entry.find('i', class_='integer').get_text().strip() + \
                              entry.find('i', class_='fraction').get_text().strip()
            rating: float = float(rating_raw)
            # store movie entry
            movie = {'rank': rank, 'title': title, 'link': link, 'stars': tuple(stars), 'rating': rating}
            movie_list.append(movie)

        offset += 10

    movie_index = pd.DataFrame(movie_list)
    return movie_index


def get_movie_detail(driver, movie_index):
    detail_list = []
    rank = 1

    while rank <= 100:
        driver.get(parse.urljoin(root_url, movie_index.query(f'rank == {rank}')['link'].values[0]))
        captcha_handler(driver)
        WebDriverWait(driver, timeout=10).until(lambda d: d.find_element(By.CLASS_NAME, 'tab-content-container'))
        source = driver.page_source
        source = bs(source, 'html.parser')

        detail = {'rank': rank}

        # type, country/region, length, release time, release place
        brief = source.find('div', class_='movie-brief-container').ul.findAll('li')
        types = [type_element.get_text().strip() for type_element in brief[0].findAll('a')]
        detail['types'] = tuple(types)
        country_region_and_length = brief[1].get_text().strip().split('/')
        detail['country/region'] = tuple(country_region_and_length[0].strip().split(','))
        detail['length'] = int(country_region_and_length[1].strip()[:-2])
        release_time_and_place = brief[2].get_text().strip()
        time_charset = '1234567890 -:'
        split_point = 0
        while release_time_and_place[split_point] in time_charset:
            split_point += 1
        detail['release time'] = release_time_and_place[:10]
        detail['release place'] = release_time_and_place[split_point:-2]

        # rater count
        font_url = re.findall("url\('(//vfile.meituan.net/colorstone/.+\.woff)'\)", source.prettify())[0]
        new_font = io.BytesIO(requests.get(f'http:{font_url}').content)
        new_font = TTFont(new_font)
        num_dict = translate_numbers(new_font)  # translated unicode -> number dictionary
        num_dict_keys = num_dict.keys()

        rater_raw = source.find('span', class_='score-num').get_text().strip()[:-3]
        rater = ''
        for index, character in enumerate(rater_raw):
            character_key = f'uni{character.encode("unicode_escape").decode()[-4:].upper()}'
            if character_key in num_dict_keys:
                rater += str(num_dict[character_key])
            else:
                rater += character

        if rater[-1] == '万':
            rater = round(float(rater[:-1]) * 10000)
        else:
            rater = int(rater)

        detail['rater count'] = rater

        # box office (may be unavailable)
        box = source.findAll('div', class_='film-mbox-item')
        try:
            detail['box office'] = int(box[1].div.get_text().strip())
        except (ValueError, IndexError):
            detail['box office'] = -1

        detail_list.append(detail)
        rank += 1

    movie_detail = pd.DataFrame(detail_list)
    return movie_detail


def combine_movie_info(movie_index, movie_detail):
    movie_info = pd.merge(movie_index, movie_detail, how='left', on='rank')
    return movie_info


def captcha_handler(driver):
    while '猫眼验证中心' in driver.page_source:  # wait for captcha to be manually solved
        driver.implicitly_wait(5)  # check the webpage once every 5 seconds


def translate_numbers(new_font) -> dict:
    base_font = TTFont('./iconfont.woff')
    char_list = [base_font['glyf']['uniF36C'],
                 base_font['glyf']['uniE0EB'],
                 base_font['glyf']['uniEB75'],
                 base_font['glyf']['uniF64C'],
                 base_font['glyf']['uniE6A2'],
                 base_font['glyf']['uniF5D3'],
                 base_font['glyf']['uniF5BB'],
                 base_font['glyf']['uniE307'],
                 base_font['glyf']['uniE47E'],
                 base_font['glyf']['uniE16B']]

    numbers_dictionary = {}
    for key in new_font['glyf'].keys():
        if 'uni' in key:
            numbers_dictionary[key] = match_char(char_list, new_font['glyf'][key])

    return numbers_dictionary


def distance(a: Tuple[int], b: Tuple[int]) -> float:
    return math.sqrt(((a[0] - b[0]) ** 2) + ((a[1] - b[1]) ** 2))


def nearest_point_distance(base_char, new_point: Tuple[int]) -> float:
    distances: List[float] = []
    for base_point in base_char.coordinates:
        distances.append(distance(base_point, new_point))
    return min(distances)


def match_char(char_list, new_char) -> int:
    if len(new_char.coordinates) < 10:
        return -1

    distance_list = []
    for base_char in char_list:
        avg_distance: float = 0
        for index, new_point in enumerate(new_char.coordinates):
            avg_distance += nearest_point_distance(base_char, new_point)
        avg_distance /= len(new_char.coordinates)
        distance_list.append(avg_distance)

    return distance_list.index(min(distance_list))


if __name__ == '__main__':
    main()
