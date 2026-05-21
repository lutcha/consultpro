"""
Scraper for LuxDev (Agence Luxembourgeoise pour la Coopération au Développement).
Two listing pages:
  - Call for Tenders:    https://luxdev.lu/en/tenders/call-tenders
  - Calls for Proposals: https://luxdev.lu/en/tenders/calls-proposals
"""
import logging
import re
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from django.utils import timezone

from .base import BaseScraper
from apps.scraping.services.quality import assess_scraped_item

logger = logging.getLogger(__name__)


class LuxDevScraper(BaseScraper):
    """Scraper for LuxDev tender and proposal listings."""

    BASE_URL = "https://luxdev.lu"
    DEFAULT_URLS = [
        "https://luxdev.lu/en/tenders/call-tenders",
        "https://luxdev.lu/en/tenders/calls-proposals",
    ]

    # Ordered from most-specific to most-generic; first match wins
    ITEM_SELECTORS = [
        'article.tender-item',
        'div.tender-item',
        'div.views-row',
        'article',
        'li.tender',
        'table tbody tr',
    ]

    TITLE_SELECTORS = ['h2 a', 'h3 a', 'h4 a', '.field--name-title a', 'a.tender-link', 'a']
    DEADLINE_SELECTORS = [
        '.field--name-field-deadline',
        '.deadline',
        '.date-display-single',
        '.closing-date',
        'time',
    ]
    DATE_SELECTORS = ['time[datetime]', '.field--name-created', '.date']
    COUNTRY_SELECTORS = ['.field--name-field-country', '.country', '.location']
    CATEGORY_SELECTORS = ['.field--name-field-category', '.category', '.type']

    def fetch(self, url: Optional[str] = None, **kwargs) -> str:
        target = url or self.config.get('url', self.DEFAULT_URLS[0])
        if not self._check_robots_txt(target):
            raise PermissionError(f"robots.txt disallows: {target}")
        resp = self._http_get(target)
        return resp.text

    def execute(self) -> Dict[str, Any]:
        """Override to scrape both listing pages."""
        urls = self.config.get('urls', self.DEFAULT_URLS)
        all_items: List[Dict[str, Any]] = []
        errors = []

        for url in urls:
            try:
                logger.info(f"LuxDev: fetching {url}")
                raw_data = self.fetch(url=url)
                items = self.parse(raw_data, base_url=url)
                all_items.extend(items)
                logger.info(f"LuxDev: {len(items)} items from {url}")
            except Exception as e:
                logger.error(f"LuxDev: error fetching {url}: {e}", exc_info=True)
                errors.append(str(e))

        if not all_items and errors:
            return {'status': 'error', 'items': [], 'error': '; '.join(errors)}

        return {'status': 'success', 'items': all_items, 'error': None}

    def parse(self, raw_data: str, base_url: str = BASE_URL) -> List[Dict[str, Any]]:
        opportunities = []
        soup = BeautifulSoup(raw_data, 'html.parser')

        item_selectors = self.config.get('item_selectors', self.ITEM_SELECTORS)
        items = []
        for sel in item_selectors:
            items = soup.select(sel)
            if items:
                logger.info(f"LuxDev: selector '{sel}' matched {len(items)} items")
                break

        if not items:
            # Last-resort: any element containing deadline-like text
            items = [
                el for el in soup.find_all(['div', 'li', 'article', 'tr'])
                if el.get_text() and any(
                    k in el.get_text().lower()
                    for k in ['deadline', 'closing', 'tender', 'proposal', '202']
                )
            ]
            logger.info(f"LuxDev: fallback found {len(items)} elements")

        seen_ids: set = set()
        for el in items:
            try:
                opp = self._parse_item(el, base_url)
                if opp and opp.get('title') and opp['external_id'] not in seen_ids:
                    seen_ids.add(opp['external_id'])
                    opportunities.append(self._standardize_item(opp, self.source))
            except Exception as e:
                logger.warning(f"LuxDev: error parsing item: {e}")

        return opportunities

    def _parse_item(self, el, base_url: str) -> Optional[Dict[str, Any]]:
        text = el.get_text(separator=' ', strip=True)
        if len(text) < 15:
            return None

        # Title + URL
        title_elem = None
        for sel in self.TITLE_SELECTORS:
            title_elem = el.select_one(sel)
            if title_elem:
                break

        title = self._clean_text(title_elem.get_text()) if title_elem else None
        if not title:
            title = text.split('\n')[0].strip()[:300]

        detail_url = None
        if title_elem and title_elem.name == 'a' and title_elem.get('href'):
            detail_url = urljoin(base_url, title_elem['href'])
        else:
            link = el.select_one('a[href]')
            if link and link.get('href'):
                detail_url = urljoin(base_url, link['href'])

        assessment = assess_scraped_item({'title': title, 'external_url': detail_url or base_url}, 'LuxDev')
        if not assessment.valid:
            return None
        title = assessment.title

        # Deadline
        deadline = None
        deadline_text = None
        for sel in self.DEADLINE_SELECTORS:
            dl_el = el.select_one(sel)
            if dl_el:
                raw = dl_el.get('datetime') or dl_el.get_text(strip=True)
                if raw:
                    deadline = self._parse_date(raw)
                    deadline_text = raw
                    break

        if not deadline:
            # Regex fallback: "Deadline: 15 January 2026" or "15/01/2026"
            dl_patterns = [
                r'(?:deadline|closing|due)\s*[:\-]?\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})',
                r'(?:deadline|closing|due|date limite|limite)\s*[:\-]?\s*(\d{1,2}[\/\.\-]\d{1,2}[\/\.\-]\d{4})',
                r'(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})',
                r'(\d{1,2}[\/\.\-]\d{1,2}[\/\.\-]\d{4})',
            ]
            for pat in dl_patterns:
                m = re.search(pat, text, re.I)
                if m:
                    deadline_text = m.group(1)
                    deadline = self._parse_date(deadline_text)
                    break

        # Published date
        published = None
        for sel in self.DATE_SELECTORS:
            date_el = el.select_one(sel)
            if date_el:
                raw = date_el.get('datetime') or date_el.get_text(strip=True)
                published = self._parse_date(raw)
                if published:
                    break

        # Country / region from text
        text_lower = text.lower()
        countries = []
        cv_keywords = ['cabo verde', 'cape verde', 'cap-vert']
        if any(k in text_lower for k in cv_keywords):
            countries.append('CPV')
        if any(k in text_lower for k in ['africa', 'afrique', 'african']):
            countries.append('Africa')
        if any(k in text_lower for k in ['lusophone', 'palop', 'cplp']):
            countries.append('PALOP')

        # Sector inference
        sectors = []
        sector_map = {
            'energias_renovaveis': ['energy', 'renewable', 'solar', 'wind', 'énergie'],
            'saude_publica': ['health', 'santé', 'médical', 'hospital'],
            'educacao': ['education', 'school', 'formation', 'éducation'],
            'agricultura': ['agriculture', 'rural', 'farming', 'food security'],
            'infraestrutura': ['infrastructure', 'road', 'water', 'sanitation'],
            'governanca': ['governance', 'reform', 'public sector', 'institution'],
        }
        for sector, keywords in sector_map.items():
            if any(k in text_lower for k in keywords):
                sectors.append(sector)

        # Determine if this is a tender or proposal call from URL/text
        source_type_hint = 'Tender'
        if 'proposal' in text_lower or 'proposal' in (detail_url or '').lower():
            source_type_hint = 'Call for Proposals'

        # Stable ID: prefer URL slug, fall back to title hash
        external_id = None
        if detail_url:
            slug = detail_url.rstrip('/').split('/')[-1]
            if slug and len(slug) > 3:
                external_id = self._make_external_id('LuxDev', slug)
        if not external_id:
            external_id = self._make_external_id('LuxDev', title)

        return {
            'external_id': external_id,
            'external_url': detail_url or base_url,
            'title': title,
            'organization': 'LuxDev',
            'client': 'Agence Luxembourgeoise pour la Coopération au Développement',
            'sector': sectors[0] if sectors else 'Cooperação ao Desenvolvimento',
            'country': ', '.join(countries) if countries else 'International',
            'region': 'África / ACP',
            'description': text,
            'deadline': deadline.isoformat() if deadline else None,
            'published_at': published.isoformat() if published else timezone.now().isoformat(),
            'language': 'en',
            'sector_tags': sectors,
            'geographic_scope': {
                'countries': countries or ['International'],
                'region': 'ACP / West Africa',
            },
            'source_metadata': {
                'scraped_from': 'luxdev.lu',
                'type': source_type_hint,
                'deadline_text': deadline_text,
            },
        }
