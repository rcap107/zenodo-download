import requests
import json
import os
import time
from argparse import ArgumentParser
import os.path as osp


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

    parser.add_argument(
        "-f", "--force", action="store_true", help="Overwrite files if already present."
    )
    parser.add_argument(
        "-a", "--ask", action="store_true", help="Ask before overwriting."
    )
    parser.add_argument(
        "-s",
        "--skip",
        action="store_true",
        help="Skip downloading files if they already exist.",
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


def list_files(files):
    for idx, target_file in enumerate(files):
        key = target_file["key"]
        link = target_file["links"]["self"]
        print(f"{key:.<80}{sizeof_fmt(target_file['size']):.>10}")


def fix_outfile_path(outfile):
    path, of = osp.split(outfile)
    of, ext = osp.splitext(of)
    of = of + " (1)" + ext
    outfile = osp.join(path, of)
    return outfile


if __name__ == "__main__":
    args = parse_args()
    if not (args.list_files or args.download):
        args.list_files = True

    url = "https://zenodo.org/api/records/"
    timeout = 20
    record_id = args.record_id

    if "~" in args.output_dir:
        data_dir = os.path.expanduser(args.output_dir)
    else:
        data_dir = os.path.realpath(args.output_dir)

    print(data_dir)
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
            list_files(files)

        if args.download:
            for idx, target_file in enumerate(files):
                download_file = False
                key = target_file["key"]
                link = target_file["links"]["self"]
                print("key:", key)
                outfile = os.path.join(data_dir, key)
                if os.path.exists(outfile):
                    if args.force:
                        print(f"File {outfile} exists. Replacing.")
                        os.remove(outfile)
                        download_file = True
                    elif args.skip:
                        print(f"Skipping file {outfile}.")
                        download_file = False
                    elif args.ask:
                        answer = input(
                            f"File {outfile} already exists. Replace? - y/n: "
                        )

                        while answer.lower() not in ["y", "n"]:
                            answer = input(
                                f"Answer {answer} not recognized. Replace? - y/n"
                            )

                        if answer == "n":
                            print(f"Downloading copy of {outfile}.")
                            outfile = fix_outfile_path(outfile)
                            download_file = True
                        elif answer == "y":
                            download_file = True
                            os.remove(outfile)
                        else:
                            raise ValueError(f"{answer} not recognized.")
                else:
                    download_file = True

                if download_file:
                    try:
                        dir_path, fname = osp.split(outfile)
                        if dir_path:
                            os.makedirs(osp.join(data_dir, dir_path), exist_ok=True)
                        with open(outfile, "wb") as fp:
                            response = requests.get(link, timeout=timeout)
                            fp.write(response.content)
                        # wget.download(link, out=outfile)
                        print(
                            f"\nDownloaded file {idx+1} of {num_files}. [{(idx+1)/num_files:.1f}%]\n"
                        )
                    except Exception as e:
                        print(e)
                        print(f"{key}: Download error.")
                        time.sleep(5)
                else:
                    print(
                        f"\nSkipped file {idx+1} of {num_files}. [{(idx+1)/num_files:.1f}%].\n"
                    )

    else:
        raise requests.exceptions.RequestException("Request failed.")

