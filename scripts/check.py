"""Script to run a quick consistency check:

- Are all files properly sorted?
- Are all domains in domaines-organismes-publics.txt also in sources/*.txt?
- Are there duplicates in sources/*.txt?
- Are all lines in sources/*.txt domain names?
"""


import sys
from pathlib import Path
from functools import cached_property

import validators


def err(*args, **kwargs):
    kwargs["file"] = sys.stderr
    print(*args, **kwargs)


def check_is_sorted(file, lines):
    if lines != sorted(lines):
        err(f"{file}: Is not sorted, run `python scripts/sort.py sources/*.txt`")


def check_is_valid_domain(file, lineno, line):
    if not validators.domain(line):
        err(f"{file}:{lineno}: {line!r} does not looks like a domain name.")


def check_lowercased(file, lineno, line):
    if line != line.lower():
        err(f"{file}:{lineno}: {line!r} is not lowercased.")


class DuplicateChecker:
    def __init__(self):
        self.seen = {}

    def __call__(self, file, lineno, line):
        if line in self.seen:
            err(
                f"{file}:{lineno}: Duplicate domain {line!r} "
                f"(already seen in {self.seen[line]})"
            )
        else:
            self.seen[line] = f"{file}:{lineno}"

    @cached_property
    def all_domains(self):
        return set(self.seen.keys())


def main():
    check_duplicate_line = DuplicateChecker()
    for file in Path("sources/").glob("*.txt"):
        lines = file.read_text(encoding="UTF-8").splitlines()
        check_is_sorted(file, lines)
        for lineno, line in enumerate(lines, start=1):
            check_is_valid_domain(file, lineno, line)
            check_duplicate_line(file, lineno, line)
            check_lowercased(file, lineno, line)

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
