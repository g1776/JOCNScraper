from selenium import webdriver
import pandas as pd
import urllib.request
import os

from scrapers import JOCN


def scrape():
    CHROMEDRIVER_PATH = r"chromedriver.exe"
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--log-level=3") # shut up the driver
    driver = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH, options=chrome_options)
    
    # define scrapers
    articles = []

    root_JOCN = r'D:\ft\ft-j1\J Cognitive Neuroscience+'
    articles.append(JOCN.scrape(root_JOCN, driver))

    columns = ['Journal', 'Volume', 'Year', 'Issue', 'Title', 'Authors', 'FileName', 'URL', 'DOI', 'IllegalTitleChars', 'IllegalAuthorsChars', 'DownloadFlag']
    df = pd.DataFrame(articles, columns=columns)
    CSV_PATH = 'output.csv'
    df.to_csv(CSV_PATH, index=False)
    print('done!')

def download(row, root):
    url = row['URL']
    volume = row['Volume']
    issue = row['Issue']
    filename = row['FileName']

    if not os.path.exists(root):
        raise BaseException('ERROR: Root directory does not exist!')

    # determine "No" or "Iss" for issue
    if volume + 1988 < 2007:
        issue_prefix = 'No'
    else:
        issue_prefix = 'Iss'

    spec = f'{root}/{volume+1988}/Vol {volume} {issue_prefix} {issue}/{filename}'
    try:
        # get file at url and download to spec location
        urllib.request.urlretrieve(url, spec)
        return 1
    except:
        print(f'ERROR DOWNLOADING {url}')
        return 0


#### driver code ####

download_csv = r'output.csv'
journal_root = r'O:\ft\ft-j1\J Cognitive Neuroscience+'

df = pd.read_csv(download_csv)
for _, row in df.iterrows():
    if row['DownloadFlag'] == 'DOWNLOAD':
        download(row, journal_root)

