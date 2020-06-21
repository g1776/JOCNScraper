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

def download(row, target_root):
    url = row['URL']
    volume = row['Volume']
    issue = row['Issue']
    filename = row['FileName']

    if not os.path.exists(target_root):
        raise BaseException('ERROR: Target root directory does not exist!')

    # determine "No" or "Iss" for issue
    if volume + 1988 < 2007:
        issue_prefix = 'No'
    else:
        issue_prefix = 'Iss'

    # check if target volume exists
    target_volume = f'{target_root}/{volume+1988}'
    if not os.path.exists(target_volume):
        os.makedirs(target_volume)
        print(f'making directory {target_volume}')
    
    # check if target issue exists
    target_issue = f'{target_root}/{volume+1988}/Vol {volume} {issue_prefix} {issue}'
    if not os.path.exists(target_issue):
        os.makedirs(target_issue)
        print(f'making directory {target_issue}')

    spec = target_issue + f'/{filename}'
    try:
        # get file at url and download to spec location
        urllib.request.urlretrieve(url, spec)
        return 1
    except:
        print(f'ERROR DOWNLOADING {url}')
        return 0


#### driver code ####

output = r'output.csv'
# root_JOCN = r'O:\ft\ft-j1\J Cognitive Neuroscience+'
root_JOCN = r'C:\Users\LocalUser\Documents\testDir'

df = pd.read_csv(output)
for _, row in df.iterrows():
    if row['DownloadFlag'] == 'DOWNLOAD':
        if row['Journal'] == 'J of Cognitive Neuroscience':
            download(row, root_JOCN)

