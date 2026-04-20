import time
import logging
from dataclasses import dataclass
import httpx
from config import DEFAULT_TIMEOUT, HABR_RATE_LIMIT_SEC
from fake_useragent import UserAgent
from urllib.parse import urlparse
from .robots import is_allowed



class RateLimiter:
    def __init__(self):
        self.last_fetch = {}  # {host: timestamp}

    def wait_if_needed(self, url: str):
        parsed = urlparse(url)
        host = parsed.hostname
        if not host:
            return

        min_pause = 3.
        if host.endswith("habr.com"):
            min_pause = HABR_RATE_LIMIT_SEC

        if host in self.last_fetch:
            elapsed = time.time() - self.last_fetch[host]
            if elapsed < min_pause:
                time.sleep(min_pause - elapsed)
                
        self.last_fetch[host] = time.time()
        return

    

@dataclass
class FetchResult:
    final_url: str
    http_status: int | None
    content_type: str | None
    content_length: int | None
    html: str | None
    response_time_ms: int | None
    is_html: bool | None
    error: str | None = None


ua = UserAgent()
logger = logging.getLogger(__name__)
rate_limiter = RateLimiter()




def fetch(url: str) -> FetchResult:
    start = time.time()
    headers = {"User-Agent": ua.random}
    try:
        if not is_allowed(url):
            return FetchResult(final_url=url, error="Blocked by robots.txt")
        rate_limiter.wait_if_needed(url=url)

        response = httpx.get(url, timeout=DEFAULT_TIMEOUT, follow_redirects=True, headers=headers)
        content_type = response.headers.get("content-type", "")
        is_html = "text/html" in content_type
        elapsed_ms = int((time.time() - start) * 1000)
        
        return FetchResult(
            final_url=str(response.url), 
            http_status=response.status_code, 
            content_type=content_type, 
            content_length=len(response.content), 
            html=response.text, 
            response_time_ms=elapsed_ms,
            is_html=is_html
            )

    except httpx.RequestError as exc:
        return FetchResult(
            final_url=url, 
            http_status=None, 
            content_type=None, 
            content_length=None, 
            html=None, 
            response_time_ms=None,
            is_html=None,
            error=str(exc)
            )
    