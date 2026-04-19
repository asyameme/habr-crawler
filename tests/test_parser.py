from crawler.parser import parse


HTML = '''
<html>
  <head>
    <title>Test title</title>
    <meta name="description" content="desc here">
  </head>
  <body>
    <a href="/ru/articles/123?utm_source=x">Article</a>
    <a href="https://example.com/page">External</a>
    <a href="mailto:test@example.com">Mail</a>
    <a href="javascript:void(0)">JS</a>
    <a href="tel:+123">Call</a>
    <p>Hello <b>world</b></p>
  </body>
</html>
'''


def test_parse_extracts_metadata_text_and_links():
    result = parse(HTML, 'https://habr.com/base/')

    assert result.title == 'Test title'
    assert result.meta_description == 'desc here'
    assert 'Hello world' in result.text_content
    assert len(result.links) == 2

    internal, external = result.links
    assert internal.url == 'https://habr.com/ru/articles/123/'
    assert internal.anchor_text == 'Article'
    assert internal.is_internal is True

    assert external.url == 'https://example.com/page/'
    assert external.anchor_text == 'External'
    assert external.is_internal is False


def test_parse_handles_missing_optional_tags():
    result = parse('<html><body><a href="/x">x</a></body></html>', 'https://habr.com')
    assert result.title is None
    assert result.meta_description is None
    assert result.links[0].url == 'https://habr.com/x/'
