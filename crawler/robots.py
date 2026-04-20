from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

DISALLOWED_PATHS = [
    "/search/",
    "/api/",
    "/auth/",
    "/kek/",
    "/sandbox/",
]


def is_allowed(url: str) -> bool:
    host = urlparse(url).hostname
    if not host or not host.endswith("habr.com"):
        return False
    path = urlparse(url).path
    for disallowed in DISALLOWED_PATHS:
        if path.startswith(disallowed):
            logger.info(f"Blocked by robots.txt: {url}")
            return False
    return True
