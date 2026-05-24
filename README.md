# plg_sitemap — XML Sitemap

Generuje `/sitemap.xml` pro vyhledávače. Ostatní komponenty mohou přidávat URL přes hook `sitemap.collect_urls`.

## Admin

`/admin/plg_sitemap` — nastavení:
- **Aktivovat** — zapne/vypne endpoint `/sitemap.xml`
- **Zahrnout domovskou stránku** — automaticky přidá `/` s prioritou 1.0
- **Vlastní URL** — JSON pole s dalšími URL

## Hook `sitemap.collect_urls`

```python
from src.core.hooks import hooks

async def on_sitemap(*, base_url: str, db, **kwargs):
    return [
        {"loc": "/clanky", "priority": "0.8", "changefreq": "daily"},
        {"loc": "/clanky/muj-clanek", "priority": "0.6", "changefreq": "monthly"},
    ]

hooks.on("sitemap.collect_urls", on_sitemap)
```

Hodnota `loc` může být relativní cesta (plugin přidá `base_url`) nebo absolutní URL.

## Vývoj a testy

```bash
cd plugin/plg_sitemap
pip install -e ".[dev]"
pytest -q
```
