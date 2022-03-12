"""Just sort the given files.

And remove blank lines, and remove duplicates, and lowercase.
"""

import argparse
from pathlib import Path
from consolidate import Domain, parse_files


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", nargs="*", type=Path)
    return parser.parse_args()


def sort_files(files):
    for file in files:
        domains = parse_files(file)
        file.write_text(
            "\n".join([str(d) for d in sorted(domains)]) + "\n", encoding="UTF-8"
        )


def main():
    args = parse_args()
    sort_files(args.file)


if __name__ == "__main__":
    main()
