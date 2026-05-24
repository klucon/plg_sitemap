from __future__ import annotations

import json
from datetime import UTC, datetime
from xml.sax.saxutils import escape

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.hooks import hooks

from .models import SitemapSettings


async def get_or_create_settings(db: AsyncSession) -> SitemapSettings:
    s = (
        await db.execute(select(SitemapSettings).where(SitemapSettings.id == 1))
    ).scalar_one_or_none()
    if s is None:
        s = SitemapSettings(id=1)
        db.add(s)
        await db.commit()
        await db.refresh(s)
    return s


async def save_settings(
    db: AsyncSession,
    *,
    enabled: bool,
    include_homepage: bool,
    custom_urls: str,
) -> SitemapSettings:
    s = await get_or_create_settings(db)
    s.enabled = enabled
    s.include_homepage = include_homepage
    s.custom_urls = custom_urls
    s.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(s)
    return s


async def build_sitemap(db: AsyncSession, base_url: str) -> str | None:
    settings = await get_or_create_settings(db)
    if not settings.enabled:
        return None

    base = base_url.rstrip("/")
    entries: list[dict] = []

    if settings.include_homepage:
        entries.append({"loc": base + "/", "priority": "1.0", "changefreq": "daily"})

    results = await hooks.fire("sitemap.collect_urls", base_url=base, db=db)
    for result in results:
        if isinstance(result, list):
            for item in result:
                if not isinstance(item, dict) or "loc" not in item:
                    continue
                loc = str(item["loc"])
                if not loc.startswith("http"):
                    loc = base + "/" + loc.lstrip("/")
                entries.append(
                    {
                        "loc": loc,
                        "priority": str(item.get("priority", "0.5")),
                        "changefreq": str(item.get("changefreq", "weekly")),
                    }
                )

    try:
        for item in json.loads(settings.custom_urls or "[]"):
            if not isinstance(item, dict) or "loc" not in item:
                continue
            loc = str(item["loc"])
            if not loc.startswith("http"):
                loc = base + "/" + loc.lstrip("/")
            entries.append(
                {
                    "loc": loc,
                    "priority": str(item.get("priority", "0.5")),
                    "changefreq": str(item.get("changefreq", "monthly")),
                }
            )
    except (json.JSONDecodeError, TypeError):
        pass

    return _render_xml(entries)


def _render_xml(entries: list[dict]) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for e in entries:
        lines.append("  <url>")
        lines.append(f"    <loc>{escape(e['loc'])}</loc>")
        lines.append(f"    <changefreq>{escape(e['changefreq'])}</changefreq>")
        lines.append(f"    <priority>{escape(e['priority'])}</priority>")
        lines.append("  </url>")
    lines.append("</urlset>")
    return "\n".join(lines)
