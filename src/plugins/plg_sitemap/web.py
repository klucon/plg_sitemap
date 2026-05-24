from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.base import get_db_session

from .service import build_sitemap

router = APIRouter(tags=["plg_sitemap"])


@router.get("/sitemap.xml")
async def sitemap_xml(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> Response:
    base_url = str(request.base_url).rstrip("/")
    xml = await build_sitemap(db, base_url)
    if xml is None:
        raise HTTPException(status_code=404)
    return Response(content=xml, media_type="application/xml; charset=utf-8")
