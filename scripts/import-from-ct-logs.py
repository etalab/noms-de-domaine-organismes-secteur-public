"""Script to import from Certificate Transparency logs.

To avoid running excessive queries, we restrict the search from the
last seen certificate to now.

When running the script it'll print the last seen certificate id, so
you can use it next time.

A good practice may be to "communicate" this last id as a git commit message, like:

    Import from CT logs up to id 6140373134.

So the next maintainer can import using:

    python script/import-from-ct-logs.py 6140373134
"""
import argparse
from pathlib import Path

import psycopg2

from public_domain import Domain, NON_PUBLIC_DOMAINS, parse_csv_file, write_csv_file

ROOT = Path(__file__).resolve().parent.parent
FILE = ROOT / "domains.csv"


def query_ct_logs(last_id):
    """Query crt.sh using their postgres public API."""
    conn = psycopg2.connect(dbname="certwatch", user="guest", host="crt.sh")
    conn.set_session(readonly=True, autocommit=True)
    cur = conn.cursor()
    cur.execute(
        """SELECT id, altnames.*, x509_subjectname(certificate) subject
    FROM certificate, LATERAL (SELECT * FROM x509_altnames(certificate)) altnames
    WHERE plainto_tsquery('gouv.fr') @@ identities(certificate) AND id > %s""",
        (last_id,),
    )

    domains = parse_csv_file(FILE)
    primary_key = None
    for primary_key, domain, subject in cur.fetchall():
        if any(non_public in subject for non_public in NON_PUBLIC_DOMAINS):
            continue
        domain = Domain(
            domain.lower(),
            script=Path(__file__).name,
            sources=f"https://crt.sh/?id={primary_key}",
        )
        if domain.is_not_public():
            continue
        if domain.name.startswith("*."):
            domain.name = domain.name[2:]
        if domain.name.endswith(".gouv.fr"):
            domain.type = "Gouvernement"
        if domain not in domains:
            domains.add(domain)
    write_csv_file(FILE, sorted(domains))
    return primary_key


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "last_id",
        type=int,
        help="Last fetched id, used to get only new domains since last query.",
        metavar="5908982198",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    last_id = query_ct_logs(args.last_id)
    print("Please manually review diff for false positives.")
    print("Don't forgot to run `python scripts/check.py`, then:")
    print("    git add domains.csv")
    print(f'    git commit -m "Import from CT logs up to id {last_id}."')


if __name__ == "__main__":
    main()
