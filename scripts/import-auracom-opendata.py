#!/usr/bin/env python

"""Imports data from Auracom:
https://www.data.gouv.fr/fr/datasets/listes-des-sites-gouv-fr/
"""

from pathlib import Path

import requests

from sort import sort_files

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "sources"


def main():
    lines = requests.get(
        "https://www.data.gouv.fr/fr/datasets/r/24848dc0-e16c-4ce8-94d9-24bc6304c9b6"
    ).text
    with (
        open(SOURCES / "gouvfr-divers.txt", "a", encoding="UTF-8") as gouv_fr,
        open(SOURCES / "nongouvfr-divers.txt", "a", encoding="UTF-8") as nongouv_fr,
    ):
        for line in lines.splitlines():
            domain = line.split(maxsplit=1)[0]
            if domain.endswith(".gouv.fr"):
                gouv_fr.write(domain + "\n")
            else:
                nongouv_fr.write(domain + "\n")
    sort_files([SOURCES / "gouvfr-divers.txt", SOURCES / "nongouvfr-divers.txt"])


if __name__ == "__main__":
    main()
