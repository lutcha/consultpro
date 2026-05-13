"""
Scraper for Cabo Verde's national public procurement portal.
https://contratacao.publico.cv/

Tries the portal REST API first (common on SIGEF/SICP-based portals used in
Lusophone Africa). Falls back to HTML scraping when the API is unavailable.
"""
import json
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlencode

from bs4 import BeautifulSoup

from .base import BaseScraper

logger = logging.getLogger(__name__)

BASE_URL = "https://contratacao.publico.cv"

# Common API paths on SICP/eSIGEF portals used in PALOP countries
_API_CANDIDATES = [
    "/api/v1/contratos",
    "/api/v1/anuncios",
    "/api/contratos",
    "/api/anuncios",
    "/rest/contratos",
]

# HTML selectors — tried in order
_ITEM_SELECTORS = [
    "table.table tbody tr",
    "div.announcement-item",
    "div.contract-item",
    "article",
    "div.item-row",
    "tr[data-id]",
    "tbody tr",
]
_TITLE_SELECTORS = ["td.title a", "td:nth-child(2) a", "h3", "h4", "a.title", "a", "td:nth-child(2)"]
_LINK_SELECTORS = ["a[href]"]
_DATE_SELECTORS = ["td.date", "td.deadline", "td:last-child", "time", ".prazo"]
_ENTITY_SELECTORS = ["td.entity", "td.entidade", "td:first-child", ".entidade"]


