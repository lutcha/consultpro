"""
Generic portal scraper for sites with standard HTML structures.
Can be configured via scraper_config JSON without writing custom code.
"""
import logging
import re
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from django.utils import timezone

from .base import BaseScraper

logger = logging.getLogger(__name__)


class GenericPortalScraper(BaseScraper):
    """
    Generic scraper that uses CSS selectors from scraper_config.
    Expected config keys:
      - url: override URL
      - item_selectors: list of CSS selectors to find opportunity items
      - title_selector: CSS selector for title within item
      - link_selector: CSS selector for detail link within item
      - description_selector: CSS selector for description
      - deadline_selector: CSS selector for deadline text
      - date_selector: CSS selector for published date
      - reference_selector: CSS selector for reference number
      - organization: static organization name
      - client: static client name
      - country: static country
      - language: static language code
    """

    def fetch(self, url: Optional[str] = None, **kwargs) -> str:
        target = url or self.config.get('url', self.source.url)
        if not self._check_robots_txt(target):
            raise PermissionError(f"robots.txt disallows: {target}")
        resp = self._http_get(target)
        return resp.text

    def parse(self, raw_data: str) -> List[Dict[str, Any]]:
        opportunities = []
        soup = BeautifulSoup(raw_data, 'html.parser')

        item_selectors = self.config.get('item_selectors', ['article', 'div.item', 'tr'])
        items = []
        for sel in item_selectors:
            items = soup.select(sel)
            if items:
                logger.info(f"GenericPortal: matched selector '{sel}' with {len(items)} items")
                break

        for item in items:
            try:
                opp = self._parse_item(item)
                if opp and opp.get('title'):
                    opportunities.append(self._standardize_item(opp, self.source))
            except Exception as e:
                logger.warning(f"GenericPortal: error parsing item: {e}")
                continue

        return opportunities

    def _parse_item(self, item) -> Optional[Dict[str, Any]]:
        text = item.get_text(separator=' ', strip=True)
        if len(text) < 15:
            return None

        title_sel = self.config.get('title_selector', 'h2, h3, h4, a, strong')
        link_sel = self.config.get('link_selector', 'a[href]')
        desc_sel = self.config.get('description_selector', 'p, .description, .summary')
        deadline_sel = self.config.get('deadline_selector', '.deadline, .date, .prazo')
        date_sel = self.config.get('date_selector', 'time, .published, .date')
        ref_sel = self.config.get('reference_selector', '.ref, .reference')

        title_elem = item.select_one(title_sel)
        title = self._clean_text(title_elem.get_text()) if title_elem else text[:250]

        link_elem = item.select_one(link_sel)
        detail_url = None
        if link_elem and link_elem.get('href'):
            base = self.config.get('url', self.source.url)
            detail_url = urljoin(base, link_elem['href'])

        desc_elem = item.select_one(desc_sel)
        description = self._clean_text(desc_elem.get_text()) if desc_elem else text

        deadline_elem = item.select_one(deadline_sel)
        deadline = self._parse_date(deadline_elem.get_text()) if deadline_elem else None
        if not deadline:
            # Try regex from full text
            dl_patterns = [
                r'(?:deadline|closing|prazo|due)\s*[:\-]?\s*(\d{1,2}[\s\/\-][A-Za-z]+[\s\/\-]\d{4})',
                r'(\d{1,2}\s+[A-Za-z]+\s+\d{4})',
            ]
            for pat in dl_patterns:
                m = re.search(pat, text, re.I)
                if m:
                    deadline = self._parse_date(m.group(1))
                    break

        date_elem = item.select_one(date_sel)
        published = self._parse_date(date_elem.get('datetime') or date_elem.get_text()) if date_elem else None

        ref_elem = item.select_one(ref_sel)
        ref = ref_elem.get_text(strip=True) if ref_elem else None

        # Geographic inference from text
        text_lower = text.lower()
        countries = []
        if any(k in text_lower for k in ['cabo verde', 'cape verde']):
            countries.append('CPV')

        return {
            'external_id': ref or self._make_external_id(self.source.name, title),
            'external_url': detail_url or self.source.url,
            'title': title,
            'organization': self.config.get('organization', self.source.organization),
            'client': self.config.get('client', self.source.organization),
            'sector': self.config.get('sector', ''),
            'country': self.config.get('country', ''),
            'region': self.config.get('region', ''),
            'description': description,
            'deadline': deadline.isoformat() if deadline else None,
            'published_at': published.isoformat() if published else timezone.now().isoformat(),
            'language': self.config.get('language', 'en'),
            'sector_tags': [],
            'geographic_scope': {'countries': countries, 'region': self.config.get('region', '')},
            'source_metadata': {
                'scraped_from': self.source.url,
                'scraper_class': 'GenericPortalScraper',
            },
        }
