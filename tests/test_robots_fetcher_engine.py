from types import SimpleNamespace

import httpx

from crawler.fetcher import FetchResult, RateLimiter, fetch
from crawler.robots import RobotsChecker
from crawler import storage
from models import Frontier, Page, FetchAttempt, Link


class DummyRobotParser:
    def __init__(self, allowed=True):
        self.allowed = allowed
        self.parsed_lines = None

    def parse(self, lines):
        self.parsed_lines = list(lines)

    def can_fetch(self, user_agent, url):
        return self.allowed


class DummyResponse:
    def __init__(self, status_code=200, text='User-agent: *', headers=None, url='https://habr.com/ok', content=b'hello'):
        self.status_code = status_code
        self.text = text
        self.headers = headers or {'content-type': 'text/html'}
        self.url = url
        self.content = content


def test_robots_checker_fetches_and_caches_parser(monkeypatch):
    calls = []
    parser = DummyRobotParser(allowed=True)

    monkeypatch.setattr('crawler.robots.robotparser.RobotFileParser', lambda: parser)
    monkeypatch.setattr('crawler.robots.httpx.get', lambda *a, **k: calls.append((a, k)) or DummyResponse(text='User-agent: *\nAllow: /'))

    checker = RobotsChecker()
    assert checker.is_allowed('https://habr.com/ru/articles/1/') is True
    assert checker.is_allowed('https://habr.com/ru/articles/2/') is True
    assert len(calls) == 1
    assert parser.parsed_lines == ['User-agent: *', 'Allow: /']


def test_rate_limiter_waits_only_when_needed(monkeypatch):
    slept = []
    times = iter([100.0, 101.0, 101.0, 106.0])
    monkeypatch.setattr('crawler.fetcher.time.time', lambda: next(times))
    monkeypatch.setattr('crawler.fetcher.time.sleep', lambda sec: slept.append(sec))

    limiter = RateLimiter()
    limiter.wait_if_needed('https://habr.com/1')
    limiter.wait_if_needed('https://habr.com/2')

    assert slept == [9.0]


def test_fetch_returns_successful_html_result(monkeypatch):
    monkeypatch.setattr('crawler.fetcher.ua', SimpleNamespace(random='ua'))
    monkeypatch.setattr('crawler.fetcher.robots_checker', SimpleNamespace(is_allowed=lambda url: True))
    monkeypatch.setattr('crawler.fetcher.rate_limiter', SimpleNamespace(wait_if_needed=lambda url: None))
    monkeypatch.setattr('crawler.fetcher.time.time', lambda: 100.0)
    monkeypatch.setattr('crawler.fetcher.httpx.get', lambda *a, **k: DummyResponse(headers={'content-type': 'text/html; charset=utf-8'}, content=b'<html>x</html>', text='<html>x</html>', url='https://habr.com/final'))

    result = fetch('https://habr.com/start')

    assert result.final_url == 'https://habr.com/final'
    assert result.http_status == 200
    assert result.is_html is True
    assert result.error is None



def test_fetch_handles_request_errors(monkeypatch):
    monkeypatch.setattr('crawler.fetcher.ua', SimpleNamespace(random='ua'))
    monkeypatch.setattr('crawler.fetcher.robots_checker', SimpleNamespace(is_allowed=lambda url: True))
    monkeypatch.setattr('crawler.fetcher.rate_limiter', SimpleNamespace(wait_if_needed=lambda url: None))
    monkeypatch.setattr('crawler.fetcher.httpx.get', lambda *a, **k: (_ for _ in ()).throw(httpx.RequestError('boom')))

    result = fetch('https://habr.com/start')
    assert result.error == 'boom'
    assert result.http_status is None


def test_engine_run_processes_html_non_html_and_error_paths(session, engine, monkeypatch):
    import crawler.engine as engine_module

    url_html = storage.get_or_create_url(session, 'https://habr.com/ru/articles/1/')
    url_pdf = storage.get_or_create_url(session, 'https://habr.com/file.pdf')
    url_err = storage.get_or_create_url(session, 'https://habr.com/ru/articles/3/')
    session.add_all([
        Frontier(url_id=url_html.id, status='queued', depth=0, priority=1),
        Frontier(url_id=url_pdf.id, status='queued', depth=0, priority=2),
        Frontier(url_id=url_err.id, status='queued', depth=0, priority=3),
    ])
    session.commit()

    monkeypatch.setattr(engine_module, 'engine', engine)

    html_result = FetchResult(
        final_url=url_html.url,
        http_status=200,
        content_type='text/html',
        content_length=20,
        html='<html><title>X</title></html>',
        response_time_ms=5,
        is_html=True,
        error=None,
    )
    pdf_result = FetchResult(
        final_url=url_pdf.url,
        http_status=200,
        content_type='application/pdf',
        content_length=20,
        html='ignored',
        response_time_ms=5,
        is_html=False,
        error=None,
    )
    err_result = FetchResult(
        final_url=url_err.url,
        http_status=None,
        content_type=None,
        content_length=None,
        html=None,
        response_time_ms=None,
        is_html=None,
        error='network failure',
    )
    fetch_map = {
        url_html.url: html_result,
        url_pdf.url: pdf_result,
        url_err.url: err_result,
    }
    monkeypatch.setattr(engine_module, 'fetch', lambda url: fetch_map.get(url, err_result))
    monkeypatch.setattr(
        engine_module,
        'parse',
        lambda html, base_url: SimpleNamespace(
            title='Parsed title',
            meta_description='Parsed desc',
            text_content='Parsed body',
            links=[SimpleNamespace(url='https://habr.com/ru/articles/99/', anchor_text='next', is_internal=True)],
        ),
    )

    engine_module.run(max_pages=5)

    pages = session.query(Page).all()
    attempts = session.query(FetchAttempt).all()
    links = session.query(Link).all()
    html_frontier = session.get(Frontier, url_html.id)
    pdf_frontier = session.get(Frontier, url_pdf.id)
    err_frontier = session.get(Frontier, url_err.id)

    assert len(attempts) == 4
    assert len(pages) == 2
    assert len(links) == 1
    assert html_frontier.status == 'done'
    assert pdf_frontier.status == 'done'
    assert err_frontier.status == 'queued'
    assert err_frontier.attempt_count == 1
