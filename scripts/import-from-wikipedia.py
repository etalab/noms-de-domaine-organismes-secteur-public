"""Script to import .gouv.fr. domains from an XML Wikipedia dump.
"""

import argparse
from pathlib import Path
import re
from sort import sort_files

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "sources"


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wikipedia_dump")
    return parser.parse_args()


def main():
    args = parse_args()

    url = re.compile(  # Restricted URL regex inspired from validators.
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
    found = set()
    with open(args.wikipedia_dump, encoding="UTF-8") as wikipedia_dump:
        for line in wikipedia_dump:
            for match in url.findall(line):
                found.add(match.split("/")[2].split(":", maxsplit=1)[0])
    with open(SOURCES / "gouvfr-divers.txt", "a", encoding="UTF-8") as gouvfr_divers:
        for domain in found:
            gouvfr_divers.write(domain + "\n")
    sort_files([SOURCES / "gouvfr-divers.txt", SOURCES / "nongouvfr-divers.txt"])


if __name__ == "__main__":
    main()
