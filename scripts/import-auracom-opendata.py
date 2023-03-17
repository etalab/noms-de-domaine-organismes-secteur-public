#!/usr/bin/env python

"""Imports data from Auracom:
https://www.data.gouv.fr/fr/datasets/listes-des-sites-gouv-fr/
"""

from pathlib import Path

import requests

from public_domain import parse_csv_file, write_csv_file, Domain

ROOT = Path(__file__).resolve().parent.parent
FILE = ROOT / "domains.csv"


def main():
    lines = requests.get(
        "https://www.data.gouv.fr/fr/datasets/r/24848dc0-e16c-4ce8-94d9-24bc6304c9b6"
    ).text
    domains = parse_csv_file(FILE)
    for line in lines.splitlines():
        domain = Domain(
            line,
            script=Path(__file__).name,
            type="Gouvernement" if line.endswith(".gouv.fr") else "",
        )
        if domain not in domains:
            domains.add(domain)
    write_csv_file(FILE, sorted(domains))


if __name__ == "__main__":
    main()
