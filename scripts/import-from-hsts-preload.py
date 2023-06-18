"""Script to import from the Chromium HSTS preload list.
"""
from pathlib import Path
from base64 import b64decode
import requests
import json
import re

from public_domain import Domain, parse_csv_file, write_csv_file

ROOT = Path(__file__).resolve().parent.parent
FILE = ROOT / "domains.csv"


def fetch_hsts_preload():
    preload_list = requests.get(
        "https://chromium.googlesource.com/chromium/src/+/refs/heads/main/net/http/transport_security_state_static.json?format=TEXT"
    ).text
    preload_list = b64decode(preload_list).decode()
    preload_list = re.sub("//.*", "", preload_list, flags=re.M)
    preload_list = json.loads(preload_list)
    domains = [entry["name"] for entry in preload_list["entries"]]
    gouv_fr_domains = {
        Domain(
            domain.lower(),
            script=Path(__file__).name,
            sources="HSTS preload",
            type="Gouvernement",
        )
        for domain in domains
        if domain.endswith(".gouv.fr")
    }
    domains = parse_csv_file(FILE)
    domains |= gouv_fr_domains
    write_csv_file(FILE, sorted(domains))


def main():
    fetch_hsts_preload()
    print("You can commit this by running:")
    print("    git add domains.csv")
    print('    git commit -m "Import from HSTS preload"')


if __name__ == "__main__":
    main()
