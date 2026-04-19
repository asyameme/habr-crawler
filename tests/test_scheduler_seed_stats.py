from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from analysis.stats import show_stats
from crawler.scheduler import get_next_url
from crawler.seed import load_seeds, SEED_URLS
from crawler import storage
from models import Frontier, Link, Page, Url


def test_get_next_url_returns_best_candidate_and_marks_fetching(session):
    now = datetime.now(timezone.utc)
    u1 = storage.get_or_create_url(session, 'https://habr.com/ru/articles/1/')
    u2 = storage.get_or_create_url(session, 'https://habr.com/ru/articles/2/')
    session.add_all([
        Frontier(url_id=u1.id, status='queued', depth=1, priority=20, next_fetch_at=now),
        Frontier(url_id=u2.id, status='queued', depth=0, priority=10, next_fetch_at=now),
    ])
    session.commit()

    frontier, url = get_next_url(session)

    assert url.id == u2.id
    assert frontier.status == 'fetching'


def test_get_next_url_skips_future_tasks(session):
    u1 = storage.get_or_create_url(session, 'https://habr.com/ru/articles/1/')
    session.add(Frontier(
        url_id=u1.id,
        status='queued',
        depth=0,
        priority=10,
        next_fetch_at=datetime.now(timezone.utc) + timedelta(hours=1),
    ))
    session.commit()

    assert get_next_url(session) is None


def test_load_seeds_is_idempotent(session):
    first = load_seeds(session)
    second = load_seeds(session)

    urls = session.execute(select(Url)).scalars().all()
    frontier = session.execute(select(Frontier)).scalars().all()

    assert first == len(SEED_URLS)
    assert second == 0
    assert len(urls) == len(SEED_URLS)
    assert len(frontier) == len(SEED_URLS)
    assert all(item.depth == 0 for item in frontier)


def test_show_stats_prints_core_sections(session, capsys):
    src = storage.get_or_create_url(session, 'https://habr.com/ru/articles/1/')
    ext = storage.get_or_create_url(session, 'https://example.com/page')
    page = Page(
        url_id=src.id,
        final_url=src.url,
        http_status=200,
        content_type='text/html',
        content_length=10,
        content_hash='abc',
        response_time_ms=11,
        title='Article 1',
        meta_description='desc',
        html='<html></html>',
        text_content='hello',
        is_html=True,
    )
    session.add(page)
    session.flush()
    session.add(Link(from_page_id=page.id, to_url_id=ext.id, anchor_text='click', is_internal=False))
    session.add(Frontier(url_id=src.id, status='done', depth=0, priority=10))
    session.commit()

    show_stats(session)
    out = capsys.readouterr().out
    assert 'Всего обработано 1 уникальных страниц' in out
    assert 'Топ-10 внешних доменов' in out
    assert 'HTTP-статусы' in out
    assert 'Article 1' in out
