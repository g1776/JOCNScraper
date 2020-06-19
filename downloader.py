import pandas as pd
import urllib.request

download_csv = r'C:\Users\grego\Documents\GitHub\JOCNScraper\csvs\MITPress_with_flags.csv'
df = pd.read_csv(download_csv)

urllib.request.urlretrieve("https://i.ytimg.com/vi/NHEtD1w5eqI/maxresdefault.jpg", "cow.jpg")

print('done')



# for index, row in df.iterrows():
#     if row['DownloadFlag'] == 'DOWNLOAD':

    