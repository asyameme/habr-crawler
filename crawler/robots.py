from urllib.parse import urlparse
from urllib import robotparser
import logging

import httpx

logger = logging.getLogger(__name__)


class RobotsChecker:
    def __init__(self):
        self._parsers = {}

    def _get_parser(self, host: str) -> robotparser.RobotFileParser:
        if host not in self._parsers:
            rp = robotparser.RobotFileParser()
            robots_url = f"https://{host}/robots.txt"
            try:
                response = httpx.get(robots_url, timeout=10, follow_redirects=True)
                if response.status_code == 200:
                    rp.parse(response.text.splitlines())
                logger.info(f"Robots.txt loaded for {host}")
            except Exception as e:
                logger.warning(f"Failed to fetch robots.txt for {host}: {e}")
                rp.allow_all = True
            self._parsers[host] = rp
        return self._parsers[host]

    def is_allowed(self, url: str) -> bool:
        host = urlparse(url).hostname
        if not host:
            return True
        parser = self._get_parser(host)
        user_agent = "*"
        allowed = parser.can_fetch(user_agent, url)
        if not allowed:
            logger.info(f"Blocked by robots.txt: {url}")
        return allowed