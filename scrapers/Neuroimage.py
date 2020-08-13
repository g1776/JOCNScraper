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
from .article import Article


def scrape(root, driver, lockedVolumes=[], startVolume='1991'):
    '''
    root: path to root of directory to compare found files against
    lockedVolumes: list of strings defining which volumes to ignore
    '''

    ##### WARNING - 
    # the term "volume" is misleading in this scraper. 
    # the volume variable contains the volume in the 'year' key
    # and the issue in the 'link' key

    #### helper functions that are called for each issue #######

    def getVolumes(years_url):

        '''
        returns list of dicts
        '''

        print('loading journal webpage...')
        driver.get(years_url)
        expand_buttons = []
        years_per_page = 20
        for i in range(years_per_page):
            try:
                button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, f'0-accordion-tab-{i}')))
            except:
                # reached end of buttons
                break
            expand_buttons.append(button)
        print('buttons expanded!')
        [expand_button.click() for expand_button in expand_buttons] # click buttons
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        accordions = soup.find_all('li', attrs={'class': 'accordion-panel js-accordion-panel'})
        volumes = []
        for accordion in accordions:
            year = accordion.find('span', attrs={'class': 'accordion-title js-accordion-title'}).text[:4]
            a_tags = accordion.find_all('a', attrs={'class': 'anchor js-issue-item-link text-m'})
            
            for a_tag in a_tags:
                name = a_tag.text[:-1]
                link = r'https://www.sciencedirect.com' + a_tag['href']
                volumes.append({
                    "name": name, 
                    "link": link,
                    "year": str(year)
                })
        
        # list is currently backwards
        volumes.reverse()
        
        return volumes

    def getNames(soup):
        '''
            returns (allAuthorsFull, allAuthorsAbbrv)
        '''
        allAuthorsAbbrv = []
        allAuthorsFull = []
        all_authors = [div.text for div in soup.find_all('div', attrs={'class': 'text-s u-clr-grey8 js-article__item__authors'})]
        for authors in all_authors:
            authors_splitted = authors.split(sep=", ")
            # find and transiliterate the author names
            authorsAbbrv = [unidecode(HumanName(author).last) for author in authors_splitted][0] # last name of first author
            authorsFull = ', '.join([unidecode(author) for author in authors_splitted])
            allAuthorsFull.append(authorsFull)
            allAuthorsAbbrv.append(authorsAbbrv)
            
        return (allAuthorsFull, allAuthorsAbbrv)


    def getUrls(soup):
        return [''.join([r"https://www.sciencedirect.com", pdfLink['href']]) for pdfLink in soup.find_all('a', attrs={'class': 'anchor pdf-download u-margin-l-right text-s'})]


    def getYears(soup): # redundant for this journal
        pass


    def getTitles(soup):
        # find and transiliterate the titles
        titlesFull =  [unidecode(title.text) for title in soup.findAll('span', attrs={'class': 'js-article-title'})]
        titlesAbbrv = []
        for title in titlesFull:
            if len(title) > 150:
                titlesAbbrv.append(title[:150])
            else:
                titlesAbbrv.append(title)

        return (titlesFull, titlesAbbrv)

    def getDois(soup):

        num_articles = len(soup.find_all('li', attrs={'class': 'js-article-list-item article-item u-padding-xs-top u-margin-l-bottom'}))
        dois = []
        for i in range(num_articles):
            css_selector = f'#article-list > form > div > div.u-margin-xs-top.u-margin-xs-bottom.col-md-18.move-right > ol > li:nth-child({i+1}) > div:nth-child(2)'
            doi = soup.select(css_selector)
            if doi:
                dois.append(doi[0].text)
            else:
                dois.append('NO DOI') # couldn't find css selector
        return dois
    
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
        if issue_names == []:
            return True
        return int(issue) > max([int(name) for name in issue_names])

    def volumeExists(volume):
        volume_names = [f.name.split()[-1] for f in os.scandir(root) if f.is_dir()]
        return bool(volume in volume_names)

    def isNewestVolume(volume):
        volume_names = [f.name for f in os.scandir(root) if f.is_dir()]
        if volume_names == []:
            return True
        return int(volume) > max([int(name) for name in volume_names])


    if not os.path.exists(root):
        raise BaseException('ERROR: Target root directory does not exist!')
    
    ###### main looping logic ########

    cwd = root
    volume_dirs = [f for f in os.scandir(root) if f.is_dir()] # volume = year
    articles = [] # output
    all_missed_illegal_chars = []

    # get all volume links
    volumes = [] # list of dicts
    url1 = 'https://www.sciencedirect.com/journal/neuroimage/issues?page=1'
    url2 = 'https://www.sciencedirect.com/journal/neuroimage/issues?page=2'
    volumes.extend(getVolumes(url1))
    volumes.extend(getVolumes(url2))

    for volume in [v for v in volumes if v['year'] >= startVolume]:

        DOWNLOAD_FLAG_OVERRIDE = None
        # does the volume not exist?
        if not volumeExists(volume['year']):
            print('new volume found:', volume['year'])
            # is it the newest issue?
            if isNewestVolume(volume['year']):
                # file was not found, and is in most recent issue
                DOWNLOAD_FLAG_OVERRIDE = 'DOWNLOAD'
            else:
                # human must review the potential new file
                DOWNLOAD_FLAG_OVERRIDE = 'NO MATCH FOUND'
            print('APPLYING OVERRIDE SETTING:', DOWNLOAD_FLAG_OVERRIDE)
        else:                  
            # volume exists, update cwd
            cwd = [vol.path for vol in volume_dirs if vol.name == volume['year']][0]
        
        if volume['year'] not in lockedVolumes:
            start_time = time.time()
            
            # counters for volume
            missed_illegal_chars_volume = []
            match_found_count = 0
            no_match_found_count = 0
            download_count = 0
            
            ######## NOW WE GET THE ARTICLES IN EACH ISSUE (THE 'link' KEY) ###########
            driver.get(volume['link'])
            html = driver.page_source
            issue_soup = BeautifulSoup(html, 'html.parser')
            # get issue information
            urls = getUrls(issue_soup)
            (allAuthorsFull, allAuthorsAbbrv)  = getNames(issue_soup)
            (titlesFull, titlesAbbrv)  = getTitles(issue_soup) 
            years = [volume['year']] * len(urls)
            dois = getDois(issue_soup)
            
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
                a.journal = 'NeuroImage+'
                a.volume = volume['year']
                a.year = year
                a.issue = volume['name']
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
                    if issueExists(cwd, volume['name']):
                        if fileFound(a, cwd, volume['name']):
                            # file was found
                            downloadFlag = 'MATCH FOUND'
                            match_found_count += 1
                        else:
                            # human must review the potential new file
                            downloadFlag = 'NO MATCH FOUND'
                            no_match_found_count += 1
                    else:
                        # is it the newest issue?
                        if isNewestIssue(cwd, volume['name']):
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

            # finished volume
            print('RUN TIME:' , round(time.time()- start_time, 1), 's')
            print('MISSED ILLEGAL CHARS:', missed_illegal_chars_volume)
            print('MATCH FOUND COUNT:', match_found_count)
            print('NO MATCH FOUND COUNT:', no_match_found_count)
            print('DOWNLOAD COUNT:', download_count)
            all_missed_illegal_chars.extend(missed_illegal_chars_volume)
            print(f'-------- reached end of {volume["name"]} ({volume["year"]}) ----------------')
        
        else:
            # locked volume
            print(f'--------  {volume["name"]} has been locked. Skipping  ----------------')

    # finished journal
    print(f'reached end of {len(volumes)} volumes')
    print('All missed illegal chars:', all_missed_illegal_chars)
    print('done scraping NeuroImage!')

    return articles



