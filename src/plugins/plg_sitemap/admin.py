from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.admin.deps import CurrentAdminUser
from src.api.admin.render import admin_render
from src.core.acl import require_admin_permission
from src.database.base import get_db_session

from .service import get_or_create_settings, save_settings

router = APIRouter(prefix="/admin/plg_sitemap", tags=["plg_sitemap"])


@router.get("", response_class=HTMLResponse)
async def index(
    request: Request,
    current_user: CurrentAdminUser,
    _acl: object = Depends(require_admin_permission("sitemap.manage")),
    db: AsyncSession = Depends(get_db_session),
) -> HTMLResponse:
    settings = await get_or_create_settings(db)
    flash = request.session.pop("flash", None)
    return await admin_render(
        "admin/plg_sitemap/index.html",
        request,
        db,
        user=current_user,
        settings=settings,
        flash=flash,
    )


@router.post("", response_class=HTMLResponse)
async def save(
    request: Request,
    current_user: CurrentAdminUser,
    _acl: object = Depends(require_admin_permission("sitemap.manage")),
    db: AsyncSession = Depends(get_db_session),
    enabled: str | None = Form(None),
    include_homepage: str | None = Form(None),
    custom_urls: str = Form("[]"),
) -> RedirectResponse:
    try:
        json.loads(custom_urls)
    except (json.JSONDecodeError, ValueError):
        custom_urls = "[]"

    await save_settings(
        db,
        enabled=enabled is not None,
        include_homepage=include_homepage is not None,
        custom_urls=custom_urls,
    )
    request.session["flash"] = {"type": "success", "text": "Nastavení uloženo."}
    return RedirectResponse("/admin/plg_sitemap", status_code=303)
