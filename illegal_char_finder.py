from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from nameparser import HumanName
from pathvalidate import sanitize_filename
import time
import pandas as pd
import string


# setup
CHROMEDRIVER_PATH = r"C:\Users\grego\Documents\GitHub\JOCNScraper\chromedriver.exe"
CSV_PATH = r'C:\Users\grego\Documents\GitHub\JOCNScraper\MITPressJOCNArticles.csv'
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless") 
chrome_options.add_argument("--log-level=3") # shut up the driver
driver = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH, options=chrome_options)

def validateURL(url):
    driver.get(url)
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    theTitle = soup.find('title').text
    if theTitle == 'Error | MIT Press Journals':
        return None
    return soup

def getNames(soup):

    allAuthorsFull = []
    authorListsHTML = soup.find_all('span', attrs={'class': 'articleEntryAuthorsLinks'})
    for authorList in authorListsHTML:
        authorsLastNames = [HumanName(author.text).last for author in authorList.find_all('a', attrs={'class': 'entryAuthor linkable hlFld-ContribAuthor'})]
        authorsFull = ''.join([string.text for string in authorList.find_all()])
        
        # filter out non-printable characters
        # authorsFull = ''.join(filter(lambda x: x in string.printable, authorsFull))

        allAuthorsFull.append(authorsFull)
    return allAuthorsFull

def getTitles(soup):
    titlesFull =  [title.text for title in soup.findAll('span', attrs={'class': 'hlFld-Title'})]

    # filter out non-printable characters
    # titlesFull = ''.join(filter(lambda x: x in string.printable, titlesFull))
    
    return titlesFull

illegal_auth_chars = []
illegal_title_chars = []
volume = 1
currentURL = f"https://www.mitpressjournals.org/toc/jocn/{volume}/1"
soup = validateURL(f"https://www.mitpressjournals.org/toc/jocn/{volume}/1")
while soup: # volumes
    start_time = time.time()
    issue = 1
    while soup: # issues
        # get information
        allAuthorsFull  = getNames(soup)
        titlesFull  = getTitles(soup)

        # iterate through articles
        for authorsFull, titleFull in zip(allAuthorsFull, titlesFull):

            # append to illegal lists
            _ = [illegal_auth_chars.append(u''.join([c])) for c in authorsFull if bool(c not in string.printable and c not in illegal_auth_chars)]
            _ = [illegal_title_chars.append(u''.join([c])) for c in titleFull if bool(c not in string.printable and c not in illegal_title_chars)] 
        # get ready for next issue
        issue += 1 
        soup = validateURL(f"https://www.mitpressjournals.org/toc/jocn/{volume}/{issue}")

    # get ready for next volume
    print('RUN TIME:' , round(time.time()- start_time, 1), 's')
    print('Illegal Auth Chars:', illegal_auth_chars)
    print('Illegal Title Chars:', illegal_title_chars)
    print(f'-------- reached end of volume {volume} ----------------')
    volume += 1
    soup = validateURL(f"https://www.mitpressjournals.org/toc/jocn/{volume}/1")


print(f'reached end of {volume-1} volumes')
print('outputting')
illegal_auth_chars_path = r'C:\Users\grego\Documents\GitHub\JOCNScraper\txts\illegal_auth_chars.txt'
illegal_title_chars_path = r'C:\Users\grego\Documents\GitHub\JOCNScraper\txts\illegal_title_chars.txt'
with open(illegal_auth_chars_path, "w") as outfile:
    outfile.write("\n".join(illegal_auth_chars))
with open(illegal_title_chars_path, "w") as outfile:
    outfile.write("\n".join(illegal_title_chars))
print('done!')