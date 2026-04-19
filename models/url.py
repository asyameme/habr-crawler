from datetime import datetime, timezone

from sqlalchemy import Boolean, Index, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Url(Base):
    __tablename__ = "urls"

    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    scheme: Mapped[str | None] = mapped_column(Text)
    host: Mapped[str] = mapped_column(Text, nullable=False)
    path: Mapped[str | None] = mapped_column(Text)
    query: Mapped[str | None] = mapped_column(Text)
    is_internal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    discovered_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("idx_urls_host", "host"),
        Index("idx_urls_is_internal", "is_internal"),
    )