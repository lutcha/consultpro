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

        deadline, deadline_text = self._extract_deadline(text_combined)
        deadline_source = 'listing' if deadline else None

        if not deadline and detail_url:
            detail_deadline, detail_deadline_text = self._fetch_detail_deadline(detail_url)
            if detail_deadline:
                deadline = detail_deadline
                deadline_text = detail_deadline_text
                deadline_source = 'detail'

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
                'deadline_source': deadline_source,
            },
        }

    def _fetch_detail_deadline(self, detail_url: str) -> tuple:
        try:
            resp = self._http_get(detail_url, retries=0)
        except Exception as exc:
            logger.info("ECREEE: detail fetch failed for %s: %s", detail_url, exc)
            return None, None

        soup = BeautifulSoup(resp.text, 'html.parser')
        detail_text = soup.get_text(separator=' ', strip=True)
        return self._extract_deadline(detail_text)

    def _extract_deadline(self, text: str) -> tuple:
        if not text:
            return None, None

        # ECREEE posts usually phrase closing dates as deadline/submission
        # labels followed by a human date; keep regex broad but label-bound.
        weekday = r'(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+'
        named_date = rf'(?:{weekday})?\d{{1,2}}(?:st|nd|rd|th)?(?:\s+of)?[\s,\/\-]+[A-Za-z]+[\s,\/\-]+\d{{4}}'
        dl_patterns = [
            rf'(?:deadline for submission is no later than)\s*({named_date})',
            rf'(?:deadline|closing date|submission deadline|date limite|prazo)\s*[:\-]?\s*({named_date})',
            r'(?:deadline|closing date|submission deadline|date limite|prazo)\s*[:\-]?\s*(\d{1,2}[\s\/\-]\d{1,2}[\s\/\-]\d{4})',
            rf'\b({named_date})\b',
        ]
        for pat in dl_patterns:
            match = re.search(pat, text, re.I)
            if match:
                deadline_text = match.group(1)
                return self._parse_date(deadline_text), deadline_text

        return None, None
