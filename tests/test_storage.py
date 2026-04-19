from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from crawler.fetcher import FetchResult
from crawler.parser import LinkInfo, ParseResult
from crawler import storage
from models import FetchAttempt, Frontier, Link, Page, Url


@pytest.fixture()
def fetch_result_html():
    return FetchResult(
        final_url='https://habr.com/ru/articles/123/',
        http_status=200,
        content_type='text/html; charset=utf-8',
        content_length=123,
        html='<html></html>',
        response_time_ms=42,
        is_html=True,
        error=None,
    )


@pytest.fixture()
def parse_result():
    return ParseResult(
        title='Title',
        meta_description='Desc',
        text_content='unique body text',
        links=[],
    )


def test_get_or_create_url_normalizes_and_reuses_existing(session):
    first = storage.get_or_create_url(session, 'HTTPS://HABR.COM/ru/articles/123?utm_source=x')
    second = storage.get_or_create_url(session, 'https://habr.com/ru/articles/123/')

    assert first.id == second.id
    assert first.host == 'habr.com'
    assert first.is_internal is True


def test_save_page_persists_full_html_page(session, fetch_result_html, parse_result):
    url = storage.get_or_create_url(session, fetch_result_html.final_url)

    page = storage.save_page(session, url.id, fetch_result_html, parse_result)

    assert page is not None
    assert page.title == 'Title'
    assert page.meta_description == 'Desc'
    assert page.html == '<html></html>'
    assert page.content_hash is not None


def test_save_page_returns_none_for_duplicate_content(session, fetch_result_html, parse_result):
    url1 = storage.get_or_create_url(session, 'https://habr.com/ru/articles/1/')
    url2 = storage.get_or_create_url(session, 'https://habr.com/ru/articles/2/')

    first = storage.save_page(session, url1.id, fetch_result_html, parse_result)
    second = storage.save_page(session, url2.id, fetch_result_html, parse_result)

    assert first is not None
    assert second is None
    assert session.execute(select(Page)).scalars().all() == [first]


def test_save_page_non_html_does_not_store_html_body(session):
    url = storage.get_or_create_url(session, 'https://habr.com/file.pdf')
    result = FetchResult(
        final_url='https://habr.com/file.pdf',
        http_status=200,
        content_type='application/pdf',
        content_length=10,
        html='binary-ish',
        response_time_ms=1,
        is_html=False,
        error=None,
    )

    page = storage.save_page(session, url.id, result, None)
    assert page.html is None
    assert page.is_html is False


def test_add_to_frontier_adds_only_supported_urls_and_respects_depth(session, monkeypatch):
    monkeypatch.setattr(storage, 'MAX_DEPTH', 2)
    url = storage.get_or_create_url(session, 'https://habr.com/ru/articles/123/')
    blocked = storage.get_or_create_url(session, 'https://habr.com/ru/news/123/')

    storage.add_to_frontier(session, url.id, depth=0, priority=50, parent_url_id=None)
    storage.add_to_frontier(session, blocked.id, depth=0, priority=50, parent_url_id=None)
    storage.add_to_frontier(session, url.id, depth=1, priority=50, parent_url_id=None)

    rows = session.execute(select(Frontier).order_by(Frontier.url_id)).scalars().all()
    assert len(rows) == 1
    assert rows[0].url_id == url.id
    assert rows[0].depth == 1


def test_mark_done_updates_status_and_commits(session):
    url = storage.get_or_create_url(session, 'https://habr.com/ru/articles/123/')
    frontier = Frontier(url_id=url.id, status='fetching', depth=0, priority=10)
    session.add(frontier)
    session.commit()

    storage.mark_done(session, frontier)
    refreshed = session.get(Frontier, url.id)
    assert refreshed.status == 'done'


def test_save_fetch_attempt_sets_timeout_error_type(session):
    url = storage.get_or_create_url(session, 'https://habr.com/ru/articles/123/')
    result = FetchResult(
        final_url=url.url,
        http_status=None,
        content_type=None,
        content_length=None,
        html=None,
        response_time_ms=None,
        is_html=None,
        error='request timed out',
    )

    storage.save_fetch_attempt(session, url.id, result)
    attempt = session.execute(select(FetchAttempt)).scalar_one()
    assert attempt.success is False
    assert attempt.error_type == 'timeout'


def test_mark_failed_requeues_with_backoff_then_marks_failed(session):
    url = storage.get_or_create_url(session, 'https://habr.com/ru/articles/123/')
    frontier = Frontier(
        url_id=url.id,
        status='fetching',
        depth=0,
        priority=1,
        attempt_count=0,
        next_fetch_at=datetime.now(timezone.utc),
    )
    session.add(frontier)
    session.commit()

    storage.mark_failed(session, frontier, 'boom')
    first = session.get(Frontier, url.id)
    assert first.status == 'queued'
    assert first.attempt_count == 1
    assert first.last_error is None

    storage.mark_failed(session, first, 'boom2')
    second = session.get(Frontier, url.id)
    assert second.status == 'queued'
    assert second.attempt_count == 2

    storage.mark_failed(session, second, 'boom3')
    third = session.get(Frontier, url.id)
    assert third.status == 'failed'
    assert third.attempt_count == 3
    assert third.last_error == 'boom3'


def test_save_links_creates_links_and_frontier_entries(session):
    page_url = storage.get_or_create_url(session, 'https://habr.com/ru/articles/100/')
    target1 = 'https://habr.com/ru/articles/123/'
    target2 = 'https://example.com/page'

    storage.save_links(
        session,
        page_id=1,
        links=[
            LinkInfo(url=target1, anchor_text='A1', is_internal=True),
            LinkInfo(url=target2, anchor_text='A2', is_internal=False),
        ],
        parent_url_id=page_url.id,
        depth=0,
    )
    session.commit()

    links = session.execute(select(Link).order_by(Link.id)).scalars().all()
    frontiers = session.execute(select(Frontier)).scalars().all()
    urls = session.execute(select(Url).order_by(Url.id)).scalars().all()

    assert len(links) == 2
    assert len(urls) == 3
    assert len(frontiers) == 1
    assert frontiers[0].depth == 1
