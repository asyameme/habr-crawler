from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
import re

UTM_PARAMS = {"utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term"}


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    host = parsed.hostname.lower() if parsed.hostname else ""
    port = f":{parsed.port}" if parsed.port else None
    path = parsed.path
    if not path.endswith("/"):
        path = path + "/"
    query_params = parse_qs(parsed.query, keep_blank_values=True)
    query_params = {
        k: v for k, v in query_params.items() if k.lower() not in UTM_PARAMS
    }
    query = urlencode(sorted(query_params.items()), doseq=True)
    netloc = f"{host}{port}" if port else host
    return urlunparse((scheme, netloc, path, "", query, ""))


def is_internal_url(url: str) -> bool:
    host = urlparse(url).hostname
    if not host:
        return False
    return host.endswith("habr.com")


ARTICLE_PATTERN = re.compile(r"/ru/articles/\d+/$")
COMPANY_ARTICLE_PATTERN = re.compile(r"/ru/companies/.+/articles/\d+/$")
HUB_PATTERN = re.compile(r"/ru/hubs/.+/articles/(/page\d+)?/$")


def should_crawl(url: str) -> bool:
    path = urlparse(url).path
    if ARTICLE_PATTERN.match(path):
        return True
    if COMPANY_ARTICLE_PATTERN.match(path):
        return True
    if HUB_PATTERN.match(path):
        return True
    return False
