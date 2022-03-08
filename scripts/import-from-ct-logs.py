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
from sort import sort_files

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "sources"


def query_ct_logs(last_id):
    conn = psycopg2.connect(dbname="certwatch", user="guest", host="crt.sh")
    conn.set_session(readonly=True, autocommit=True)
    cur = conn.cursor()
    cur.execute(
        """SELECT id, x509_notBefore(certificate), x509_altnames(certificate)
    FROM certificate
    WHERE plainto_tsquery('gouv.fr') @@ identities(certificate) AND id > %s""",
        (last_id,),
    )
    with (
        open(SOURCES / "gouvfr-divers.txt", "a", encoding="UTF-8") as gouv_fr,
        open(SOURCES / "nongouvfr-divers.txt", "a", encoding="UTF-8") as nongouv_fr,
    ):
        for pk, _added, domain in cur.fetchall():
            if domain.startswith("*."):
                domain = domain[2:]
            if domain.endswith(".gouv.fr"):
                gouv_fr.write(domain + "\n")
            else:
                nongouv_fr.write(domain + "\n")

    return pk


def parse_args():
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
    sort_files(SOURCES.glob("*.txt"))
    print("Don't forgot to run `python scripts/check.py`, then:")
    print("    git add sources/*.txt")
    print(f'    git commit -m "Import from CT logs up to id {last_id}."')


if __name__ == "__main__":
    main()
