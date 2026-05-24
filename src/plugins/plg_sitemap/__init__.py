from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.registry import ComponentRegistry

_PLUGIN_DIR = Path(__file__).parent


def setup(registry: ComponentRegistry) -> None:
    from jinja2 import FileSystemLoader
    from src.core.templates import admin_templates
    from src.i18n.translator import translator

    from src.plugins.plg_sitemap import admin, web

    templates_dir = _PLUGIN_DIR / "templates"
    if templates_dir.is_dir():
        loaders = getattr(admin_templates.loader, "loaders", [])
        if not any(
            isinstance(ldr, FileSystemLoader) and str(templates_dir) in ldr.searchpath
            for ldr in loaders
        ):
            loaders.append(FileSystemLoader(str(templates_dir)))

    registry.register_router(admin.router)
    registry.register_router(web.router)
    translator.load_domain("plg_sitemap", _PLUGIN_DIR / "i18n")
