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

    def scrape_compare_MITPress(self, root, lockedVolumes=[], startVolume='1989'):
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
            issue_names = [f.name.split()[-1] for f in os.scandir(cwd) if f.is_dir()]
            return bool(issue in issue_names)

        def getCurrentIssuePDFs(cwd, issue):
            issue_names = [f.name.split()[-1] for f in os.scandir(cwd) if f.is_dir()]
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
            issue_names = [f.name.split()[-1] for f in os.scandir(cwd) if f.is_dir()]
            return int(issue) > max([int(name) for name in issue_names])

        def volumeExists(volume):
            volume_names = [f.name.split()[-1] for f in os.scandir(root) if f.is_dir()]
            return bool(volume in volume_names)

        def isNewestVolume(volume):
            volume_names = [f.name for f in os.scandir(root) if f.is_dir()]
            return int(volume) > max([int(name) for name in volume_names])

        ###### main looping logic ########

        cwd = root
        volume_dirs = [f for f in os.scandir(cwd) if f.is_dir()]
        articles = [] # output
        all_missed_illegal_chars = []
        volume = int(startVolume) - 1988
        soup = validateURL(f"https://www.mitpressjournals.org/toc/jocn/{volume}/1")
        while soup: # volume

            DOWNLOAD_FLAG_OVERRIDE = None
            # does the volume not exist?
            if not volumeExists(str(volume + 1988)):
                print('new volume found:', str(volume + 1988))
                # is it the newest issue?
                if isNewestVolume(str(volume + 1988)):
                    # file was not found, and is in most recent issue
                    DOWNLOAD_FLAG_OVERRIDE = 'DOWNLOAD'
                else:
                    # human must review the potential new file
                    DOWNLOAD_FLAG_OVERRIDE = 'NO MATCH FOUND'
                print('APPLYING OVERRIDE SETTING:', DOWNLOAD_FLAG_OVERRIDE)
            else:                  
                # volume exists, update cwd
                cwd = [vol.path for vol in volume_dirs if str(int(vol.name)-1988) == str(volume)][0]
            
            if str(volume+1988) not in lockedVolumes:
                start_time = time.time()
                
                # counters for volume
                issue = 1
                missed_illegal_chars_volume = []
                match_found_count = 0
                no_match_found_count = 0
                download_count = 0
                
                while soup: # issue

                    # get issue information
                    urls = getUrls(soup)
                    (allAuthorsFull, allAuthorsAbbrv)  = getNames(soup)
                    (titlesFull, titlesAbbrv)  = getTitles(soup) 
                    years = getYears(soup)
                    dois = [''.join(["https://doi.org/", '/'.join(url.split('/')[-2:])]) for url in urls]

                    # build article objects
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


                        ########## DETERMINE DOWNLOAD FLAG FOR ISSUE ############
                        downloadFlag = None
                        if DOWNLOAD_FLAG_OVERRIDE != None:
                            downloadFlag = DOWNLOAD_FLAG_OVERRIDE
                            if DOWNLOAD_FLAG_OVERRIDE == 'NO MATCH FOUND':
                                no_match_found_count += 1
                            else:
                                download_count += 1
                        else:
                            # does the issue currently exist?
                            if issueExists(cwd, str(issue)):
                                if fileFound(a, cwd, str(issue)):
                                    # file was found
                                    downloadFlag = 'MATCH FOUND'
                                    match_found_count += 1
                                else:
                                    # human must review the potential new file
                                    downloadFlag = 'NO MATCH FOUND'
                                    no_match_found_count += 1
                            else:
                                # is it the newest issue?
                                if isNewestIssue(cwd, str(issue)):
                                    # file was not found, and is in most recent issue
                                    downloadFlag = 'DOWNLOAD'
                                    download_count += 1
                                else:
                                    # human must review the potential new file
                                    downloadFlag = 'NO MATCH FOUND'
                                    no_match_found_count += 1
                        

                        a.downloadFlag = downloadFlag

                        
                        
                    
                        articleDict = a.asdict()
                        articles.append(articleDict)
                    
                    # move on to next issue
                    issue += 1
                    soup = validateURL(f"https://www.mitpressjournals.org/toc/jocn/{volume}/{issue}")
                
                # finished volume
                print('RUN TIME:' , round(time.time()- start_time, 1), 's')
                print('ISSUES:', issue-1)
                print('MISSED ILLEGAL CHARS:', missed_illegal_chars_volume)
                print('MATCH FOUND COUNT:', match_found_count)
                print('NO MATCH FOUND COUNT:', no_match_found_count)
                print('DOWNLOAD COUNT:', download_count)
                all_missed_illegal_chars.extend(missed_illegal_chars_volume)
                print(f'-------- reached end of volume {volume} ({years[0]}) ----------------')
            
            else:
                # locked volume
                print(f'--------  volume {volume+1988} has been locked. Skipping  ----------------')
        
            volume += 1
            soup = validateURL(f"https://www.mitpressjournals.org/toc/jocn/{volume}/1")

        # finished journal
        print(f'reached end of {volume-1} volumes')
        print('All missed illegal chars:', all_missed_illegal_chars)
        print('done scraping!')

        return articles


scraper = JournalScraper()
journalRoot = r'D:\ft\ft-j1\J Cognitive Neuroscience+'
articles = scraper.scrape_compare_MITPress(root=journalRoot)
CSV_PATH = r'C:\Users\grego\Documents\GitHub\JOCNScraper\csvs\MITPress_with_flags.csv'
columns = ['Journal', 'Volume', 'Year', 'Issue', 'Title', 'Authors', 'FileName', 'URL', 'DOI', 'IllegalTitleChars', 'IllegalAuthorsChars', 'DownloadFlag']
df = pd.DataFrame(articles, columns=columns)
df.to_csv(CSV_PATH, index=False)
print('done!')