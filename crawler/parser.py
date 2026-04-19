from dataclasses import dataclass
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from crawler.dedup import normalize_url, is_internal_url


@dataclass
class LinkInfo:
    url: str
    anchor_text: str
    is_internal: bool


@dataclass
class ParseResult:
    title: str | None
    meta_description: str | None
    text_content: str | None
    links: list[LinkInfo]  


def parse(html: str, base_url: str) -> ParseResult:
    soup = BeautifulSoup(html, "lxml")

    title = soup.title.string if soup.title else None

    tag = soup.find('meta', attrs={'name': 'description'})
    meta_description = tag['content'] if tag else None

    text_content = soup.get_text(separator=" ", strip=True)
    links = soup.find_all('a')

    all_links = []
    for link in links:

        href = link.get('href')
        if not href or href.startswith("mailto:") or href.startswith("tel:") or href.startswith("javascript:"):
            continue

        abs_url = urljoin(base_url, href)
        norm_url = normalize_url(abs_url)
        is_internal = is_internal_url(norm_url)

        anchor_text = link.get_text(strip=True) 
        link_obj = LinkInfo(url=norm_url, anchor_text=anchor_text, is_internal=is_internal)
        
        all_links.append(link_obj)
    
    return ParseResult(title=title, meta_description=meta_description, text_content=text_content, links=all_links)


