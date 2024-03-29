"""Script to manipulate the domain names of French public organizations."""

import argparse
import csv
import logging
import re
import sys
from dataclasses import dataclass
from functools import total_ordering
from pathlib import Path
from urllib.parse import urlparse
from denylist import NON_PUBLIC_DOMAINS


logger = logging.getLogger(__name__)


@total_ordering
@dataclass
class Domain:
    name: str
    source_file: Path | None = None
    comment: str = ""
    http_status: str | None = None
    https_status: str | None = None
    SIREN: str | None = None  # pylint: disable=invalid-name
    type: str | None = None
    sources: str | None = None
    script: str | None = None

    # http*_status can also start with "Redirects to: "
    #
    # It's encouraged to add any needed attributes like:
    # smtp_status
    # ssh_status
    # ...

    @classmethod
    def csv_headers(cls):
        """List of columns to generate for the CSV files."""
        return (
            "name",
            "http_status",
            "https_status",
            "SIREN",
            "type",
            "sources",
            "script",
        )

    def set_status(self, service, status):
        """Set new status for the given service.

        like: domain.set_status("https", "200 OK")
        """
        if f"{service}_status" not in self.csv_headers():
            raise ValueError(
                f"Can't set status for service {service}: "
                f"{service}_status is not a Domain attribute."
            )
        setattr(self, f"{service}_status", status)

    def astuple(self):
        """Useful for CSV output."""
        return tuple(getattr(self, attr) for attr in self.csv_headers())

    @classmethod
    def fromtuple(cls, domain_tuple):
        """Useful to read from CSV files."""
        attrs = dict(zip(cls.csv_headers(), domain_tuple))
        return cls(**attrs)

    @classmethod
    def from_file_line(cls, file, line):
        """Creates a Domain instance from a text line.

        The provided line may just be a domain nane, or a full URL.
        """
        domain, comment = line, ""
        if "#" in line:
            domain, comment = line.split("#", maxsplit=1)
        kwargs = {"comment": comment.strip(), "source_file": file}
        domain = domain.strip().lower()
        if domain.startswith("http://") or domain.startswith("https://"):
            return cls.from_url(urlparse(domain), **kwargs)
        return cls(domain, **kwargs)

    @classmethod
    def from_url(cls, url, **kwargs):
        """Constructs a Domain instance from the result of urlparse."""
        if url.scheme == "https":
            return cls(name=url.netloc, https_status="200 OK", **kwargs)
        else:
            return cls(name=url.netloc, http_status="200 OK", **kwargs)

    def is_not_public(self) -> bool:
        """Returns False if the domain is clearly not public (in NON_PUBLIC_DOMAINS)."""
        return any(self.name.endswith(non_public) for non_public in NON_PUBLIC_DOMAINS)

    def __hash__(self):
        return hash(self.name)

    def __lt__(self, other):
        return self.name.split(".")[::-1] < other.name.split(".")[::-1]

    def __repr__(self):
        if self.comment:
            return f"{self.name}  # {self.comment}"
        else:
            return self.name

    def __eq__(self, other):
        if isinstance(other, str):
            return self.name == other
        return self.name == other.name

    @property
    def url(self) -> str:
        """Representation of this domain as an URL."""
        if self.https_status.startswith("200 "):
            return f"https://{self.name}"
        elif self.http_status.startswith("200 "):
            return f"http://{self.name}"
        else:
            raise ValueError(
                "Can't represent Domain as an URL, not sure about the scheme."
            )


def parse_files(*files: Path) -> set[Domain]:
    """Parse one or many files containing lines of domains.

    It allows comments in source files, starting with # anywhere in the line.
    """
    return {
        Domain.from_file_line(file, line)
        for file in files
        for line in file.read_text(encoding="UTF-8").splitlines()
        if not line.startswith("#")
    }


def parse_csv_file(domainsfile) -> set[Domain]:
    domains = set()
    try:
        with open(domainsfile, "r", encoding="UTF-8") as domainsfile:
            domainsreader = csv.reader(domainsfile)
            next(domainsreader)
            for row in domainsreader:
                domains.add(Domain.fromtuple(row))
        return domains
    except FileNotFoundError:
        return set()


def write_csv_file(domainsfile, domains):
    with open(domainsfile, "w", encoding="UTF-8") as f:
        domainswriter = csv.writer(f, lineterminator="\n")
        domainswriter.writerow(Domain.csv_headers())
        for domain in sorted(domains):
            try:
                domainswriter.writerow(domain.astuple())
            except UnicodeEncodeError:
                logger.exception(f"Can't write line in CSV file: {domain.astuple()!r}")


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(help="Sub commands", required=True)

    parser_get = subparsers.add_parser("get", help="Get a domain informations.")
    parser_get.add_argument("name", help="A domain name")
    parser.set_defaults(func=main_get)

    return parser.parse_args()


TITLE_COLOR = "\x1b[1;33m"
PROPERTY_COLOR = "\x1b[32m"
OK_COLOR = "\x1b[32m"
OKISH_COLOR = "\x1b[33m"
KO_COLOR = "\x1b[31m"
NO_COLOR = "\x1b[0m"


def main_get(args):
    """TODO: Ajouter l'historique d'un domaine en consultant le git log?"""

    def title(string):
        return TITLE_COLOR + string + NO_COLOR

    def property(string):
        return PROPERTY_COLOR + string + NO_COLOR

    data = parse_csv_file("domains.csv")
    domains = [domain for domain in data if re.search(args.name, domain.name)]
    for domain in domains:
        print(title(domain.name))
        if domain.type:
            print(property("Type:"), domain.type)
        if domain.sources:
            print(property("Source:"), domain.sources)
        if domain.SIREN:
            print(property("SIREN:"), domain.SIREN)
        if domain.script:
            print(property("Script:"), domain.script)
        print(property(f"http://{domain.name}:"), domain.http_status)
        print(property(f"https://{domain.name}:"), domain.https_status)
        print("\n")


def main():
    """Pretty print domains, to use from command line."""
    args = parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
