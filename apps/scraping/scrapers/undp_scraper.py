"""
API/RSS scraper for UNDP procurement notices.
"""
import json
import logging
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

from .base import BaseScraper

logger = logging.getLogger(__name__)


class UNDPScraper(BaseScraper):
    """Scraper for UNDP notices through UNGM, with UNDP RSS fallback."""

    UNGM_API_URL = "https://www.ungm.org/Public/Notice"
    UNDP_RSS_URL = "https://procurement-notices.undp.org/feed.cfm?po_filter=all"

    def fetch(self, url: Optional[str] = None, **kwargs) -> str:
        api_url = url or self.config.get('api_url', self.UNGM_API_URL)
        if not self._check_robots_txt(api_url):
            raise PermissionError(f"robots.txt disallows: {api_url}")

        page_size = int(self.config.get('page_size', 50))
        max_items = int(self.config.get('max_items', 200))
        items: List[Dict[str, Any]] = []
        page_index = 0

        try:
            while len(items) < max_items:
                resp = self._http_get(
                    api_url,
                    headers={'Accept': 'application/json'},
                    params={
                        'noticeType': self.config.get('notice_type', 0),
                        'pageIndex': page_index,
                        'pageSize': page_size,
                    },
                )
                page_items = self._extract_ungm_items(resp.json())
                if not isinstance(page_items, list):
                    raise ValueError(f"UNGM returned unexpected response type: {type(page_items).__name__}")
                if not page_items:
                    break

                remaining = max_items - len(items)
                items.extend(page_items[:remaining])

                if len(page_items) < page_size:
                    break
                page_index += 1

            return json.dumps({'source': 'ungm_api', 'items': items})
        except Exception as exc:
            logger.warning(f"UNDP: UNGM API unavailable; falling back to RSS: {exc}")

        rss_url = self.config.get('rss_url', self.UNDP_RSS_URL)
        if not self._check_robots_txt(rss_url):
            raise PermissionError(f"robots.txt disallows: {rss_url}")
        resp = self._http_get(rss_url)
        return json.dumps({'source': 'rss', 'xml': resp.text})

    def parse(self, raw_data: str) -> List[Dict[str, Any]]:
        try:
            payload = json.loads(raw_data)
        except (TypeError, json.JSONDecodeError) as exc:
            logger.warning(f"UNDP: could not parse fetch payload: {exc}")
            return []

        if payload.get('source') == 'ungm_api':
            return self._parse_ungm_items(self._extract_ungm_items(payload))
        if self._extract_ungm_items(payload):
            return self._parse_ungm_items(self._extract_ungm_items(payload))
        if payload.get('source') == 'rss':
            return self._parse_rss(payload.get('xml') or '')
        return []

    def _parse_ungm_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        opportunities: List[Dict[str, Any]] = []
        seen_ids = set()

        for item in items:
            try:
                opp = self._parse_ungm_item(item)
                if opp and opp['external_id'] not in seen_ids:
                    seen_ids.add(opp['external_id'])
                    opportunities.append(self._standardize_item(opp, self.source))
            except Exception as exc:
                logger.warning(f"UNDP: error parsing UNGM notice: {exc}")

        return opportunities

    def _parse_ungm_item(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        title = self._clean_text(item.get('Title') or item.get('title') or item.get('noticeTitle'))
        unique_key = self._clean_text(str(
            item.get('NoticeId') or item.get('noticeId') or item.get('id') or
            item.get('Reference') or item.get('reference') or ''
        ))
        if not title or not unique_key:
            return None

        notice_id = self._clean_text(str(item.get('NoticeId') or item.get('noticeId') or item.get('id') or ''))
        notice_type = self._clean_text(item.get('NoticeTypeCode') or item.get('noticeType') or item.get('type'))
        deadline = self._parse_date(item.get('DeadlineDate') or item.get('deadlineDate') or item.get('deadline'))
        published_at = self._parse_date(item.get('PublishedDate') or item.get('publishedDate') or item.get('publicationDate'))
        external_url = item.get('Url') or item.get('url') or (
            f"{self.UNGM_API_URL}/{notice_id}" if notice_id else self.UNGM_API_URL
        )
        description = self._html_to_text(item.get('Description') or item.get('description')) or title
        country = self._clean_text(item.get('CountryName') or item.get('countryName') or item.get('country')) or 'International'
        agency = self._clean_text(item.get('AgencyName') or item.get('agencyName') or item.get('agency'))
        organization = self.config.get('organization') or agency or 'UNGM'

        return {
            'external_id': self._make_external_id('UNGM', unique_key),
            'external_url': external_url,
            'title': title,
            'organization': organization,
            'client': self.config.get('client') or agency or 'United Nations',
            'sector': notice_type,
            'country': country,
            'region': 'Global',
            'description': description,
            'value': None,
            'currency': 'USD',
            'deadline': deadline.isoformat() if deadline else None,
            'published_at': published_at.isoformat() if published_at else None,
            'language': 'en',
            'sector_tags': [notice_type] if notice_type else [],
            'geographic_scope': {'countries': [country], 'region': 'Global'},
            'source_metadata': {
                'notice_id': notice_id,
                'reference': item.get('Reference'),
                'notice_type': notice_type,
                'scraped_from': 'ungm.org',
            },
        }

    @staticmethod
    def _extract_ungm_items(payload: Any) -> List[Dict[str, Any]]:
        if isinstance(payload, list):
            return payload
        if not isinstance(payload, dict):
            return []
        for key in ('items', 'data', 'results', 'notices', 'rows'):
            value = payload.get(key)
            if isinstance(value, list):
                return value
        nested = payload.get('response') or payload.get('result')
        if isinstance(nested, dict):
            for key in ('items', 'data', 'results', 'notices', 'rows'):
                value = nested.get(key)
                if isinstance(value, list):
                    return value
        return []

    def _parse_rss(self, xml_text: str) -> List[Dict[str, Any]]:
        opportunities: List[Dict[str, Any]] = []
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as exc:
            logger.warning(f"UNDP: could not parse RSS feed: {exc}")
            return []

        seen_ids = set()
        for rss_item in root.findall('.//item'):
            try:
                opp = self._parse_rss_item(rss_item)
                if opp and opp['external_id'] not in seen_ids:
                    seen_ids.add(opp['external_id'])
                    opportunities.append(self._standardize_item(opp, self.source))
            except Exception as exc:
                logger.warning(f"UNDP: error parsing RSS item: {exc}")

        return opportunities

    def _parse_rss_item(self, rss_item: ET.Element) -> Optional[Dict[str, Any]]:
        title = self._clean_text(self._child_text(rss_item, 'title'))
        link = self._clean_text(self._child_text(rss_item, 'link'))
        guid = self._clean_text(self._child_text(rss_item, 'guid'))
        description = self._html_to_text(self._child_text(rss_item, 'description')) or title
        unique_key = guid or link or title
        if not title or not unique_key:
            return None

        published_at = self._parse_date(self._child_text(rss_item, 'pubDate'))
        deadline = self._extract_deadline(description)

        return {
            'external_id': self._make_external_id('UNDP', unique_key),
            'external_url': link or self.UNDP_RSS_URL,
            'title': title,
            'organization': 'UNDP',
            'client': 'UNDP / UN System',
            'sector': '',
            'country': 'International',
            'region': 'Global',
            'description': description,
            'value': None,
            'currency': 'USD',
            'deadline': deadline.isoformat() if deadline else None,
            'published_at': published_at.isoformat() if published_at else None,
            'language': 'en',
            'sector_tags': [],
            'geographic_scope': {'countries': ['International'], 'region': 'Global'},
            'source_metadata': {
                'guid': guid,
                'scraped_from': 'procurement-notices.undp.org',
                'source_format': 'rss',
            },
        }

    @staticmethod
    def _child_text(item: ET.Element, tag: str) -> str:
        child = item.find(tag)
        return child.text if child is not None and child.text else ''

    def _extract_deadline(self, text: str):
        """Extract deadline date from free text in RSS descriptions."""
        import re
        patterns = [
            r'(?:deadline|closing date|submission deadline|due date)\s*[:\-]?\s*([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
            r'(?:deadline|closing date|submission deadline|due date)\s*[:\-]?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})',
            r'(?:deadline|closing date|submission deadline|due date)\s*[:\-]?\s*(\d{1,2}\s+[A-Za-z]{3,12}\s+\d{4})',
        ]
        for pattern in patterns:
            match = re.search(pattern, text or '', re.I)
            if match:
                parsed = self._parse_date(match.group(1))
                if parsed:
                    return parsed
        return None

    def _html_to_text(self, value: Any) -> str:
        if not value:
            return ''
        return self._clean_text(BeautifulSoup(str(value), 'html.parser').get_text(' ', strip=True))
