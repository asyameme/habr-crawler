from datetime import datetime, timezone

from sqlalchemy import Boolean, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Link(Base):
    __tablename__ = "links"

    id: Mapped[int] = mapped_column(primary_key=True)
    from_page_id: Mapped[int] = mapped_column(
        ForeignKey("pages.id", ondelete="CASCADE"), nullable=False
    )
    to_url_id: Mapped[int] = mapped_column(
        ForeignKey("urls.id", ondelete="CASCADE"), nullable=False
    )
    anchor_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_internal: Mapped[bool] = mapped_column(Boolean, nullable=False)
    nofollow: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    discovered_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("idx_links_from_page_id", "from_page_id"),
        Index("idx_links_to_url_id", "to_url_id"),
        Index("idx_links_is_internal", "is_internal"),
    )