from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from nameparser import HumanName
from pathvalidate import sanitize_filename
import time
import pandas as pd
import string
from unidecode import unidecode


class Article():
    def __init__(self):
        self.journal = None
        self.volume = None
        self.year = None
        self.issue = None
        self.title = None
        self.authors = None
        self.fileName = None
        self.url = None
        self.doi = None
    
    def __repr__(self):
        return self.fileName
    
    def asdict(self):
        return {
        'Journal': self.journal,
        'Volume': self.volume,
        'Year': self.year,
        'Issue': self.issue,
        'Title': self.title,
        'Authors': self.authors,
        'FileName': self.fileName,
        'URL': self.url,
        'DOI': self.doi
        }

    __str__=__repr__


# setup
CHROMEDRIVER_PATH = r"C:\Users\grego\Documents\GitHub\JOCNScraper\chromedriver.exe"
CSV_PATH = r'C:\Users\grego\Documents\GitHub\JOCNScraper\csvs\normalized_illegal_characters.csv'
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
    '''
        returns (allAuthorsFull, allAuthorsAbbrv)
    '''
    allAuthorsAbbrv = []
    allAuthorsFull = []
    authorListsHTML = soup.find_all('span', attrs={'class': 'articleEntryAuthorsLinks'})
    for authorList in authorListsHTML:
        authorsLastNames = [unidecode(HumanName(author.text).last) for author in authorList.find_all('a', attrs={'class': 'entryAuthor linkable hlFld-ContribAuthor'})]
        authorsFull = ''.join([unidecode(string.text) for string in authorList.find_all()])
        if len(authorsLastNames) == 1:
            authorsAbbrv = authorsLastNames[0]
        elif len(authorsLastNames) == 2:
            authorsAbbrv = authorsLastNames[0] + ' & ' + authorsLastNames[1]
        else:
            authorsAbbrv = authorsLastNames[0] + ' et al'
        
        # filter out non-printable characters
        # authorsAbbrv = ''.join(filter(lambda x: x in string.printable, authorsAbbrv))
        # authorsFull = ''.join(filter(lambda x: x in string.printable, authorsFull))

        allAuthorsAbbrv.append(authorsAbbrv)
        allAuthorsFull.append(authorsFull)
    return (allAuthorsFull, allAuthorsAbbrv)

def getUrls(soup):
    return [''.join([r"https://www.mitpressjournals.org", pdfLink['href']]) for pdfLink in soup.find_all('a', attrs={'class': 'ref nowrap pdf'})]

def getYears(soup):
    years = []
    for issueInfo in soup.findAll('span', attrs={'class': 'issueInfo'}):
        issueInfo_list = issueInfo.text.split()
        if '2001,' in issueInfo_list or '2002,' in issueInfo_list or '2003,' in issueInfo_list:
            years.append(issueInfo_list[6][:-1])
        else:
            years.append(issueInfo_list[5][:-1])
        
    return years

def getTitles(soup):
    titlesFull =  [unidecode(title.text) for title in soup.findAll('span', attrs={'class': 'hlFld-Title'})]
    titlesAbbrv = []
    for title in titlesFull:
        if len(title) > 150:
            titlesAbbrv.append(title[:150])
        else:
            titlesAbbrv.append(title)

    # filter out non-printable characters
    # titlesFull = ''.join(filter(lambda x: x in string.printable, titlesFull))
    # titlesAbbrv = ''.join(filter(lambda x: x in string.printable, titlesAbbrv))
    
    return (titlesFull, titlesAbbrv)

articles = [] # output
volume = 1
currentURL = f"https://www.mitpressjournals.org/toc/jocn/{volume}/1"
soup = validateURL(f"https://www.mitpressjournals.org/toc/jocn/{volume}/1")
while soup: # volumes
    start_time = time.time()
    issue = 1
    while soup: # issues
        # get information
        urls = getUrls(soup)
        (allAuthorsFull, allAuthorsAbbrv)  = getNames(soup)
        (titlesFull, titlesAbbrv)  = getTitles(soup)
        years = getYears(soup)
        dois = [''.join(["https://doi.org/", '/'.join(url.split('/')[-2:])]) for url in urls]

        # build article object
        data = zip(urls, allAuthorsFull, allAuthorsAbbrv, dois, titlesFull, titlesAbbrv, years)
        for url, authorsFull, authorsAbbrv, doi, titleFull, titleAbbrv, year in data:
            a = Article()
            a.journal = 'J of Cognitive Neuroscience'
            a.volume = volume
            a.year = year
            a.issue = issue
            a.title = titleFull
            a.authors = authorsFull
            a.fileName = sanitize_filename(f'{authorsAbbrv}_{titleAbbrv}_{year}.pdf')
            a.url = url
            a.doi = doi

            articleDict = a.asdict()
            articles.append(articleDict)
        
        # get ready for next issue
        issue += 1
        soup = validateURL(f"https://www.mitpressjournals.org/toc/jocn/{volume}/{issue}")
    
    # get ready for next volume
    print('RUN TIME:' , round(time.time()- start_time, 1), 's')
    print(f'-------- reached end of volume {volume} ({years[0]}) ----------------')
    volume += 1
    soup = validateURL(f"https://www.mitpressjournals.org/toc/jocn/{volume}/1")


print(f'reached end of {volume-1} volumes')

df = pd.DataFrame(articles, columns=['Journal', 'Volume', 'Year', 'Issue', 'Title', 'Authors', 'FileName', 'URL', 'DOI'])
df.to_csv(CSV_PATH, index=False)
print('done!')

# df = pd.DataFrame(data, columns=[Journal, Volume, Year, Issue, Title, Authors, FileName, URL, DOI])

# EXAMPLE:
# [J of Congnitive Neuroscience, 
# 32, 
# 2020, 
# 6, 
# Brain Regions Involved in Conceptual Retrieval in Sighted and Blind People,
# Robert Bottini, Stefania Ferraro, Anna Nigri, Valeria Cuccarini, Maria Grazia Bruzzone, and Olivier Collingnon,
# FileName,
# URL,
# https://doi.org/10.1162/jocn_a_01538
# ]


