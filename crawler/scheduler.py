from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from models import Url, Frontier



def get_next_url(session: Session) -> tuple[Frontier, Url] | None:
    stmt = (
        select(Frontier, Url)
        .join(Url, Frontier.url_id == Url.id)
        .where(
            Frontier.status == "queued",
            Frontier.next_fetch_at <= datetime.now(timezone.utc),
        )
        .order_by(Frontier.priority.asc(), Frontier.depth.asc())
        .limit(1)
        .with_for_update(skip_locked=True)
    )
    result = session.execute(stmt).first()
    if not result:
        return None

    frontier, url = result
    frontier.status = "fetching"
    session.commit()
    
    return frontier, url
