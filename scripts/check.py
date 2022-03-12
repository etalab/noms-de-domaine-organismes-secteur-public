"""Script to run a quick consistency check:

- Are all files properly sorted?
- Are all domains in domaines-organismes-publics.txt also in sources/*.txt?
- Are there duplicates in sources/*.txt?
- Are all lines in sources/*.txt domain names?
"""


import sys
from pathlib import Path
from functools import cached_property
from consolidate import Domain
import validators


def err(*args, **kwargs):
    kwargs["file"] = sys.stderr
    print(*args, **kwargs)


def check_is_sorted(file, lines):
    domains = [Domain.from_file_line(file, line) for line in lines]
    if domains != sorted(domains):
        err(f"{file}: Is not sorted, run `python scripts/sort.py sources/*.txt`")


def check_is_valid_domain(file, lineno, line):
    if not validators.domain(line):
        err(f"{file}:{lineno}: {line!r} does not looks like a domain name.")


def check_lowercased(file, lineno, line):
    if line != line.lower():
        err(f"{file}:{lineno}: {line!r} is not lowercased.")


def check_gouvfr(file, lineno, line):
    if file.name == "gouvfr-divers.txt" and not line.endswith(".gouv.fr"):
        err(f"{file}:{lineno}: {line!r} does is not a '.gouv.fr' domain")


def check_nongouvfr(file, lineno, line):
    if file.name == "nongouvfr-divers.txt" and line.endswith(".gouv.fr"):
        err(f"{file}:{lineno}: {line!r} should be in file 'gouvfr-divers.txt'")


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
        seen_in_file, seen_at_line = self.seen[domain]
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
        self.seen[line] = (file, lineno)

    @cached_property
    def all_domains(self):
        return set(self.seen.keys())


def main():
    check_duplicate_line = DuplicateChecker()
    for file in Path("sources/").glob("*.txt"):
        lines = [
            line.split("#", maxsplit=1)[0].strip()
            for line in file.read_text(encoding="UTF-8").splitlines()
            if not line.startswith("#")
        ]
        check_is_sorted(file, lines)
        for lineno, line in enumerate(lines, start=1):
            check_is_valid_domain(file, lineno, line)
            check_duplicate_line(file, lineno, line)
            check_lowercased(file, lineno, line)
            check_gouvfr(file, lineno, line)
            check_nongouvfr(file, lineno, line)

    consolidated = (
        Path("domaines-organismes-publics.txt").read_text(encoding="UTF-8").splitlines()
    )
    for domain in consolidated:
        if domain not in check_duplicate_line.all_domains:
            err(
                f"domaines-organismes-publics.txt: {domain} not found in sources/*.txt."
            )


if __name__ == "__main__":
    main()
