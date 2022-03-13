"""Consolidate a bunch of files containing domains names to a single
file containing those replying 200 over HTTP.
"""

import argparse
import asyncio
from functools import total_ordering
from dataclasses import dataclass
from itertools import chain
from pathlib import Path
from typing import Tuple
import logging
import random

import aiohttp
from yarl import URL
from tqdm.asyncio import tqdm

USER_AGENT = (
    "consolidate.py (https://github.com/etalab/noms-de-domaine-organismes-publics)"
)

logger = logging.getLogger("consolidate")

# Domains that are commonly found behind redurections but are not public service:
NON_PUBLIC_DOMAINS = {
    "128k.io",
    "3dathome.fr",
    "attichy.com",
    "bellevillesurmeuse.com",  # Domaine squatté
    "changementadresse-carte-grise.com",  # squatte www.roussillo-conflent.fr
    "cloudflaressl.com",
    "communecter.org",  # Une association
    "creps.ovh",
    "cyberfinder.com",
    "dropcatch.com",  # squtte mairie-clarensac.com
    "gitbook.com",
    "github.com",
    "github.io",
    "go.crisp.chat",
    "google.com",
    "host-web.com",
    "imperva.com",
    "incapsula.com",
    "mesvres.com",  # Domaine squatté
    "microsoftonline.com",
    "milfshorny.com",  # squatte www.opoul.fr et villelefousseret.fr.
    "opendatasoft.com",
    "ovh.co.uk",
    "passeport-mairie.com",  # squatte www.mairiedeliverdy.fr et www.mairieozon.fr
    "sarbacane.com",
    "sendinblue.com",
    "sioracderiberac.com",
    "varchetta.fr",  # squatte www.commune-la-chapelle-de-brain.fr
    "wewmanager.com",
}


@total_ordering
@dataclass
class Domain:
    name: str
    source_file: Path = None
    comment: str = ""
    is_up: bool = False
    redirects_to: str | None = None

    @classmethod
    def from_file_line(cls, file, line):
        """Creates a Domain instance from a text line."""
        if "#" in line:
            domain, comment = line.split("#", maxsplit=1)
        else:
            domain, comment = line, ""
        return Domain(domain.strip().lower(), file, comment=comment.strip())

    def is_not_public(self) -> bool:
        """Returns False if the domain is clearly not public (in NON_PUBLIC_DOMAINS)."""
        return any(self.name.endswith(non_public) for non_public in NON_PUBLIC_DOMAINS)

    def __hash__(self):
        return hash(self.name)

    def __lt__(self, other):
        return self.name.split(".")[::-1] < other.name.split(".")[::-1]

    def __repr__(self):
        if self.comment:
            return f"{self.name}  # {self.comment}"
        else:
            return self.name

    def __eq__(self, other):
        if isinstance(other, str):
            return self.name == other
        return self.name == other.name

    def is_interesting(self) -> bool:
        if self.is_not_public():
            return False
        if self.redirects_to is not None:
            return False
        return self.is_up


async def check_domain(
    domain: Domain,
    client: aiohttp.ClientSession,
    sem: asyncio.Semaphore,
) -> None:
    """Check if the given domain replies an ok-ish response over HTTP or HTTPS."""
    for protocol in "https", "http":
        try:
            url = f"{protocol}://{domain.name}"
            async with sem:
                logger.debug("%s: Querying...", url)
                async with client.head(
                    url,
                    allow_redirects=True,
                    headers={"User-Agent": USER_AGENT},
                ) as response:
                    if response.status == 200:
                        logger.info("%s: OK", url)
                        if response.url.host != domain.name:
                            domain.redirects_to = response.url.host
                        domain.is_up = True
                        return
                logger.info("%s: KO, status={response.status}", url)
        except aiohttp.ClientError as err:
            logger.info("%s: KO: %s", url, err)
        except asyncio.TimeoutError:
            logger.info("%s: KO: Timeout", url)
        except UnicodeError as err:  # Can happen on malformed IDNA.
            logger.info("%s: KO: %s", url, err)
        except ValueError as err:  # Can happen while following redirections
            logger.info("%s: KO: %s", url, err)
    domain.is_up = False


def parse_args():
    parser = argparse.ArgumentParser()
    here = Path(__file__).parent
    parser.add_argument("files", type=Path, nargs="+")
    parser.add_argument(
        "--output",
        type=Path,
        help="File to write domains with OK HTTP responses.",
        default=here.parent / "domaines-organismes-publics.txt",
    )
    parser.add_argument(
        "--slow",
        help="Run slower, in case we're rate limited.",
        action="store_const",
        const=1,
        default=0,
        dest="kindness",
    )
    parser.add_argument(
        "--slower",
        help="Run even slower, in case we're rate limited.",
        action="store_const",
        const=2,
        default=0,
        dest="kindness",
    )
    parser.add_argument(
        "--slowest",
        help="Run extremly slowly, in case we're rate limited.",
        action="store_const",
        const=3,
        default=0,
        dest="kindness",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="Verbosity: use -v or -vv.",
    )
    parser.add_argument(
        "-s", "--silent", action="store_true", help="Disable progress bar"
    )
    args = parser.parse_args()
    args.verbose = min(args.verbose, 2)
    return args


def parse_files(*files: Path) -> set[Domain]:
    """Parse one or many files containing lines of domains.

    It allows comments in source files, starting with # anywhere in the line.
    """
    return {
        Domain.from_file_line(file, line)
        for file in files
        for line in file.read_text(encoding="UTF-8").splitlines()
        if not line.startswith("#")
    }


async def main():
    args = parse_args()
    source_domains = parse_files(*args.files)
    known_domains = parse_files(args.output)
    unknown_domains = list(source_domains - known_domains)
    random.shuffle(unknown_domains)
    logging.basicConfig(
        level=[logging.WARNING, logging.INFO, logging.DEBUG][args.verbose]
    )
    sem = asyncio.Semaphore([20, 10, 5, 2][args.kindness])
    gather = asyncio.gather if (args.verbose or args.silent) else tqdm.gather
    async with aiohttp.ClientSession(
        raise_for_status=True,
        timeout=aiohttp.ClientTimeout(total=20),
    ) as client:
        await gather(*[check_domain(domain, client, sem) for domain in unknown_domains])
    accepted = {domain for domain in unknown_domains if domain.is_interesting()}
    args.output.write_text(
        "\n".join([domain.name for domain in sorted(known_domains | accepted)]) + "\n",
        encoding="UTF-8",
    )
    # In case the domain redirects to an interesting other one,
    # add it to the sources:
    for domain in unknown_domains:
        if not domain.redirects_to:
            continue
        if Domain(domain.redirects_to).is_not_public():
            continue
        if domain.redirects_to in source_domains:
            continue
        with open(domain.source_file, "a", encoding="UTF-8") as source:
            source.write(f"{domain.redirects_to}  # (redirection from {domain.name})\n")
    await asyncio.sleep(
        0.5  # See https://docs.aiohttp.org/en/stable/client_advanced.html#graceful-shutdown
    )  # Which is fixed in aiohttp 4.


if __name__ == "__main__":
    asyncio.run(main())
