from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from .scheduler import get_next_url
from .fetcher import fetch, logger
from .parser import parse
from . import storage
from config import DATABASE_URL, MAX_PAGES

engine = create_engine(DATABASE_URL)

def run(max_pages: int = MAX_PAGES):
    with Session(engine) as session:
        count = 0

        while count < max_pages:
            result = get_next_url(session=session)
            if not result:
                break
            frontier, nxt_url = result 
            logger.info(f"[{count}/{max_pages}] Fetching: {nxt_url.url}")
            fetch_result = fetch(nxt_url.url)
            storage.save_fetch_attempt(session=session, url_id=nxt_url.id, fetch_result=fetch_result)
            
            if fetch_result.error:
                storage.mark_failed(session=session, frontier=frontier, error=fetch_result.error)
                logger.info(f' - fetch error: {fetch_result.error}, url {fetch_result.final_url}')
                continue

            if not fetch_result.is_html:
                storage.save_page(session=session, url_id=nxt_url.id, fetch_result=fetch_result, parse_result=None)
                storage.mark_done(session=session, frontier=frontier)
                logger.info(f' - is not html, url: {fetch_result.final_url}')
                count += 1
                continue

            parse_result = parse(fetch_result.html, fetch_result.final_url)
            
            saved_page = storage.save_page(session=session, url_id=nxt_url.id, fetch_result=fetch_result, parse_result=parse_result)
            if not saved_page:
                storage.mark_done(session=session, frontier=frontier)
                logger.info(f" - duplicate,  skipped: {fetch_result.final_url}")
                continue
            storage.save_links(session=session, page_id=saved_page.id, links=parse_result.links, parent_url_id=nxt_url.id, depth=frontier.depth)
            storage.mark_done(session=session, frontier=frontier)
            logger.info(f' - successful page saving, url: {fetch_result.final_url}')
            count += 1