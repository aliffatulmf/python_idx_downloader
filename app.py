import argparse
import cloudscraper
import csv
import os
import shutil

from urllib.parse import quote
from rich.console import Console
from multiprocessing import Pool

parser = argparse.ArgumentParser(
    prog="IDX Downloader",
    description="Download file from idx.co.id",
    usage='use "%(prog)s --help" for more information',
    formatter_class=argparse.RawTextHelpFormatter,
)
parser.add_argument(
    "-y",
    "--year",
    action="extend",
    type=int,
    nargs="+",
    required=True,
    dest="year",
    help="year to search (required)\nexample: -y 2019 -y 2020, -y 2021",
)
parser.add_argument(
    "-x",
    "--parallel",
    type=int,
    default=os.cpu_count(),
    dest="parallel",
    help="parallel task\n(default: based on the number of cores owned)",
)
parser.add_argument(
    "-e",
    "--ext",
    type=str,
    nargs="+",
    dest="exts",
    default=(".zip", ".xlsx"),
    help="Download by given extensions. Default (.zip, .xlsx)",
)
parser.add_argument("--all",
                    type=bool,
                    action=argparse.BooleanOptionalAction,
                    dest="all",
                    default=False,
                    help="download all files")
args = parser.parse_args()

console = Console()
csinit = cloudscraper.create_scraper(
    browser={
        "browser": "chrome",
        "desktop": True,
        "mobile": False,
        "platform": "linux",
    },
    delay=5,
)


def reader():
	arr = []
	with open("data.csv", mode="r", encoding="latin1") as csv_file:
		csv_reader = csv.DictReader(csv_file)

		for row in csv_reader:
			arr.append(row)

	return arr


HEADERS = {"Connection": "Keep-Alive", "Keep-Alive": "timeout=5;max=1000"}
YEARS = args.year
ROWS = reader()


def json_info(year, kode_emiten):
	url = "https://www.idx.co.id/primary/ListedCompany/GetFinancialReport"
	params = {
	    "indexFrom": 1,
	    "pageSize": 12,
	    "year": year,
	    "reportType": "rda",
	    "EmitenType": "s",
	    "periode": "audit",
	    "kodeEmiten": kode_emiten,
	    "SortColumn": "KodeEmiten",
	    "SortOrder": "asc",
	}

	return csinit.get(url, params=params).json()


def main(row):
	for year in YEARS:
		data = json_info(year, row["kode"])
		result = data["Results"]

		console.print(
		    f'[DW] {row["no"]} - [cyan][{year}] [yellow]{data["Search"]["KodeEmiten"]} [white]{row["nama"]}'
		)

		if len(result) < 1:
			continue

		fdir = f'files/{row["no"]} {data["Search"]["KodeEmiten"]}-{row["nama"]}/{year}'

		if os.path.exists(fdir):
			shutil.rmtree("files/")
		else:
			os.makedirs(fdir)

		for i in data["Results"][0]["Attachments"]:
			if not args.all:
				if not i["File_Name"].endswith(tuple(args.exts)):
					continue

			fpath = i["File_Path"]
			link = "https://www.idx.co.id" + quote(fpath)
			content = csinit.get(link).content

			fileopen = open(f'{fdir}/{i["File_Name"]}', "wb")
			fileopen.write(content)
			fileopen.close()


if __name__ == "__main__":
	with Pool(processes=args.parallel) as pool:
		pool.map(main, ROWS)
		pool.close()
		pool.join()

	console.print("[green]FINISH")
