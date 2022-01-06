"""Just sort the given files.

And remove blank lines, and remove duplicates.
"""

import argparse
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", nargs="*")
    return parser.parse_args()


def main():
    args = parse_args()
    for file in args.file:
        path = Path(file)
        lines = path.read_text(encoding="UTF-8").splitlines()
        lines = {line for line in lines if line}
        path.write_text("\n".join(sorted(lines)) + "\n", encoding="UTF-8")


if __name__ == "__main__":
    main()
