from __future__ import annotations

import json

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.plugins.plg_sitemap.service import (
    build_sitemap,
    get_or_create_settings,
    save_settings,
)

# ---------------------------------------------------------------------------
# service layer
# ---------------------------------------------------------------------------


async def test_get_or_create_returns_defaults(db_session: AsyncSession):
    s = await get_or_create_settings(db_session)
    assert s.id == 1
    assert s.enabled is True
    assert s.include_homepage is True
    assert s.custom_urls == "[]"


async def test_get_or_create_idempotent(db_session: AsyncSession):
    s1 = await get_or_create_settings(db_session)
    s2 = await get_or_create_settings(db_session)
    assert s1.id == s2.id


async def test_save_settings(db_session: AsyncSession):
    await save_settings(
        db_session,
        enabled=False,
        include_homepage=False,
        custom_urls='[{"loc": "/test"}]',
    )
    s = await get_or_create_settings(db_session)
    assert s.enabled is False
    assert s.include_homepage is False
    assert s.custom_urls == '[{"loc": "/test"}]'


async def test_build_sitemap_disabled_returns_none(db_session: AsyncSession):
    await save_settings(db_session, enabled=False, include_homepage=True, custom_urls="[]")
    result = await build_sitemap(db_session, "http://example.com")
    assert result is None


async def test_build_sitemap_contains_xml_declaration(db_session: AsyncSession):
    xml = await build_sitemap(db_session, "http://example.com")
    assert xml is not None
    assert xml.startswith('<?xml version="1.0"')
    assert "<urlset" in xml


async def test_build_sitemap_includes_homepage(db_session: AsyncSession):
    xml = await build_sitemap(db_session, "http://example.com")
    assert xml is not None
    assert "<loc>http://example.com/</loc>" in xml


async def test_build_sitemap_no_homepage_when_disabled(db_session: AsyncSession):
    await save_settings(db_session, enabled=True, include_homepage=False, custom_urls="[]")
    xml = await build_sitemap(db_session, "http://example.com")
    assert xml is not None
    assert "<loc>http://example.com/</loc>" not in xml


async def test_build_sitemap_custom_urls(db_session: AsyncSession):
    custom = json.dumps([{"loc": "/stranky/kontakt", "priority": "0.7", "changefreq": "monthly"}])
    await save_settings(db_session, enabled=True, include_homepage=False, custom_urls=custom)
    xml = await build_sitemap(db_session, "http://example.com")
    assert xml is not None
    assert "<loc>http://example.com/stranky/kontakt</loc>" in xml
    assert "<priority>0.7</priority>" in xml


async def test_build_sitemap_hook_urls(db_session: AsyncSession):
    from src.core.hooks import hooks

    async def _extra(*, base_url: str, db, **kwargs):
        return [{"loc": "/hook-path", "priority": "0.9", "changefreq": "weekly"}]

    hooks.on("sitemap.collect_urls", _extra)
    try:
        xml = await build_sitemap(db_session, "http://example.com")
        assert xml is not None
        assert "<loc>http://example.com/hook-path</loc>" in xml
        assert "<priority>0.9</priority>" in xml
    finally:
        hooks.off("sitemap.collect_urls", _extra)


async def test_build_sitemap_absolute_hook_url(db_session: AsyncSession):
    from src.core.hooks import hooks

    async def _extra(*, base_url: str, db, **kwargs):
        return [{"loc": "https://cdn.example.com/assets", "priority": "0.3"}]

    hooks.on("sitemap.collect_urls", _extra)
    try:
        xml = await build_sitemap(db_session, "http://example.com")
        assert xml is not None
        assert "<loc>https://cdn.example.com/assets</loc>" in xml
    finally:
        hooks.off("sitemap.collect_urls", _extra)


async def test_build_sitemap_invalid_custom_urls_graceful(db_session: AsyncSession):
    await save_settings(db_session, enabled=True, include_homepage=True, custom_urls="not-json")
    xml = await build_sitemap(db_session, "http://example.com")
    assert xml is not None
    assert "<loc>http://example.com/</loc>" in xml


# ---------------------------------------------------------------------------
# web route
# ---------------------------------------------------------------------------


async def test_sitemap_xml_endpoint(client: AsyncClient):
    resp = await client.get("/sitemap.xml")
    assert resp.status_code == 200
    assert "application/xml" in resp.headers["content-type"]
    assert b"<urlset" in resp.content


async def test_sitemap_xml_disabled_returns_404(client: AsyncClient, db_session: AsyncSession):
    await save_settings(db_session, enabled=False, include_homepage=True, custom_urls="[]")
    resp = await client.get("/sitemap.xml")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# admin routes
# ---------------------------------------------------------------------------


async def test_admin_requires_auth(client: AsyncClient):
    resp = await client.get("/admin/plg_sitemap", follow_redirects=False)
    assert resp.status_code in (302, 303)


async def test_admin_index_authenticated(auth_client: AsyncClient):
    resp = await auth_client.get("/admin/plg_sitemap", follow_redirects=False)
    assert resp.status_code == 200


async def test_admin_save_redirects(auth_client: AsyncClient):
    resp = await auth_client.post(
        "/admin/plg_sitemap",
        data={"enabled": "on", "include_homepage": "on", "custom_urls": "[]"},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert "/admin/plg_sitemap" in resp.headers["location"]


async def test_admin_save_persists(auth_client: AsyncClient, db_session: AsyncSession):
    await auth_client.post(
        "/admin/plg_sitemap",
        data={"custom_urls": "[]"},
        follow_redirects=False,
    )
    s = await get_or_create_settings(db_session)
    assert s.enabled is False
    assert s.include_homepage is False
