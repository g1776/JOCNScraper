# JOCNScraper

## How to use the tool

### Scraping

First, you must scrape the journal website using the scrape() function found in main.py
Calling scrape() alone won't do anything if you don't first modify it to include the scrapers you want it to include in the output csv file. 
This is done in the section of the function blocked out, where you specify the root of each scraper's directory and append the results of the scraper to the "articles" list.

### Downloading

In order to download the PDFs from the csv file, you call download() from main.py
download() takes 3 parameters:
    - root: the location you want to download the files to.
    - csv: the csv file that stores all the urls to download from.
    - downloaders: a dict where the keys are the Journals and the values are the corresponding download functions

### Adding Journals

Since this project is all web scraping, it is highly dependent on the HTML structure of the websites you are scraping. Because of this, there is only so much that can be guaranteed when it comes to extending a web scraping tool to a new website. Much adapting has to be done manually instead of the code adapting to a new website. I have outlined the changes that are necessary in the template.py files found in the scrapers and downloaders folders. These 2 files each have comments that show what needs to be changed for adding a new website.

In template.py:

The comment "# TO MODIFY" means the following function or line of code most likely needs to be changed in order to adapt for a new website. Thay may include changing an html class, or writing completely new Python logic.

The comment "# modify to tailor to HTML of site" also specifies the specific line that needs to be changed within a TO MODIFY function.

The variable "year_offset" is unique to each website, as it specifies the starting year of the journal (ie the first year of the first volume/issue).

The comment "# LEAVE ALONE" means that the function should not need to be modified for a new website.