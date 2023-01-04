"""Script to convert sources/ to the 2023 format.

How to run:

    $ python scripts/convert.py
    $ git rm -fr sources
    $ git add domains.csv
    $ git commit -m "Merge sources/* to domains.csv"

The old hierarchy was:

sources/
├── academies.txt
├── ambassades.txt
├── aphp.txt
├── collectivites.txt
├── etablissements-scolaires.txt
├── gouvfr-divers.txt
├── hopitaux.txt
├── nongouvfr-divers.txt
├── sante-fr.txt
└── universites.txt

But this split was arbitrary, we're converting it to a single
source.csv file instead of a directory with the following columns:

- Nom de domaine
- SIRET
- Type d’établissement (à partir du découpage actuel des noms de fichier,
  des catégories banatic, catégorie juridique INSEE)
- Sources (URL)
- Scripts qui moissonnent (URL)

But we almost stored the source, so we'll use git log to deduce it from commit messages.
"""

from subprocess import run, PIPE
from pathlib import Path
import shelve
import re

from public_domain import parse_csv_file, write_csv_file, parse_files, Domain


def git(*args):
    """Just calls git, returns a list of lines."""
    return run(
        ["git"] + list(args), stdout=PIPE, encoding="UTF-8", check=True
    ).stdout.splitlines()


def shelve_cache(path):
    "Cache a function result to a shelf."

    def cache(function):
        def cached(*args, **kwargs):
            with shelve.open(path) as cache:
                key = f"{function.__name__}({args}, {kwargs})"
                if key in cache:
                    return cache[key]
                result = function(*args, **kwargs)
                cache[key] = result
                return result

        return cached

    return cache


@shelve_cache(".cache")
def domains_and_commits():
    """Parse `git log` to tell which commit added which domain.

    Returns a mapping of domains to git commits like: {"example.com": "433f496"}
    """
    domain_commit_map = {}
    commits = git("log", "--format=%H", "--reverse")
    for commit in commits:
        tree = git("ls-tree", "--name-only", "-r", commit)
        for file in map(Path, tree):
            if file.suffix in (".yml", ".py", ".md"):
                continue
            file = git("show", f"{commit}:{file}")
            for line in file:
                domain = re.split(r"[\s,]", line, maxsplit=1)[0]
                domain = domain.split("/")[-1]
                if domain in domain_commit_map:
                    continue
                domain_commit_map[domain] = commit
    return domain_commit_map


def domains_and_types():
    """Build a list of domains and their types.

    The type of a domain is only deduced from its location in the old hierarchy.
    """
    pretty_names = {
        "academies.txt": "Académie",
        "ambassades.txt": "Ambassade",
        "aphp.txt": "APHP",
        "centre-de-gestion.txt": "Centre de gestion",
        "collectivites.txt": "Collectivité",
        "communes.txt": "Commune",
        "conseils-departementaux.txt": "Conseil départemental",
        "conseils-regionaux.txt": "Conseil régional",
        "epci.txt": "EPCI",
        "etablissements-scolaires.txt": "Établissement scolaire",
        "gouvfr-divers.txt": "Gouvernement",
        "hopitaux.txt": "Hôpital",
        "mdph-mda.txt": "MDPH ou MDA",
        "nongouvfr-divers.txt": "",
        "prefectures.txt": "Préfécture",
        "sante-fr.txt": "Santé",
        "universites.txt": "Université",
    }

    domains_and_types_map = {}
    for file in Path("sources").glob("*.txt"):
        for line in file.read_text().splitlines():
            domains_and_types_map[Domain(line)] = pretty_names[file.name]
    return domains_and_types_map


@shelve_cache(".cache")
def get_commit_message(sha):
    return " ".join(git("show", "-s", "--format=%B", sha))


@shelve_cache(".cache")
def get_commit_author(sha):
    return git("show", "-s", "--format=%an", sha)[0]


def commit_to_script(commit):
    """In case we can know which script was used to find this domain, return it."""
    message = get_commit_message(commit)
    if "CT log" in message:
        return "import-from-ct-logs.py"
    if "banatic" in message:
        return "import-base-nationale-sur-les-intercommunalites.py"
    if "Auracom" in message:
        return "import-auracom-opendata.py"
    return None


def commit_to_source(commit):
    """In case we can know which source was used to find this domain, return it."""
    message = get_commit_message(commit)
    if "https://github.com/tb0hdan/domains/blob/master/data/france" in message:
        return "https://github.com/tb0hdan/domains/blob/master/data/france"
    if "wikipedia" in message.lower():
        return "Wikipedia"
    if "ADULLACT" in message.upper():
        return "ADULLACT"
    if "AFNIC" in message:
        return "AFNIC open data"
    if "DILA" in message:
        return "DILA open data"
    if "wikidata" in message.lower():
        return "Wikidata"
    if "Auracom" in message:
        return "Auracom open data"
    if "https://www.data.gouv.fr/fr/datasets/listes-des-sites-gouv-fr/" in message:
        return "https://www.data.gouv.fr/fr/datasets/listes-des-sites-gouv-fr/"
    if "github.com/bzg/gouvfrlist" in message:
        return "https://github.com/bzg/gouvfrlist"
    if "banatic" in message:
        return "Banatic"
    if "a few domains hosted on the same IP on already known domains" in message:
        return "DNS"
    if "CT log" in message or "certificate transparency logs" in message:
        return "CT logs"
    return "Ajout manuel de " + get_commit_author(commit)


def convert_domains_csv():
    """As a reminder, the following columns are expected:
    - Nom de domaine
    - SIRET
    - Type d’établissement (à partir du découpage actuel des noms de fichier,
      des catégories banatic, catégorie juridique INSEE)
    - Sources (URL)
    - Scripts qui moissonnent (URL)
    """
    types_map = domains_and_types()
    commit_map = domains_and_commits()
    old_domains_csv = {domain.name: domain for domain in parse_csv_file("domains.csv")}
    from_sources_txt = sorted(parse_files(*(Path("sources").glob("*.txt"))))
    domains = [
        old_domains_csv.get(domain.name, Domain(domain.name))
        for domain in from_sources_txt
    ]
    domains.sort()
    for domain in domains:
        commit = commit_map[domain.name]
        domain.sources = commit_to_source(commit)
        domain.script = commit_to_script(commit)
        domain.type = types_map.get(domain.name)
    write_csv_file("domains.csv", domains)


if __name__ == "__main__":
    convert_domains_csv()
