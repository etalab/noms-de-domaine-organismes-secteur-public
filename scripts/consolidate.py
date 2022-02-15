"""Consolidate a bunch of files containing domains names to a single
file containing those replying 200 over HTTP.
"""

import argparse
import asyncio
from itertools import chain
from pathlib import Path
from typing import Tuple
import logging
import random

import aiohttp
from yarl import URL
from tqdm.asyncio import tqdm


logger = logging.getLogger("consolidate")

# Domains that are commonly found behind redurections but are not public service:
NON_PUBLIC_DOMAINS = {
    "128k.io",
    "accounts.google.com",
    "cloud.wewmanager.com",
    "github.com",
    "go.crisp.chat",
    "journal-officiel-datadila.opendatasoft.com",
    "www.changementadresse-carte-grise.com",  # squatte www.roussillo-conflent.fr
    "host-web.com",
    "login.microsoftonline.com",
    "socialgouv.github.io",
    "www.3dathome.fr",
    "www.creps.ovh",
    "www.cyberfinder.com",
    "www.ovh.co.uk",
    "www.sarbacane.com",
    "www.sendinblue.com",
    "www.wewmanager.com",
}


def ingest_good_response(
    first_domain: str, last_domain: str, source_domains
) -> Tuple[str, bool]:
    """Given a 200 HTTP response, tell if it should be added to
    domaines-organismes-publics.txt."""
    if last_domain not in source_domains:
        if last_domain not in NON_PUBLIC_DOMAINS:
            logger.warning(
                "%s: Redirects to unknown domain: %s", first_domain, last_domain
            )
        return first_domain, False
    if first_domain != last_domain:
        logger.info(
            "%s: Redirects to another known domain (%s), skipping.",
            first_domain,
            last_domain,
        )
        return first_domain, False
    return first_domain, True


async def check_if_adding_www_helps(
    domain: str,
    err: Exception,
    client: aiohttp.ClientSession,
    sem: asyncio.Semaphore,
    source_domains: set[str],
) -> None:
    """When we fail resolving a domain, it may be good to test with a www prefix."""
    if "Name or service not known" not in str(err) or domain.startswith("www."):
        return
    if "www." + domain in source_domains:
        return
    for protocol in "https", "http":
        try:
            async with sem:
                async with client.head(f"{protocol}://{domain}") as response:
                    if response.status == 200:
                        logger.warning(
                            "%s: (Would have worked prefixed with 'www.': "
                            "sed -i s/%s/%s/ sources/*.txt",
                            domain,
                            domain,
                            "www." + domain,
                        )
                    return
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError):
            pass


async def check_domain(
    domain: str,
    client: aiohttp.ClientSession,
    sem: asyncio.Semaphore,
    source_domains: set[str],
) -> Tuple[str, bool]:
    """Check if the given domain replies an ok-ish response over HTTP or HTTPS."""
    for protocol in "https", "http":
        try:
            url = f"{protocol}://{domain}"
            async with sem:
                logger.debug("%s: Querying...", url)
                async with client.head(url, allow_redirects=True) as response:
                    if response.status == 200:
                        logger.info("%s: OK", url)
                        return ingest_good_response(
                            domain, response.url.host, source_domains
                        )
                logger.info("%s: KO, status={response.status}", url)
        except aiohttp.ClientError as err:
            logger.info("%s: KO: %s", url, err)
            await check_if_adding_www_helps(domain, err, client, sem, source_domains)
        except asyncio.TimeoutError:
            logger.info("%s: KO: Timeout", url)
        except UnicodeError as err:  # Can happen on malformed IDNA.
            logger.info("%s: KO: %s", url, err)
        except ValueError as err:  # Can happen while following redirections
            logger.info("%s: KO: %s", url, err)
    return domain, False


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


def parse_files(*files) -> set[str]:
    """Parse one or many files containing lines of domains."""
    return set(
        chain(*[file.read_text(encoding="UTF-8").splitlines() for file in files])
    )


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
        results = await gather(
            *[
                check_domain(domain, client, sem, source_domains)
                for domain in unknown_domains
            ]
        )
    accepted = {domain for domain, is_up in results if is_up}
    args.output.write_text(
        "\n".join(sorted(list(known_domains | accepted))) + "\n",
        encoding="UTF-8",
    )
    await asyncio.sleep(
        0.5  # See https://docs.aiohttp.org/en/stable/client_advanced.html#graceful-shutdown
    )  # Which is fixed in aiohttp 4.


if __name__ == "__main__":
    asyncio.run(main())
