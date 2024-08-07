"""Script to run a quick consistency check:

- Is domains.csv properly sorted?
- Are all domains in urls.txt also in domains.csv?
- Are there duplicates in domains.csv?
- Are all domains in domains.csv proper domain names?
"""

import csv
import sys
from functools import cached_property
from pathlib import Path

import validators
from public_domain import Domain, parse_files

nb_errors = 0


def err(*args, **kwargs):
    global nb_errors
    nb_errors += 1
    kwargs["file"] = sys.stderr
    print(*args, **kwargs)


def warn(*args, **kwargs):
    kwargs["file"] = sys.stderr
    print(*args, **kwargs)


def check_is_valid_domain(file, lineno, line):
    if not validators.domain(line, rfc_2782=True):
        err(f"{file}:{lineno}: {line!r} does not looks like a domain name.")
    if not validators.domain(line):
        warn(
            f"{file}:{lineno}: {line!r} cannot be used in an URL,",
            "it's either an DNS SRV record or a typo.",
        )


def check_lowercased(file, lineno, line):
    if line != line.lower():
        err(f"{file}:{lineno}: {line!r} is not lowercased.")


def check_is_public_domain(file, lineno, line):
    if Domain.from_file_line(file, line).is_not_public():
        err(f"{file}:{lineno}: {line!r} is not a public domain.")


class SortedChecker:
    def __init__(self):
        self.previous = None
        self.has_errored = False

    def __call__(self, file, lineno, domain):
        if self.has_errored:
            return  # Don't flood
        if self.previous is not None:
            if self.previous > Domain.from_file_line(file, domain):
                err(f"{file}: Is not sorted, run `python scripts/sort.py domains.csv`")
                self.has_errored = True
        self.previous = Domain.from_file_line(file, domain)


class DuplicateChecker:
    def __init__(self):
        self.seen = {}

    def check_if_already_seen(self, file, lineno, domain):
        """Checks if the given domain has already been seen."""
        if domain in self.seen:
            seen_in_file, seen_at_line = self.seen[domain]
            err(
                f"{file}:{lineno}: Duplicate domain {domain!r} "
                f"(already seen in {seen_in_file}:{seen_at_line})"
            )

    def check_if_seen_in_other_file(self, file, lineno, domain):
        """Called twice, checks either we've seen the same domain with or without 'www.'
        in another file.

        As both (www and non-www) should probably lie in the same file.
        """
        if domain not in self.seen:
            return
        seen_in_file, seen_at_line = self.seen[Domain.from_file_line(file, domain)]
        if seen_in_file != file:
            err(
                f"{file}:{lineno}: Domain {domain} and its www-prefixed counterpart "
                "should reside in the same file, the other one is in "
                f"{seen_in_file}:{seen_at_line}"
            )

    def __call__(self, file, lineno, line):
        self.check_if_already_seen(file, lineno, line)
        self.check_if_seen_in_other_file(file, lineno, "www." + line)
        if line.startswith("www."):
            self.check_if_seen_in_other_file(file, lineno, line[4:])
        self.seen[Domain.from_file_line(file, line)] = (file, lineno)

    @cached_property
    def all_domains(self) -> set[Domain]:
        return set(self.seen.keys())


def main():
    check_duplicate_line = DuplicateChecker()
    checkers = [
        check_duplicate_line,
        check_is_valid_domain,
        check_is_public_domain,
        check_lowercased,
        SortedChecker(),
    ]

    with open("domains.csv", encoding="UTF-8") as domainsfile:
        domainsreader = csv.reader(domainsfile)
        next(domainsreader)  # Skip header

        for line in domainsreader:
            for checker in checkers:
                checker("domains.csv", domainsreader.line_num, line[0])

    for domain in parse_files(Path("urls.txt")) - check_duplicate_line.all_domains:
        err(f"urls.txt: {domain} not found in domains.csv.")


if __name__ == "__main__":
    main()
    sys.exit(bool(nb_errors))
