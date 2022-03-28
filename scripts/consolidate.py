"""Consolidate a bunch of files containing domains names to a single
file containing those replying 200 over HTTP.
"""

import argparse
import asyncio
from pathlib import Path
import logging
import random

import aiohttp
from tqdm.asyncio import tqdm

from public_domain import Domain, parse_files

USER_AGENT = (
    "consolidate.py (https://github.com/etalab/noms-de-domaine-organismes-publics)"
)

logger = logging.getLogger("consolidate")


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
                        domain.scheme = protocol
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


def parse_args():
    parser = argparse.ArgumentParser()
    here = Path(__file__).parent
    parser.add_argument("files", type=Path, nargs="+")
    parser.add_argument(
        "--output",
        type=Path,
        help="File to write domains with OK HTTP responses.",
        default=here.parent / "urls.txt",
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


async def main():
    args = parse_args()
    source_domains = parse_files(*args.files)
    if args.output.is_file():
        known_domains = parse_files(args.output)
    else:
        known_domains = set()
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
        "\n".join([domain.url for domain in sorted(known_domains | accepted)]) + "\n",
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
