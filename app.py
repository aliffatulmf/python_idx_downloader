import argparse
import cloudscraper
import json
import csv
import os
import shutil

from urllib.parse import quote
from time import sleep
from rich.console import Console
from multiprocessing import Pool


console = Console()


# Options
BROWSER = {
    "browser": "chrome",
    "desktop": True,
    "mobile": False,
    "platform": "linux",
}
DELAYS = 5

# Args
# fmt:off
parser = argparse.ArgumentParser(prog="IDX Downloader",
                                 description="Download file from idx.co.id",
                                 usage='use "%(prog)s --help" for more information',
                                 formatter_class=argparse.RawTextHelpFormatter
                                 )
parser.add_argument("-y", "--year", action="extend", type=list, nargs="+", required=True, dest="year", help="year to search (required)\nexample: -y 2019 -y 2020, -y 2021")
parser.add_argument("-x", "--parallel", type=int, default=os.cpu_count(), dest="parallel", help="parallel task\n(default: based on the number of cores owned)")
# fmt:on
args = parser.parse_args()


def join_year(years):
    year_list = []
    for year in years:
        ys = "".join(year)
        year_list.append(ys)

    return year_list


def reader():
    arr = []
    with open("data.csv", mode="r") as csv_file:
        csv_reader = csv.DictReader(csv_file)

        for row in csv_reader:
            arr.append(row)

    return arr


def json_info(year, kode_emiten, number, name):
    url = "https://idx.co.id/primary/ListedCompany/GetFinancialReport"
    params = {
        "indexFrom": 1,
        "pageSize": 12,
        "year": year,
        "reportType": "rdf",
        "EmitenType": "s",
        "periode": "audit",
        "kodeEmiten": kode_emiten,
        "SortColumn": "KodeEmiten",
        "SortOrder": "asc",
    }

    init = cloudscraper.create_scraper(browser=BROWSER, delay=DELAYS)
    r = init.get(url, params=params).text

    return json.loads(r)


YEARS = join_year(args.year)
ROWS = reader()
TOTAL_ROWS = len(ROWS)
CURRENT_ROW = 3

RANDOM_SLEEP_DOWNLOAD = [2, 4]
RANDOM_SLEEP_LOOP = [1, 5]

console.clear()


def main(row):
    for year in YEARS:
        data = json_info(year, row["kode"], row["no"], row["nama"])
        result = data["Results"]

        console.log(
            f'[DW] [yellow]{data["Search"]["KodeEmiten"]} [white]{row["nama"]} => [cyan][{year}]'
        )

        if len(result) < 1:
            continue

        fdir = f'files/{row["no"]} {data["Search"]["KodeEmiten"]}-{row["nama"]}/{year}'

        if os.path.exists(fdir):
            shutil.rmtree("files/")

        os.makedirs(fdir)

        for i in data["Results"][0]["Attachments"]:
            if i["File_Name"].endswith((".zip", ".xlsx")):
                continue

            fpath = i["File_Path"]
            link = "https://idx.co.id" + quote(fpath)

            dw = cloudscraper.create_scraper(browser=BROWSER, delay=DELAYS)

            content = dw.get(link).content

            fileopen = open(f'{fdir}/{i["File_Name"]}', "wb")
            fileopen.write(content)
            fileopen.close()


if __name__ == "__main__":
    with console.status("[bold green]Downloading...") as status:
        sleep(1)  # necessary
        with Pool(processes=args.parallel) as pool:
            pool.map(main, ROWS)

    console.print("\n[green]FINISH")
