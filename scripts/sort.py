"""Just sort the given files.

And remove blank lines, and remove duplicates, and lowercase.
"""

import argparse
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", nargs="*")
    return parser.parse_args()


def sort_files(files):
    for file in files:
        path = Path(file)
        lines = path.read_text(encoding="UTF-8").lower().splitlines()
        lines = {line for line in lines if line}
        path.write_text("\n".join(sorted(lines)) + "\n", encoding="UTF-8")


def main():
    args = parse_args()
    sort_files(args.file)


if __name__ == "__main__":
    main()
