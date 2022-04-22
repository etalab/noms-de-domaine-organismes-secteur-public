"""Update domains.csv from sources/*.txt."""

import argparse
import asyncio
from pathlib import Path
import logging
import random
from urllib.parse import urlparse, urljoin

import aiohttp
from tqdm.asyncio import tqdm

from public_domain import Domain, parse_files, parse_csv_file, write_csv_file

USER_AGENT = "See https://github.com/etalab/noms-de-domaine-organismes-publics"

HEADERS = {"User-Agent": USER_AGENT}

logger = logging.getLogger("http_checker")


def avoid_surrogates(s):
    return s.encode("utf-8", "surrogateescape").decode("utf-8", "backslashreplace")


def to_message(err):
    """Try to producuce a clean and readable message from the given HTTP
    response or exception caused by an HTTP query."""
    match err:
        case aiohttp.ClientResponse(status=200):
            return f"200 {avoid_surrogates(err.reason)}"
        case aiohttp.ClientResponse(status=301 | 302 | 303 | 307 | 308):
            dest = err.headers.get("Location", "(but no Location in headers)")
            return f"{err.status} {avoid_surrogates(err.reason)} {dest}"
        case aiohttp.client_exceptions.ClientConnectorError() if err.strerror:
            return err.strerror
        case aiohttp.client_exceptions.ClientConnectorCertificateError():
            return f"{err.certificate_error!s}"
        case asyncio.TimeoutError():
            return "Timeout"
        case aiohttp.ClientResponse():
            return f"{err.status} {avoid_surrogates(err.reason)}"
        case _:
            return type(err).__name__ + ": " + str(err)


def share_same_domain(url1: str, url2: str):
    return urlparse(url1).netloc == urlparse(url2).netloc


async def http_head(
    url: str, client: aiohttp.ClientSession, max_redirects=10, method="HEAD"
) -> aiohttp.ClientResponse:
    """Performs an HTTP GET on the given URL.

    Only follow redirections on the **same** domain, so:

    - if http://munster.alsace redirects to http://www.munster.alsace it's a redirection.
    - if http://munster.alsace redirects to http://muster.alsace/fr replying OK it's OK.

    We try to use HEAD requests, but if not allwed we fallback to GET requests.
    """
    async with client.request(
        method, url, headers=HEADERS, allow_redirects=False
    ) as response:
        logger.info("%s: %s %s", url, response.status, response.reason)
    if response.status == 405 and method == "HEAD":  # Method Not Allowed
        return await http_head(url, client, method="GET")
    if (
        300 < response.status < 400
        and "Location" in response.headers
        and share_same_domain(url, dest := urljoin(url, response.headers["Location"]))
        and max_redirects > 0
    ):
        return await http_head(dest, client, max_redirects - 1, method=method)
    return response


async def check_domain(
    domain: Domain,
    client: aiohttp.ClientSession,
) -> None:
    """Check if the given domain replies an ok-ish response over HTTP or HTTPS."""
    for protocol in "https", "http":
        try:
            url = f"{protocol}://{domain.name}"
            logger.debug("%s: Querying...", url)
            response = await http_head(url, client=client)
            domain.set_status(protocol, to_message(response))
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as err:
            message = to_message(err)
            domain.set_status(protocol, message)
            logger.info("%s: KO: %s", url, message)


def parse_args():
    parser = argparse.ArgumentParser()
    here = Path(__file__).parent
    default_files = list((here / "sources").glob("*.txt"))
    parser.add_argument("files", type=Path, nargs="*", default=default_files)
    parser.add_argument(
        "--output",
        type=Path,
        help="File to write domains with OK HTTP responses.",
        default=here.parent / "domains.csv",
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
    parser.add_argument("--limit", help="Test at most n domains.", type=int)
    parser.add_argument(
        "--grep", help="Test only domain matching this argument.", type=str
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
    if args.limit is None:
        args.limit = 2**32
    return args


async def rescan_domains(
    to_check: list[Domain], kindness: int = 0, verbose: int = 0, silent: bool = False
) -> None:
    sem = asyncio.Semaphore([20, 10, 5, 2][kindness])

    async def with_sem(coroutine):
        async with sem:
            return await coroutine

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as client:
        gather = asyncio.gather if (verbose or silent) else tqdm.gather
        await gather(*[with_sem(check_domain(domain, client)) for domain in to_check])

    await asyncio.sleep(
        0.5  # See https://docs.aiohttp.org/en/stable/client_advanced.html#graceful-shutdown
    )  # Which is fixed in aiohttp 4.


def main():
    args = parse_args()
    logging.basicConfig(
        level=[logging.WARNING, logging.INFO, logging.DEBUG][args.verbose]
    )
    domains = parse_csv_file(args.output) | parse_files(*args.files)

    to_check = sorted(
        domains, key=lambda domain: min(domain.http_last_check, domain.https_last_check)
    )[: args.limit]

    if args.grep:
        to_check = [domain for domain in to_check if args.grep in domain.name]

    try:
        asyncio.run(rescan_domains(to_check, args.kindness, args.verbose, args.silent))
    except KeyboardInterrupt:
        logging.info("Interrupted by keyboard, saving before exiting…")

    write_csv_file(args.output, domains)


if __name__ == "__main__":
    main()
