import logging
from urllib.parse import urlparse
from sqlalchemy import select
from sqlalchemy.orm import Session

from models import Url, Page, Link, Frontier, FetchAttempt
from crawler.dedup import normalize_url, is_internal_url
from crawler.fetcher import FetchResult
from crawler.parser import LinkInfo, ParseResult
from config import MAX_DEPTH
from .dedup import should_crawl
import hashlib
from datetime import datetime, timezone, timedelta


logger = logging.getLogger(__name__)


def get_or_create_url(session: Session, url: str) -> Url:
    norm_url = normalize_url(url)
    url_obj = session.execute(select(Url).where(Url.url == norm_url)).scalar_one_or_none()

    if url_obj:
        return url_obj
    
    parsed = urlparse(norm_url)

    new_url = Url(
        url=norm_url,
        scheme=parsed.scheme,
        host=parsed.hostname,
        path=parsed.path,
        query=parsed.query,
        is_internal=is_internal_url(norm_url)
    )

    session.add(new_url)
    session.flush()

    return new_url


def save_page(session: Session, url_id: int, fetch_result: FetchResult, parse_result: ParseResult = None) -> Page:
    
    content_hash = None
    if parse_result and parse_result.text_content:
        content_hash = hashlib.sha256(parse_result.text_content.encode()).hexdigest()

    if content_hash:
        existing = session.execute(select(Page).where(Page.content_hash == content_hash)).scalar_one_or_none()
        if existing:
            logger.info(f"duplicate content found: {fetch_result.final_url}")
            return None

    page = Page(
        url_id=url_id,
        final_url=fetch_result.final_url,
        http_status=fetch_result.http_status,
        content_type=fetch_result.content_type,
        content_length=fetch_result.content_length,
        content_hash=content_hash,
        response_time_ms=fetch_result.response_time_ms,
        html=fetch_result.html if fetch_result.is_html else None,
        is_html=fetch_result.is_html,
        title=parse_result.title if parse_result else None,
        meta_description=parse_result.meta_description if parse_result else None,
        text_content=parse_result.text_content if parse_result else None,
    )

    session.add(page)
    session.flush()

    return page


def add_to_frontier(session: Session, url_id: int, depth: int, priority: int, parent_url_id: int):
    frontier_obj = session.execute(select(Frontier).where(Frontier.url_id == url_id)).scalar_one_or_none()
    if frontier_obj:
        return
    if depth >= MAX_DEPTH:
        return
    url_obj = session.execute(select(Url).where(Url.id == url_id)).scalar_one()
    if not should_crawl(url_obj.url):
        return
    
    frontier = Frontier(
        url_id=url_id,
        status="queued",
        depth= depth + 1,
        priority=priority, 
        discovered_from_url_id=parent_url_id,

    )
    session.add(frontier)


def mark_done(session: Session, frontier: Frontier):
    frontier.status = "done"
    session.commit()


def save_fetch_attempt(session: Session, url_id: int, fetch_result: FetchResult):
    attempt = FetchAttempt(
        url_id=url_id,
        success=fetch_result.error is None,
        http_status=fetch_result.http_status,
        error_type="timeout" if "timed out" in (fetch_result.error or "") else "request_error" if fetch_result.error else None,
        error_message=fetch_result.error,
        response_time_ms=fetch_result.response_time_ms,
    )
    session.add(attempt)
    session.flush()


def mark_failed(session:Session, frontier: Frontier, error: str):
    if frontier.attempt_count >= 2:  # после трех попыток скачивания - failed
        frontier.status = "failed"
        frontier.last_error = error          
        frontier.attempt_count += 1
    else:
        frontier.status = "queued"
        backoff_seconds = 5 * (3 ** frontier.attempt_count)
        frontier.next_fetch_at = datetime.now(timezone.utc) + timedelta(seconds=backoff_seconds)
        frontier.attempt_count += 1
              
    session.commit()


def save_links(session: Session, page_id: int, links: list[LinkInfo], parent_url_id: int, depth: int):
    for link_info in links:
        url_obj = get_or_create_url(session=session, url=link_info.url)

        link = Link(
            from_page_id=page_id,
            to_url_id=url_obj.id,
            anchor_text=link_info.anchor_text,
            is_internal=link_info.is_internal,
        )

        session.add(link)
        add_to_frontier(session, url_obj.id, depth, 100, parent_url_id)




