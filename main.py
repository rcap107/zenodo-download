import requests
import json
import wget
import os
import time
from tqdm import tqdm

url = "https://zenodo.org/api/records/"
timeout = 20


record_id = 6517052

data_dir = os.path.expanduser('~/store/zenodo')
os.makedirs(data_dir, exist_ok=True)

try: 
    r = requests.get(f"{url}{record_id}", timeout=timeout)
except requests.exceptions.Timeout:
    print('Request timed out.')
except requests.exceptions.RequestException:
    print('Request error')

if r.ok:
    js_request = json.loads(r.text)
    files = js_request['files']
    num_files = len(files)
    for idx, target_file in enumerate(files):
        key = target_file['key']
        link = target_file['links']['self']
        print(key)
        try:
            wget.download(link, out=os.path.join(data_dir, key))
        except Exception:
            print(f'{key}: Download error.')
            time.sleep(5)
        
        print(f'\nDownloaded file {idx+1} of {num_files}.\n')
else:
    raise requests.exceptions.RequestException('Request failed.')
    