def download(row, target_root):
    url = row['URL']
    volume = row['Volume']
    issue = row['Issue']
    filename = row['FileName']

    if not os.path.exists(target_root):
        raise BaseException('ERROR: Target root directory does not exist!')

    # check if target volume exists

    # MODIFY
    year_offset = 1988

    target_volume = f'{target_root}/{volume+year_offset}'
    if not os.path.exists(target_volume):
        os.makedirs(target_volume)
        print(f'making directory {target_volume}')
    
    # check if target issue exists
    target_issue = f'{target_root}/{volume+year_offset}/Vol {volume} {issue_prefix} {issue}'
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