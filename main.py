import requests
import json
import wget
import os
import time

url = "https://zenodo.org/api/records/"
timeout = 20


record_id = 6517052

data_dir = "data/"
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
    for target_file in files:
        key = target_file['key']
        link = target_file['links']['self']
        try:
            wget.download(link, out=os.path.join(data_dir, key))
        except Exception:
            print(f'{key}: Download error.')
            time.sleep(5)
else:
    raise requests.exceptions.RequestException('Request failed.')
    