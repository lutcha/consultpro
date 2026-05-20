"""
Scraper for GIZ jobs and tender listings.
"""
import logging
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from django.utils import timezone

from .base import BaseScraper

logger = logging.getLogger(__name__)


class GIZScraper(BaseScraper):
    """Scraper for GIZ opportunity listings."""

    BASE_URL = "https://www.giz.de"
    DEFAULT_URL = "https://www.giz.de/en/jobs/jobs.html"
    TENDERS_URL = "https://www.giz.de/en/mediacenter/107225.html"

    TITLE_SELECTORS = ['h2 a', 'h3 a', 'h2', 'h3', 'a']
    COUNTRY_SELECTORS = ['.country', '.location', '[class*="country"]', '[class*="location"]']
    DEADLINE_SELECTORS = ['time[datetime]', 'time', '.deadline', '[class*="deadline"]', '[class*="date"]']
    SECTOR_SELECTORS = ['.sector', '.category', '[class*="sector"]', '[class*="category"]']

    def fetch(self, url: Optional[str] = None, **kwargs) -> str:
        target = url or self.config.get('url') or self.source.url or self.DEFAULT_URL
        if not self._check_robots_txt(target):
            raise PermissionError(f"robots.txt disallows: {target}")
        response = self._http_get(target)
        return response.text

    def parse(self, raw_data: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(raw_data or '', 'lxml')
        items = soup.find_all('article')
        if not items:
            for selector in self.config.get('item_selectors', ['table tr', 'div.tender', 'div.notice', 'li']):
                items = soup.select(selector)
                if items:
                    break
        if len(items) == 0:
            logging.warning("GIZ: JS-heavy page detected — Playwright may be required")
            return []

        opportunities = []
        seen_ids = set()
        for article in items:
            try:
                item = self._parse_article(article)
                if item and item['external_id'] not in seen_ids:
                    seen_ids.add(item['external_id'])
                    standardized = self._standardize_item(item, self.source)
                    standardized['raw_payload'] = item
                    opportunities.append(standardized)
            except Exception as exc:
                logger.warning("GIZ: error parsing article: %s", exc)
        return opportunities

    def _parse_article(self, article) -> Optional[Dict[str, Any]]:
        text = self._clean_text(article.get_text(separator=' ', strip=True))
        if not text:
            return None

        title_elem = self._first_match(article, self.TITLE_SELECTORS)
        title = self._clean_text(title_elem.get_text()) if title_elem else text[:300]
        if not title:
            return None

        link_elem = title_elem if getattr(title_elem, 'name', None) == 'a' else article.select_one('a[href]')
        base_url = self.config.get('url') or self.source.url or self.BASE_URL
        detail_url = base_url
        if link_elem and link_elem.get('href'):
            detail_url = urljoin(base_url, link_elem['href'])

        country = self._extract_selector_text(article, self.COUNTRY_SELECTORS)
        sector = self._extract_selector_text(article, self.SECTOR_SELECTORS)
        deadline_text = self._extract_deadline_text(article, text)
        deadline = self._parse_date(deadline_text) if deadline_text else None

        raw_id = detail_url or title
        external_id = self._make_external_id('GIZ', raw_id)

        return {
            'external_id': external_id,
            'external_url': detail_url,
            'title': title,
            'organization': 'GIZ',
            'client': 'Deutsche Gesellschaft fuer Internationale Zusammenarbeit',
            'sector': sector or 'International Development',
            'country': country or '',
            'region': 'International',
            'description': text,
            'deadline': deadline.isoformat() if deadline else None,
            'published_at': timezone.now().isoformat(),
            'language': 'en',
            'sector_tags': [sector] if sector else [],
            'geographic_scope': {
                'countries': [country] if country else [],
                'region': 'International',
            },
            'source_metadata': {
                'scraped_from': 'giz.de',
                'deadline_text': deadline_text,
            },
        }

    def _first_match(self, element, selectors):
        for selector in selectors:
            match = element.select_one(selector)
            if match:
                return match
        return None

    def _extract_selector_text(self, element, selectors) -> str:
        match = self._first_match(element, selectors)
        return self._clean_text(match.get_text()) if match else ''

    def _extract_deadline_text(self, article, text: str) -> str:
        for selector in self.DEADLINE_SELECTORS:
            match = article.select_one(selector)
            if match:
                value = match.get('datetime') or match.get_text(strip=True)
                if value:
                    return self._clean_text(value)

        patterns = [
            r'(?:deadline|closing date|apply by)\s*[:\-]?\s*([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
            r'(?:deadline|closing date|apply by)\s*[:\-]?\s*(\d{1,2}[./-]\d{1,2}[./-]\d{4})',
            r'(\d{1,2}\s+[A-Za-z]{3,12}\s+\d{4})',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                return self._clean_text(match.group(1))
        return ''
