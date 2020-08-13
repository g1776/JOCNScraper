from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from nameparser import HumanName
from pathvalidate import sanitize_filename
import time
import pandas as pd
import string
from unidecode import unidecode
import os



CHROMEDRIVER_PATH = r"chromedriver.exe"
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless") 
chrome_options.add_argument("--log-level=3") # shut up the driver
driver = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH, options=chrome_options)

def getDois(soup):

    num_articles = len(soup.find_all('li', attrs={'class': 'js-article-list-item article-item u-padding-xs-top u-margin-l-bottom'}))
    print(num_articles)
    dois = []

    for i in range(num_articles):
        css_selector = f'#article-list > form > div > div.u-margin-xs-top.u-margin-xs-bottom.col-md-18.move-right > ol > li:nth-child({i+1}) > div:nth-child(2)'
        dois.append(soup.select(css_selector)[0].text)
    return dois

url = r'https://www.sciencedirect.com/journal/neuroimage/vol/10/issue/6'
driver.get(url)
html = driver.page_source
soup = BeautifulSoup(html, 'html.parser')
dois = getDois(soup)



