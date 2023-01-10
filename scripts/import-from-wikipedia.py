"""Script to import .gouv.fr. domains from an XML Wikipedia dump.

Uses .xml.bz2 dumps from:

=> https://meta.wikimedia.org/wiki/Data_dump_torrents#French_Wikipedia

Run directly on the bz2 file like:

scripts/import-from-wikipedia.py frwiki-20220101-pages-articles-multistream.xml.bz2
"""

import argparse
from pathlib import Path
import bz2
import re
from tqdm import tqdm
from sort import sort_files

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "sources"


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wikipedia_dump")
    return parser.parse_args()


URL = re.compile(  # Restricted URL regex inspired from validators.
    r"^"
    # protocol identifier
    r"https?://"
    # host name
    r"(?:(?:(?:xn--)|[a-z\u00a1-\uffff\U00010000-\U0010ffff0-9]-?)*"
    r"[a-z\u00a1-\uffff\U00010000-\U0010ffff0-9]+)"
    # domain name
    r"(?:\.(?:(?:xn--)|[a-z\u00a1-\uffff\U00010000-\U0010ffff0-9]-?)*"
    r"[a-z\u00a1-\uffff\U00010000-\U0010ffff0-9]+)*"
    # TLD identifier
    r"\.gouv\.fr"
    # port number
    r"(?::\d{2,5})?",
    re.UNICODE | re.IGNORECASE,
)


def main():
    args = parse_args()
    found = set()
    with tqdm(
            desc="Domains found", unit="domain", position=1, total=float("inf")
    ) as found_progress:
        with bz2.open(args.wikipedia_dump, mode="rt", encoding="UTF-8") as dump:
            for line in tqdm(dump, "Lines scanned", unit="line"):
                for match in URL.findall(line):
                    found_progress.update()
                    found.add(match.split("/")[2].split(":", maxsplit=1)[0])
    with open(SOURCES / "gouvfr-divers.txt", "a", encoding="UTF-8") as gouvfr_divers:
        for domain in found:
            gouvfr_divers.write(domain + "  # (from Wikipedia dump)\n")
    sort_files([SOURCES / "gouvfr-divers.txt", SOURCES / "nongouvfr-divers.txt"])


if __name__ == "__main__":
    main()
