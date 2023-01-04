#!/usr/bin/env python

"""Imports data from the « Base nationale sur les intercommunalités », see:
https://www.data.gouv.fr/fr/datasets/base-nationale-sur-les-intercommunalites/
"""

import argparse
from pathlib import Path

import validators
import pandas as pd

from public_domain import Domain, parse_csv_file, write_csv_file


ROOT = Path(__file__).resolve().parent.parent

NATURE_JURIDIQUES = {
    "MET69": "Métropole de Lyon",
    "METRO": "Métropole",
    "CU": "Communauté urbaine",
    "CA": "Communauté d'agglomération",
    "CC": "Communauté de communes",
    "SAN": "Syndicat d'agglomération nouvelle",
    "SIVU": "Syndicat intercommunal à vocation unique",
    "SIVOM": "Syndicat intercommunal à vocation multiple",
    "SMF": "Syndicat mixte fermé",
    "SMO": "Syndicat mixte ouvert",
    "POLEM": "Pôle métropolitain",
    "PETR": "Pôle d'équilibre territorial et rural",
    "EPT": "Etablissement Public Territorial",
}


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "nature_juridique",
        choices=list(NATURE_JURIDIQUES.keys()) + list(NATURE_JURIDIQUES.values()),
    )
    args = parser.parse_args()
    REVERSED_NATURE_JURIDIQUES = {
        value: key for key, value in NATURE_JURIDIQUES.items()
    }
    args.nature_juridique = REVERSED_NATURE_JURIDIQUES.get(
        args.nature_juridique, args.nature_juridique
    )
    return args


def main():
    args = parse_args()

    df = pd.read_csv(
        "https://www.data.gouv.fr/fr/datasets/r/85d11f2d-f7cd-469b-89e5-b210d2658e4f",
        encoding="latin1",
        sep="\t",
        index_col=False,
    )

    domains = parse_csv_file(ROOT / "domains.csv")
    for line in (
        df[df["Nature juridique"] == args.nature_juridique]["Site internet"]
        .dropna()
        .unique()
    ):
        line = line.strip().replace("http://", "").replace("https://", "")
        line = line.split("/", maxsplit=2)[0]  # Drop the path part.
        if not line:
            continue
        if not validators.domain(line):
            continue
        domain = Domain(
            line,
            script=Path(__file__).name,
        )
        if domain not in domains:
            domains.add(domain)
    write_csv_file(ROOT / "domains.csv", sorted(domains))


if __name__ == "__main__":
    main()
