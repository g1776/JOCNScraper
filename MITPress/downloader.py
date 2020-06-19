import pandas as pd
import urllib.request

def download(row, root):

    if row['DownloadFlag'] == 'DOWNLOAD':
        url = row['URL']
        volume = row['Volume']
        issue = row['Issue']
        filename = row['FileName']

        # determine "No" or "Iss" for issue
        if volume + 1988 < 2007:
            issue_prefix = 'No'
        else:
            issue_prefix = 'Iss'

        spec = f'{root}/{volume+1988}/Vol {volume} {issue_prefix} {issue}/{filename}'
        try:
            urllib.request.urlretrieve(url, spec)
            return 1
        except:
            print(f'ERROR DOWNLOADING {url}')
            return 0

download_csv = r'C:\Users\grego\Documents\GitHub\JOCNScraper\csvs\MITPress_with_flags.csv'
journal_root = r'D:\ft\ft-j1\J Cognitive Neuroscience+'

df = pd.read_csv(download_csv)
for _, row in df.iterrows():
    download(row, journal_root)
