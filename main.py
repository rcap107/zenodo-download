import requests
import json
import wget
import os
import time
from tqdm import tqdm
from argparse import ArgumentParser


def parse_args():
    parser = ArgumentParser()
    parser.add_argument(
        "--record_id",
        "-r",
        action="store",
        required=True,
        help="Target record to study.",
        type=int,
    )
    parser.add_argument(
        "-d", "--download", action="store_true", help="Download the files in record ID."
    )
    parser.add_argument(
        "-l", "--list_files", action="store_true", help="List files and their size."
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        action="store",
        help="Directory to use to store files in.",
        default=".",
    )
    # parser.add_argument

    args = parser.parse_args()
    return args


def sizeof_fmt(num, suffix="B"):
    # From https://stackoverflow.com/questions/1094841/get-human-readable-version-of-file-size
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"


if __name__ == "__main__":
    args = parse_args()

    url = "https://zenodo.org/api/records/"
    timeout = 20
    record_id = args.record_id

    if "~" in args.output_dir:
        data_dir = os.path.expanduser(args.output_dir)
    else:
        data_dir = args.output_dir
    
    os.makedirs(data_dir, exist_ok=True)

    try:
        r = requests.get(f"{url}{record_id}", timeout=timeout)
    except requests.exceptions.Timeout:
        print("Request timed out.")
    except requests.exceptions.RequestException:
        print("Request error")

    if r.ok:
        js_request = json.loads(r.text)
        files = js_request["files"]
        num_files = len(files)
        total_size = sum([tgt["size"] for tgt in files])
        print(f"Total size: {sizeof_fmt(total_size)}")
        if args.list_files:
            for idx, target_file in enumerate(files):
                key = target_file["key"]
                link = target_file["links"]["self"]
                print(f"{key:.<80}{sizeof_fmt(target_file['size']):.>10}")

        if args.download:
            for idx, target_file in enumerate(files):
                key = target_file["key"]
                link = target_file["links"]["self"]
                print(key)
                outfile = os.path.join(data_dir, key)
                if not (os.path.exists(outfile)):
                    try:
                        wget.download(link, out=outfile)
                    except Exception:
                        print(f"{key}: Download error.")
                        time.sleep(5)
                else:
                    print(f"File {key} has already been downloaded. Skipping.")

                print(
                    f"\nDownloaded file {idx+1} of {num_files}. [{(idx+1)/num_files:.1f}%]\n"
                )
    else:
        raise requests.exceptions.RequestException("Request failed.")

