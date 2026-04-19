from datetime import datetime, timezone

from sqlalchemy import BigInteger, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Frontier(Base):
    __tablename__ = "frontier"

    url_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("urls.id", ondelete="CASCADE"), primary_key=True
    )
    status: Mapped[str] = mapped_column(
        Text, nullable=False, default="queued"
    )
    depth: Mapped[int] = mapped_column(nullable=False, default=0)
    priority: Mapped[int] = mapped_column(nullable=False, default=100)
    discovered_from_url_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("urls.id", ondelete="SET NULL"), nullable=True
    )
    next_fetch_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    attempt_count: Mapped[int] = mapped_column(nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("idx_frontier_status_next_fetch", "status", "next_fetch_at"),
        Index("idx_frontier_priority", "priority"),
    )