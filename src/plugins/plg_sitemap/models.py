from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.database.base import Base


def _now() -> datetime:
    return datetime.now(UTC)


class SitemapSettings(Base):
    __tablename__ = "plg_sitemap_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    include_homepage: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    custom_urls: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now, nullable=False
    )
