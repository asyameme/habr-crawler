from crawler.dedup import is_internal_url, normalize_url, should_crawl


def test_normalize_url_lowercases_host_and_removes_utm():
    url = 'HTTPS://HABR.COM/ru/articles/123?utm_source=x&b=2&a=1'
    assert normalize_url(url) == 'https://habr.com/ru/articles/123/?a=1&b=2'


def test_normalize_url_adds_trailing_slash_and_preserves_port():
    url = 'http://Example.com:8080/path'
    assert normalize_url(url) == 'http://example.com:8080/path/'


def test_is_internal_url_only_for_habr_domains():
    assert is_internal_url('https://habr.com/ru/articles/1/') is True
    assert is_internal_url('https://career.habr.com/vacancies/') is True
    assert is_internal_url('https://example.com/') is False
    assert is_internal_url('/relative/path') is False


def test_should_crawl_matches_expected_habr_patterns():
    assert should_crawl('https://habr.com/ru/articles/123/') is True
    #assert should_crawl('https://habr.com/ru/hubs/machine_learning/articles/page23/') is True
    assert should_crawl('https://habr.com/ru/companies/acme/articles/123/') is True
    assert should_crawl('https://habr.com/ru/news/123/') is False
