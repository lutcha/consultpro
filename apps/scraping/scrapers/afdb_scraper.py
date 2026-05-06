"""
API/RSS scraper for African Development Bank procurement notices.
"""
import json
import logging
import re
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .base import BaseScraper

logger = logging.getLogger(__name__)


class AfDBScraper(BaseScraper):
    """Scraper for AfDB procurement notices."""

    BASE_URL = "https://www.afdb.org"
    JSON_API_URL = "https://www.afdb.org/api/v1/node/procurement"
    RSS_URL = "https://www.afdb.org/en/projects-and-operations/procurement/rss"

    def fetch(self, url: Optional[str] = None, **kwargs) -> str:
        api_url = url or self.config.get('api_url', self.JSON_API_URL)
        if not self._check_robots_txt(api_url):
            raise PermissionError(f"robots.txt disallows: {api_url}")

        try:
            resp = self._http_get(api_url, params={
                '_format': 'json',
                'status': self.config.get('status', 1),
                'items_per_page': int(self.config.get('page_size', 50)),
                'page': int(self.config.get('page', 0)),
            })
            payload = resp.json()
            if isinstance(payload, list):
                return json.dumps({'source': 'json_api', 'items': payload})
            logger.warning("AfDB: JSON API did not return a list; falling back to RSS")
        except Exception as exc:
            logger.warning(f"AfDB: JSON API fetch failed; falling back to RSS: {exc}")

        rss_url = self.config.get('rss_url', self.RSS_URL)
        if not self._check_robots_txt(rss_url):
            raise PermissionError(f"robots.txt disallows: {rss_url}")
        resp = self._http_get(rss_url)
        return json.dumps({'source': 'rss', 'xml': resp.text})

    def parse(self, raw_data: str) -> List[Dict[str, Any]]:
        try:
            payload = json.loads(raw_data)
        except (TypeError, json.JSONDecodeError) as exc:
            logger.warning(f"AfDB: could not parse fetch payload: {exc}")
            return []

        if payload.get('source') == 'json_api':
            return self._parse_json_items(payload.get('items') or [])
        if payload.get('source') == 'rss':
            return self._parse_rss(payload.get('xml') or '')
        return []

    def _parse_json_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        opportunities: List[Dict[str, Any]] = []
        seen_ids = set()

        for item in items:
            try:
                opp = self._parse_json_item(item)
                if opp and opp['external_id'] not in seen_ids:
                    seen_ids.add(opp['external_id'])
                    opportunities.append(self._standardize_item(opp, self.source))
            except Exception as exc:
                logger.warning(f"AfDB: error parsing JSON item: {exc}")

        return opportunities

    def _parse_json_item(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        title = self._clean_text(item.get('title'))
        if not title:
            return None

        path = item.get('path') or {}
        relative_url = path.get('alias') if isinstance(path, dict) else None
        external_url = urljoin(self.BASE_URL, relative_url or item.get('url') or '')

        item_id = (
            item.get('nid') or item.get('id') or item.get('uuid') or
            item.get('field_reference') or relative_url or title
        )
        unique_key = self._clean_text(str(item_id))
        if not unique_key:
            return None

        body = item.get('body') or {}
        body_value = body.get('value') if isinstance(body, dict) else body
        description = self._html_to_text(body_value) or title
        deadline = self._parse_date(item.get('field_deadline')) or self._extract_date(description)
        published_at = self._parse_date(item.get('created') or item.get('published_at'))
        country = self._clean_text(item.get('field_country')) or self._extract_country(f"{title} {description}")
        sector = self._clean_text(item.get('field_category'))

        return self._build_item(
            unique_key=unique_key,
            title=title,
            external_url=external_url or self.RSS_URL,
            description=description,
            deadline=deadline,
            published_at=published_at,
            country=country,
            sector=sector,
            metadata={'api_id': item_id, 'source_format': 'json_api'},
        )

    def _parse_rss(self, xml_text: str) -> List[Dict[str, Any]]:
        opportunities: List[Dict[str, Any]] = []
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as exc:
            logger.warning(f"AfDB: could not parse RSS feed: {exc}")
            return []

        seen_ids = set()
        for rss_item in root.findall('.//item'):
            try:
                opp = self._parse_rss_item(rss_item)
                if opp and opp['external_id'] not in seen_ids:
                    seen_ids.add(opp['external_id'])
                    opportunities.append(self._standardize_item(opp, self.source))
            except Exception as exc:
                logger.warning(f"AfDB: error parsing RSS item: {exc}")

        return opportunities

    def _parse_rss_item(self, rss_item: ET.Element) -> Optional[Dict[str, Any]]:
        title = self._clean_text(self._child_text(rss_item, 'title'))
        link = self._clean_text(self._child_text(rss_item, 'link'))
        guid = self._clean_text(self._child_text(rss_item, 'guid'))
        description = self._html_to_text(self._child_text(rss_item, 'description')) or title
        unique_key = guid or link or title
        if not title or not unique_key:
            return None

        deadline = self._extract_date(description)
        published_at = self._parse_date(self._child_text(rss_item, 'pubDate'))
        country = self._extract_country(f"{title} {description}")

        return self._build_item(
            unique_key=unique_key,
            title=title,
            external_url=urljoin(self.BASE_URL, link) if link else self.RSS_URL,
            description=description,
            deadline=deadline,
            published_at=published_at,
            country=country,
            sector='Procurement',
            metadata={'guid': guid, 'source_format': 'rss'},
        )

    def _build_item(
        self,
        unique_key: str,
        title: str,
        external_url: str,
        description: str,
        deadline,
        published_at,
        country: str,
        sector: str,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        clean_country = country or 'Africa'
        clean_sector = sector or 'Procurement'
        return {
            'external_id': self._make_external_id('AfDB', unique_key),
            'external_url': external_url,
            'title': title,
            'organization': 'African Development Bank (AfDB)',
            'client': 'AfDB',
            'sector': clean_sector,
            'country': clean_country,
            'region': 'Africa',
            'description': description,
            'value': None,
            'currency': 'USD',
            'deadline': deadline.isoformat() if deadline else None,
            'published_at': published_at.isoformat() if published_at else None,
            'language': 'en',
            'sector_tags': [clean_sector] if clean_sector else [],
            'geographic_scope': {'countries': [clean_country], 'region': 'Africa'},
            'source_metadata': {
                'scraped_from': 'afdb.org',
                **metadata,
            },
        }

    @staticmethod
    def _child_text(item: ET.Element, tag: str) -> str:
        child = item.find(tag)
        return child.text if child is not None and child.text else ''

    def _extract_date(self, text: str):
        patterns = [
            r'(?:deadline|closing date|submission deadline)\s*[:\-]?\s*([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
            r'(?:deadline|closing date|submission deadline)\s*[:\-]?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})',
            r'(\d{1,2}\s+[A-Za-z]{3,12}\s+\d{4})',
        ]
        for pattern in patterns:
            match = re.search(pattern, text or '', re.I)
            if match:
                parsed = self._parse_date(match.group(1))
                if parsed:
                    return parsed
        return None

    def _extract_country(self, text: str) -> str:
        text_lower = (text or '').lower()
        if any(keyword in text_lower for keyword in ['cabo verde', 'cape verde']):
            return 'Cabo Verde'
        if any(keyword in text_lower for keyword in ['regional', 'multinational', 'africa']):
            return 'Africa'
        return ''

    def _html_to_text(self, value: Any) -> str:
        if not value:
            return ''
        return self._clean_text(BeautifulSoup(str(value), 'html.parser').get_text(' ', strip=True))
