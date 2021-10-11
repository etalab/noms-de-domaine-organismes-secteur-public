"""Consolidate a bunch of files containing hosts names to a single
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

logger = logging.getLogger("consolidate")


async def check_host(
    host: str, client: aiohttp.ClientSession, kindness: int = 0
) -> Tuple[str, bool]:
    """Check if the given host replies an ok-ish response over HTTP or HTTPS.

    kindness range from 0 to 3 included (from fast to very kind).
    """
    for protocol in "https", "http":
        await asyncio.sleep((1 + random.random() * 5) * kindness ** 2)
        try:
            url = f"{protocol}://{host}"
            async with client.head(url, allow_redirects=True) as response:
                if response.status == 200:
                    logger.info("%s: OK", url)
                    return host, True
                logger.info("%s: failure, status={response.status}", url)
        except aiohttp.ClientError as err:
            logger.info("%s: failure: %s", url, err)
        except asyncio.TimeoutError:
            logger.info("%s: failure: Timeout", url)
        except UnicodeError as err:  # Can happen on malformed IDNA.
            logger.info("%s: failure: %s", url, err)
    return host, False


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
    args = parser.parse_args()
    args.verbose = min(args.verbose, 2)
    return args


def clean_host(line):
    """Check if the given line looks like a hostname.

    Clean as needed, raise as needed.
    """
    line = line.strip()
    if not line:
        return None
    host = line.split()[0]
    if "/" in host:
        raise ValueError(f"Unexpected '/' in host: {line}")
    return host.lower()


def parse_files(*files) -> set[str]:
    """Parse one or many files containing lines of hosts."""
    lines = chain(*[file.read_text(encoding="UTF-8").split("\n") for file in files])
    return {host for line in lines if (host := clean_host(line))}


async def main():
    args = parse_args()
    source_hosts = parse_files(*args.files)
    known_hosts = parse_files(args.output)
    unknown_hosts = list(source_hosts - known_hosts)
    random.shuffle(unknown_hosts)
    logging.basicConfig(
        level=[logging.ERROR, logging.INFO, logging.DEBUG][args.verbose]
    )
    async with aiohttp.ClientSession(
        raise_for_status=True,
        connector=aiohttp.TCPConnector(
            limit=1 if args.kindness else 10, limit_per_host=1
        ),
    ) as client:
        results = await asyncio.gather(
            *[check_host(host, client, args.kindness) for host in unknown_hosts]
        )
    accepted = {host for host, is_up in results if is_up}
    args.output.write_text(
        "\n".join(sorted(list(known_hosts | accepted))) + "\n",
        encoding="UTF-8",
    )
    await asyncio.sleep(
        0.5  # See https://docs.aiohttp.org/en/stable/client_advanced.html#graceful-shutdown
    )  # Which is fixed in aiohttp 4.


if __name__ == "__main__":
    asyncio.run(main())
