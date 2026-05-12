"""
Scraper for USAID procurement and partnership opportunities.

Targets multiple USAID pages since there is no single public machine-readable API:
  1. USAID Business Forecast (HTML table)
  2. USAID West Africa Regional mission opportunities
  3. USAID Cabo Verde country office

Falls back gracefully when pages return no items.
"""
import json
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .base import BaseScraper

logger = logging.getLogger(__name__)

DEFAULT_URLS = [
    "https://www.usaid.gov/partnership-opportunities",
    "https://www.usaid.gov/west-africa-regional/business-opportunities",
    "https://www.usaid.gov/cabo-verde",
]

# CSS selectors tried in order for each page
ITEM_SELECTORS = [
    "article",
    "div.views-row",
    "div.field-items .field-item",
    "table.views-table tbody tr",
    "li.views-row",
    "div.card",
]

TITLE_SELECTORS = ["h1", "h2", "h3", "h4", "a.field-content", "td.views-field-title a", "a"]
LINK_SELECTORS = ["a[href]"]
DESC_SELECTORS = ["div.field-body", "div.views-field-body", "p"]
DATE_SELECTORS = ["span.date-display-single", "time", ".date-display-start"]


class USAIDScraper(BaseScraper):
    """
    HTML scraper for USAID partnership and procurement opportunity pages.

    Config keys:
        urls        List of USAID page URLs to scrape (overrides defaults).
        max_items   Maximum total items to return across all pages (default: 100).
        country     Static country tag applied to all items (default: 'International').
        region      Static region (default: 'West Africa / Global').
    """

    def fetch(self, url: Optional[str] = None, **kwargs) -> str:
        urls = self.config.get("urls") or DEFAULT_URLS
        max_items = int(self.config.get("max_items", 100))

        all_items: List[Dict[str, Any]] = []

        for page_url in urls:
            if len(all_items) >= max_items:
                break
            try:
                resp = self._http_get(page_url)
                page_items = self._extract_items(resp.text, page_url)
                remaining = max_items - len(all_items)
                all_items.extend(page_items[:remaining])
                logger.info("USAID: %d items from %s", len(page_items), page_url)
            except Exception as exc:
                logger.warning("USAID: failed to fetch %s: %s", page_url, exc)

        return json.dumps({"items": all_items})

    def parse(self, raw_data: str) -> List[Dict[str, Any]]:
        try:
            payload = json.loads(raw_data)
            items = payload.get("items") or []
        except (TypeError, json.JSONDecodeError) as exc:
            logger.warning("USAID: could not decode payload: %s", exc)
            return []

        opportunities: List[Dict[str, Any]] = []
        seen_ids: set = set()

        for item in items:
            try:
                opp = self._build_opportunity(item)
                if opp and opp["external_id"] not in seen_ids:
                    seen_ids.add(opp["external_id"])
                    opportunities.append(self._standardize_item(opp, self.source))
            except Exception as exc:
                logger.warning("USAID: error parsing item: %s", exc)

        return opportunities

    # ── HTML extraction ───────────────────────────────────────────────────────

    def _extract_items(self, html: str, base_url: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html or "", "html.parser")
        for tag in soup(["script", "style", "noscript", "nav", "header", "footer"]):
            tag.decompose()

        elements = []
        for selector in ITEM_SELECTORS:
            elements = soup.select(selector)
            if len(elements) >= 2:
                break

        items: List[Dict[str, Any]] = []
        for el in elements:
            title = _first_text(el, TITLE_SELECTORS)
            if not title or len(title) < 10:
                continue
            link_tag = el.select_one(",".join(LINK_SELECTORS))
            link = urljoin(base_url, link_tag["href"]) if link_tag and link_tag.get("href") else base_url
            description = _first_text(el, DESC_SELECTORS) or title
            date_str = _first_text(el, DATE_SELECTORS)

            items.append({
                "title": self._clean_text(title),
                "url": link,
                "description": self._clean_text(description)[:1000],
                "date": date_str,
                "source_url": base_url,
            })

        return items

    def _build_opportunity(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        title = item.get("title") or ""
        url = item.get("url") or self.source.url
        if not title:
            return None

        published_at = self._parse_date(item.get("date"))
        country = self.config.get("country", "International")
        region = self.config.get("region", "West Africa / Global")

        return {
            "external_id": self._make_external_id("USAID", url),
            "external_url": url,
            "title": title,
            "organization": "USAID",
            "client": "US Agency for International Development",
            "sector": "International Development",
            "country": country,
            "region": region,
            "description": item.get("description") or title,
            "value": None,
            "currency": "USD",
            "deadline": None,
            "published_at": published_at.isoformat() if published_at else None,
            "language": "en",
            "sector_tags": ["USAID", "international development"],
            "geographic_scope": {"countries": [country], "region": region},
            "source_metadata": {
                "source_url": item.get("source_url"),
                "scraped_from": "usaid.gov",
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
