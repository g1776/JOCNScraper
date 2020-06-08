from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from nameparser import HumanName
from pathvalidate import sanitize_filename
import time
import pandas as pd
import string
from unidecode import unidecode
import os


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
        self.illegalTitleChars = None
        self.illegalAuthorsChars = None
        self.downloadFlag = None # MATCH FOUND, MATCH NOT FOUND, DOWNLOAD
    
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
        'DOI': self.doi,
        'IllegalTitleChars': self.illegalTitleChars,
        'IllegalAuthorsChars': self.illegalAuthorsChars,
        'DownloadFlag': self.downloadFlag  
        }

    __str__=__repr__


class JournalScraper():

    CHROMEDRIVER_PATH = r"C:\Users\grego\Documents\GitHub\JOCNScraper\chromedriver.exe"
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--log-level=3") # shut up the driver
    driver = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH, options=chrome_options)

    def scrape_compare_MITPress(self,  root='', lockedVolumes=[]):
        '''
        root: path to root of directory to compare found files against
        lockedVolumes: list of strings defining which volumes to ignore
        '''

        #### helper functions that are called for each issue #######

        def validateURL(url):
            self.driver.get(url)
            html = self.driver.page_source
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
                # find and transiliterate the author names
                authorsLastNames = [unidecode(HumanName(author.text).last) for author in authorList.find_all('a', attrs={'class': 'entryAuthor linkable hlFld-ContribAuthor'})]
                authorsFull = ''.join([unidecode(string.text) for string in authorList.find_all()])
                if len(authorsLastNames) == 1:
                    authorsAbbrv = authorsLastNames[0]
                elif len(authorsLastNames) == 2:
                    authorsAbbrv = authorsLastNames[0] + ' & ' + authorsLastNames[1]
                else:
                    authorsAbbrv = authorsLastNames[0] + ' et al'
                
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
            # find and transiliterate the titles
            titlesFull =  [unidecode(title.text) for title in soup.findAll('span', attrs={'class': 'hlFld-Title'})]
            titlesAbbrv = []
            for title in titlesFull:
                if len(title) > 150:
                    titlesAbbrv.append(title[:150])
                else:
                    titlesAbbrv.append(title)

            return (titlesFull, titlesAbbrv)

        
        def issueExists(cwd, issue):
            issue_names = [f.name for f in os.scandir(cwd) if f.is_dir()]
            return bool(issue in issue_names)

        def getCurrentIssuePDFs(cwd, issue):
            issue_names = [f.name for f in os.scandir(cwd) if f.is_dir()]
            currentIssue_index = issue_names.index(issue)
            issue_paths = [f.path for f in os.scandir(cwd) if f.is_dir()]
            currentIssue_path = issue_paths[currentIssue_index]

            # get all pdfs in current issue
            extensions = ['pdf']
            return [f.name for f in os.scandir(currentIssue_path) if not f.is_dir() and f.path.split('.')[-1] in extensions]
        
        def fileFound(theFile, cwd, issue):
            currentIssuePDFs_names = getCurrentIssuePDFs(cwd, issue)
            # logic to compare files
            return bool(theFile.fileName in currentIssuePDFs_names)

        def isNewestIssue(cwd, issue):
            issue_names = [f.name for f in os.scandir(cwd) if f.is_dir()]
            return not bool(True in [issue < an_issue for an_issue in issue_names])

        ###### main looping logic ########

        cwd = root
        volume_dirs = [f for f in os.scandir(cwd) if f.is_dir()]
        articles = [] # output
        all_missed_illegal_chars = []
        volume = 1
        soup = validateURL(f"https://www.mitpressjournals.org/toc/jocn/{volume}/1")
        while soup: # volume
            # update cwd
            cwd = [vol.path for vol in volume_dirs if vol.name == str(volume)][0]
            if str(volume) not in lockedVolumes:
                start_time = time.time()
                issue = 1
                missed_illegal_chars_volume = []
                while soup: # issue

                    # get information
                    urls = getUrls(soup)
                    (allAuthorsFull, allAuthorsAbbrv)  = getNames(soup)
                    (titlesFull, titlesAbbrv)  = getTitles(soup) 
                    years = getYears(soup)
                    dois = [''.join(["https://doi.org/", '/'.join(url.split('/')[-2:])]) for url in urls]

                    # build article object
                    data = zip(urls, allAuthorsFull, allAuthorsAbbrv, dois, titlesFull, titlesAbbrv, years)
                    for url, authorsFull, authorsAbbrv, doi, titleFull, titleAbbrv, year in data:
                        
                        illegal_title_chars_bool = False
                        illegal_authors_chars_bool = False
                        

                        # second pass for illegal chars that were not transliterated
                        for element in [titleFull, titleAbbrv]:
                            for i, char in enumerate(element):
                                if char not in string.printable:
                                    illegal_title_chars_bool = True
                                    missed_illegal_chars_volume.append(char)
                                    element[i] = '~'
                        for element in [authorsFull, authorsAbbrv]:
                            for i, char in enumerate(element):
                                if char not in string.printable:
                                    illegal_authors_chars_bool = True
                                    missed_illegal_chars_volume.append(char)
                                    element[i] = '~'


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
                        a.illegalTitleChars = illegal_title_chars_bool
                        a.illegalAuthorsChars = illegal_authors_chars_bool

                        
                        ########## COMPARE TO EXISTING DIRECTORY ############

                        # does the issue currently exist?
                        if issueExists(cwd, str(issue)):
                            if fileFound(a, cwd, issue):
                                # file was found
                                a.downloadFlag = 'MATCH FOUND'
                                articleDict = a.asdict()
                                articles.append(articleDict)
                            else:
                                # human must review the potential new file
                                a.downloadFlag = 'NO MATCH FOUND'
                                articleDict = a.asdict()
                                articles.append(articleDict) 
                        else:
                            # is it the newest issue?
                            if isNewestIssue(cwd, issue):
                                # file was not found, and is in most recent issue
                                a.downloadFlag = 'DOWNLOAD'
                                articleDict = a.asdict()
                                articles.append(articleDict)
                            else:
                                # human must review the potential new file
                                a.downloadFlag = 'NO MATCH FOUND'
                                articleDict = a.asdict()
                                articles.append(articleDict) 

                    
                    # finished issue
                    issue += 1
                    soup = validateURL(f"https://www.mitpressjournals.org/toc/jocn/{volume}/{issue}")
                
                # finished volume
                print('RUN TIME:' , round(time.time()- start_time, 1), 's')
                print('MISSED ILLEGAL CHARS:', missed_illegal_chars_volume)
                all_missed_illegal_chars.extend(missed_illegal_chars_volume)
                print(f'-------- reached end of volume {volume} ({years[0]}) ----------------')
            
            else:
                # locked volume
                print(f'--------  volume {volume} has been locked. Skipping  ----------------')
            volume += 1
            soup = validateURL(f"https://www.mitpressjournals.org/toc/jocn/{volume}/1")

        # finished journal
        print(f'reached end of {volume-1} volumes')
        print('All missed illegal chars:', all_missed_illegal_chars)
        print('done scraping!')

        return articles


scraper = JournalScraper()
articles = scraper.scrape_compare_MITPress()
CSV_PATH = r'C:\Users\grego\Documents\GitHub\JOCNScraper\csvs\normalized_illegal_characters.csv'
columns = ['Journal', 'Volume', 'Year', 'Issue', 'Title', 'Authors', 'FileName', 'URL', 'DOI', 'IllegalTitleChars', 'IllegalAuthorsChars, DownloadFlag']
df = pd.DataFrame(articles, columns=columns)
df.to_csv(CSV_PATH, index=False)
print('done!')