class CaboVerdeProcurementScraper(BaseScraper):
    """
    Scraper for contratacao.publico.cv — Cabo Verde's national e-procurement portal.

    Config keys:
        api_path      Override REST API path (default: auto-detected).
        page_size     Items per page for API mode (default: 50).
        max_items     Maximum items to return (default: 200).
        search_url    Override HTML search page URL.
        language      Language code (default: 'pt').
    """

    def fetch(self, url: Optional[str] = None, **kwargs) -> str:
        base = self.config.get("base_url", BASE_URL).rstrip("/")
        max_items = int(self.config.get("max_items", 200))

        # ── Try REST API ──────────────────────────────────────────────────────
        api_path = self.config.get("api_path")
        if api_path:
            result = self._fetch_api(base, api_path, max_items)
            if result:
                return result

        for path in _API_CANDIDATES:
            result = self._fetch_api(base, path, max_items)
            if result:
                return result

        # ── Fall back to HTML ─────────────────────────────────────────────────
        logger.info("CaboVerde: no API found — falling back to HTML scraping")
        search_url = self.config.get("search_url", f"{base}/")
        try:
            resp = self._http_get(search_url)
            items = self._extract_html_items(resp.text, search_url)
            return json.dumps({"source": "html", "items": items})
        except Exception as exc:
            logger.warning("CaboVerde: HTML fetch failed for %s: %s", search_url, exc)
            return json.dumps({"source": "html", "items": []})

    def parse(self, raw_data: str) -> List[Dict[str, Any]]:
        try:
            payload = json.loads(raw_data)
        except (TypeError, json.JSONDecodeError) as exc:
            logger.warning("CaboVerde: cannot decode payload: %s", exc)
            return []

        source = payload.get("source", "html")
        items = payload.get("items") or []

        opportunities: List[Dict[str, Any]] = []
        seen_ids: set = set()

        for item in items:
            try:
                opp = self._build_opportunity(item, source)
                if opp and opp["external_id"] not in seen_ids:
                    seen_ids.add(opp["external_id"])
                    opportunities.append(self._standardize_item(opp, self.source))
            except Exception as exc:
                logger.warning("CaboVerde: error parsing item: %s", exc)

        return opportunities

    # ── API fetch ─────────────────────────────────────────────────────────────

    def _fetch_api(self, base: str, path: str, max_items: int) -> Optional[str]:
        page_size = int(self.config.get("page_size", 50))
        endpoint = base + path
        all_items: List[Dict] = []
        page = 0

        try:
            while len(all_items) < max_items:
                params = {"page": page, "size": page_size, "limit": page_size, "offset": page * page_size}
                resp = self._http_get(f"{endpoint}?{urlencode(params)}")
                data = resp.json()

                # Handle various response shapes
                if isinstance(data, list):
                    batch = data
                elif isinstance(data, dict):
                    batch = (
                        data.get("results")
                        or data.get("data")
                        or data.get("items")
                        or data.get("contratos")
                        or data.get("anuncios")
                        or []
                    )
                else:
                    break

                if not batch:
                    break

                remaining = max_items - len(all_items)
                all_items.extend(batch[:remaining])

                if len(batch) < page_size:
                    break
                page += 1

            if all_items:
                logger.info("CaboVerde: API %s returned %d items", path, len(all_items))
                return json.dumps({"source": "api", "path": path, "items": all_items})

        except Exception as exc:
            logger.debug("CaboVerde: API path %s unavailable: %s", path, exc)

        return None

    # ── HTML extraction ───────────────────────────────────────────────────────

    def _extract_html_items(self, html: str, base_url: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html or "", "html.parser")
        for tag in soup(["script", "style", "noscript", "nav", "header", "footer"]):
            tag.decompose()

        elements = []
        for selector in _ITEM_SELECTORS:
            elements = soup.select(selector)
            if len(elements) >= 2:
                break

        items: List[Dict[str, Any]] = []
        for el in elements:
            title = _first_text(el, _TITLE_SELECTORS)
            if not title or len(title.strip()) < 5:
                continue
            link_tag = el.select_one("a[href]")
            link = urljoin(base_url, link_tag["href"]) if link_tag and link_tag.get("href") else base_url
            entity = _first_text(el, _ENTITY_SELECTORS)
            deadline = _first_text(el, _DATE_SELECTORS)

            items.append({
                "title": self._clean_text(title),
                "url": link,
                "entity": self._clean_text(entity),
                "deadline": deadline,
            })
        return items

    # ── Opportunity builder ───────────────────────────────────────────────────

    def _build_opportunity(self, item: Dict[str, Any], source: str) -> Optional[Dict[str, Any]]:
        if source == "api":
            title = self._clean_text(
                item.get("designacao")
                or item.get("objeto")
                or item.get("titulo")
                or item.get("title")
                or item.get("nome")
                or ""
            )
            external_id = str(
                item.get("id") or item.get("codigo") or item.get("reference") or item.get("url") or title
            )
            url = item.get("url") or item.get("link") or item.get("detalhe") or BASE_URL
            if url and not url.startswith("http"):
                url = BASE_URL.rstrip("/") + "/" + url.lstrip("/")
            entity = self._clean_text(item.get("entidade") or item.get("adjudicante") or "")
            deadline_str = item.get("prazoSubmissao") or item.get("deadline") or item.get("dataLimite") or ""
            published_str = item.get("dataCriacao") or item.get("publishedAt") or item.get("dataPublicacao") or ""
            value_raw = item.get("valor") or item.get("price") or item.get("valorBase")
        else:
            title = item.get("title") or ""
            external_id = item.get("url") or title
            url = item.get("url") or BASE_URL
            entity = item.get("entity") or ""
            deadline_str = item.get("deadline") or ""
            published_str = ""
            value_raw = None

        if not title:
            return None

        deadline = self._parse_date(deadline_str)
        published_at = self._parse_date(published_str)
        value, currency = self._extract_value(str(value_raw)) if value_raw else (None, "CVE")

        return {
            "external_id": self._make_external_id("CaboVerdeProcurement", external_id),
            "external_url": url,
            "title": title,
            "organization": entity or "Entidade Pública - Cabo Verde",
            "client": entity or "Governo de Cabo Verde",
            "sector": "Contratação Pública",
            "country": "Cabo Verde",
            "region": "Cabo Verde",
            "description": title,
            "value": value,
            "currency": currency or "CVE",
            "deadline": deadline.isoformat() if deadline else None,
            "published_at": published_at.isoformat() if published_at else None,
            "language": "pt",
            "sector_tags": ["contratação pública", "governo", "Cabo Verde"],
            "geographic_scope": {"countries": ["Cabo Verde", "CPV"], "region": "Cabo Verde"},
            "source_metadata": {
                "source_format": source,
                "scraped_from": "contratacao.publico.cv",
            },
        }


def _first_text(element, selectors: List[str]) -> str:
    for sel in selectors:
        tag = element.select_one(sel)
        if tag:
            text = tag.get_text(" ", strip=True)
            if text:
                return text
    return ""
