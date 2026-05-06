"""
Scraper for ECREEE - ECOWAS Centre for Renewable Energy and Energy Efficiency.
URL: https://www.ecreee.org/category/procurement-notices/
"""
import logging
import re
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from django.utils import timezone

from .base import BaseScraper

logger = logging.getLogger(__name__)


class ECREEEScraper(BaseScraper):
    """Scraper for ecreee.org procurement notices."""

    BASE_URL = "https://www.ecreee.org/category/procurement-notices/"

    def fetch(self, url: Optional[str] = None, **kwargs) -> str:
        target = url or self.config.get('url', self.BASE_URL)
        if not self._check_robots_txt(target):
            raise PermissionError(f"robots.txt disallows: {target}")
        resp = self._http_get(target)
        return resp.text

    def parse(self, raw_data: str) -> List[Dict[str, Any]]:
        opportunities = []
        soup = BeautifulSoup(raw_data, 'html.parser')

        # WordPress typical structure
        selectors = self.config.get('item_selectors', [
            'article.post',
            'div.post',
            'article.type-post',
            '.procurement-notice',
        ])

        posts = []
        for sel in selectors:
            posts = soup.select(sel)
            if posts:
                logger.info(f"ECREEE: matched selector '{sel}' with {len(posts)} posts")
                break

        for post in posts:
            try:
                opp = self._parse_post(post)
                if opp and opp.get('title'):
                    opportunities.append(self._standardize_item(opp, self.source))
            except Exception as e:
                logger.warning(f"ECREEE: error parsing post: {e}")
                continue

        return opportunities

    def _parse_post(self, post) -> Optional[Dict[str, Any]]:
        title_elem = post.select_one('h2 a, h3 a, .entry-title a, a[rel="bookmark"]')
        summary_elem = post.select_one('.entry-summary, .post-excerpt, p')
        date_elem = post.select_one('time, .published, .entry-date')

        title = self._clean_text(title_elem.get_text()) if title_elem else None
        detail_url = None
        if title_elem and title_elem.get('href'):
            detail_url = urljoin(self.BASE_URL, title_elem['href'])

        if not title:
            return None

        description = self._clean_text(summary_elem.get_text()) if summary_elem else title
        text_combined = f"{title} {description}".lower()

        # Extract deadline from text
        deadline = None
        deadline_text = None
        # Patterns like "Deadline: 15 May 2025" or "Closing date: 30/04/2025"
        dl_patterns = [
            r'(?:deadline|closing date|date limite|prazo)\s*[:\-]?\s*(\d{1,2}[\s\/\-][A-Za-z]+[\s\/\-]\d{4})',
            r'(?:deadline|closing date|date limite|prazo)\s*[:\-]?\s*(\d{1,2}[\s\/\-]\d{1,2}[\s\/\-]\d{4})',
        ]
        for pat in dl_patterns:
            m = re.search(pat, text_combined, re.I)
            if m:
                deadline_text = m.group(1)
                deadline = self._parse_date(deadline_text)
                break

        published = self._parse_date(date_elem.get('datetime') or date_elem.get_text()) if date_elem else None

        # Geographic inference
        countries = []
        if any(k in text_combined for k in ['cabo verde', 'cape verde', 'cap-verde']):
            countries.append('CPV')
        if any(k in text_combined for k in ['ghana', 'accra']):
            countries.append('GHA')
        if any(k in text_combined for k in ['senegal', 'dakar']):
            countries.append('SEN')
        if any(k in text_combined for k in ['nigeria', 'lagos', 'abuja']):
            countries.append('NGA')
        if not countries:
            countries = ['ECOWAS Region']

        sectors = []
        if any(k in text_combined for k in ['energy', 'renewable', 'solar', 'eólica', 'wind']):
            sectors.append('energias_renovaveis')
        if any(k in text_combined for k in ['water', 'água', 'wASH', 'nexus']):
            sectors.append('gestao_agua')
        if any(k in text_combined for k in ['gender', 'women', 'mulher', 'género']):
            sectors.append('igualdade_genero')

        return {
            'external_id': self._make_external_id(self.source.name, title),
            'external_url': detail_url or self.BASE_URL,
            'title': title,
            'organization': 'ECREEE',
            'client': 'ECREEE / CEDEAO',
            'sector': sectors[0] if sectors else 'Energia',
            'country': 'Regional (CEDEAO)',
            'region': 'West Africa',
            'description': description,
            'deadline': deadline.isoformat() if deadline else None,
            'published_at': published.isoformat() if published else timezone.now().isoformat(),
            'language': 'en',
            'sector_tags': sectors,
            'geographic_scope': {'countries': countries, 'region': 'West Africa'},
            'source_metadata': {
                'scraped_from': 'ecreee.org',
                'deadline_text': deadline_text,
            },
        }
