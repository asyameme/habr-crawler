import logging
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.orm import Session

from models import Url, Frontier
from crawler.dedup import normalize_url, is_internal_url


logger = logging.getLogger(__name__)

SEED_URLS = [
    f"https://habr.com/ru/hubs/machine_learning/articles/page{i}/"
    for i in range(1, 20)
]


def load_seeds(session: Session) -> int:
    count = 0
    for raw_url in SEED_URLS:
        url = normalize_url(raw_url)
        parsed = urlparse(url)

        existing = session.execute(
            select(Url).where(Url.url == url)
        ).scalar_one_or_none()

        if existing:
            logger.info(f"Seed already exists: {url}")
            continue

        url_obj = Url(
            url=url,
            scheme=parsed.scheme,
            host=parsed.hostname,
            path=parsed.path,
            query=parsed.query,
            is_internal=is_internal_url(url),
        )
        session.add(url_obj)
        session.flush()

        frontier = Frontier(
            url_id=url_obj.id,
            status="queued",
            depth=0,
            priority=10,
        )
        session.add(frontier)
        count += 1
        logger.info(f"Seed added: {url}")

    session.commit()
    return count