import pytest

from crawler.dedup import should_crawl, normalize_url, is_internal_url


def test_should_not_crawl_non_http_scheme_even_if_path_looks_like_article():
    url = "xmpp:aveysov@gmail.com/ru/articles/123/"
    assert should_crawl(url) is False


def test_should_not_crawl_foreign_domain_with_habr_like_article_path():
    url = "https://www.mql5.com/ru/articles/123/"
    assert should_crawl(url) is False


def test_is_internal_url_accepts_only_habr_domain():
    assert is_internal_url("https://habr.com/ru/articles/1/") is True
    assert is_internal_url("https://mql5.com/ru/articles/1/") is False


def test_normalize_url_keeps_non_http_scheme_visible_for_validation():
    normalized = normalize_url("xmpp:aveysov@gmail.com")
    assert normalized.startswith("xmpp:")
