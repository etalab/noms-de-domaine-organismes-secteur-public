"""Just sort domains.csv."""

from pathlib import Path

from public_domain import parse_csv_file, write_csv_file


def main():
    file = Path("domains.csv")
    domains = parse_csv_file(file)
    domains = sorted(domains)
    write_csv_file(file, domains)


if __name__ == "__main__":
    main()
