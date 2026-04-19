import pytest

from crawler.storage import get_or_create_url


def test_get_or_create_url_rejects_xmpp_url_without_host(session):
    """
    Regression test: non-HTTP URL like xmpp:aveysov@gmail.com/ must not reach
    INSERT into urls with host=None, otherwise DB raises NotNullViolation.
    """
    with pytest.raises((ValueError, AssertionError)):
        get_or_create_url(session, "xmpp:aveysov@gmail.com/")
