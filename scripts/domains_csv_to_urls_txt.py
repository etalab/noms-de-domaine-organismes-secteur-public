from pathlib import Path

from public_domain import Domain, parse_csv_file


def is_interesting_domain(domain):
    return domain.http_status.startswith("200 ") or domain.https_status.startswith(
        "200 "
    )


def main():
    repo_root = Path(__file__).parent.parent
    urls_txt = repo_root / "urls.txt"
    domains_csv = repo_root / "domains.csv"
    domains = parse_csv_file(domains_csv)
    urls = [domain.url for domain in sorted(domains) if is_interesting_domain(domain)]
    urls_txt.write_text("\n".join(urls) + "\n", encoding="UTF-8")


if __name__ == "__main__":
    main()
