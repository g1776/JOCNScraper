import os.path
import os
import urllib.request

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