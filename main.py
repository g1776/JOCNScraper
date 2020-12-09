from selenium import webdriver
import pandas as pd
import urllib.request
import os

from scrapers import JOCN, Neuroimage
from downloaders import JOCN_d


def scrape():
    CHROMEDRIVER_PATH = r"chromedriver.exe"
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--log-level=3") # shut up the driver
    driver = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH, options=chrome_options)
    
    # define scrapers
    articles = []

    # a change

    ###############################################################

    # root_JOCN = r'D:\ft\ft-j1\J Cognitive Neuroscience+'
    # articles.append(JOCN.scrape(root_JOCN, driver))

    root_NeuroImage = r'C:\Users\grego\Documents\GitHub\JOCNScraper\testDir'
    articles.append(Neuroimage.scrape(root_NeuroImage, driver))

    ###############################################################

    columns = ['Journal', 'Volume', 'Year', 'Issue', 'Title', 'Authors', 'FileName', 'URL', 'DOI', 'IllegalTitleChars', 'IllegalAuthorsChars', 'DownloadFlag']
    df = pd.DataFrame(articles, columns=columns)
    CSV_PATH = 'output.csv'
    df.to_csv(CSV_PATH, index=False)
    print('done!')

def download(root, csv, downloaders):
    df = pd.read_csv(csv)
    for _, row in df.iterrows():
        if row['DownloadFlag'] == 'DOWNLOAD':
                downloaders[row['Journal']](row, root) # the actual downloading happens here

#### driver code ####

# scrape #
# scrape()

# download #

root = r'C:\Users\grego\Documents\GitHub\JOCNScraper\testDir\2001'
csv = 'output.csv'
downloaders = {
    'J of Cognitive Neuroscience': JOCN_d.download
}

download(root, csv, downloaders)


