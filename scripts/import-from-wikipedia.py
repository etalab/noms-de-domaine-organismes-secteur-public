"""Script to import .gouv.fr. domains from an XML Wikipedia dump.

Uses .xml.bz2 dumps from:

=> https://meta.wikimedia.org/wiki/Data_dump_torrents#French_Wikipedia

Run directly on the bz2 file like:

scripts/import-from-wikipedia.py frwiki-20220101-pages-articles-multistream.xml.bz2
"""

import argparse
import bz2
import re
from pathlib import Path

from tqdm import tqdm

from public_domain import Domain, parse_csv_file, write_csv_file

ROOT = Path(__file__).resolve().parent.parent
FILE = ROOT / "domains.csv"


def parse_args():
    """Parse command line arguments."""
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
    """Parse a bz2 wikipedia dump searching for .gouv.fr domains."""
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
    domains = parse_csv_file(FILE)
    for line in found:
        domain = Domain(line, script=Path(__file__).name, type="Gouvernement")
        if domain not in domains:
            domains.add(domain)
    write_csv_file(FILE, sorted(domains))


if __name__ == "__main__":
    main()
