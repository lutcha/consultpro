"""
Scraper for UGPE - Unidade de Gestão de Projetos Especiais (Cabo Verde).
URL: https://ugpe.gov.cv/concursos
"""
import logging
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from django.utils import timezone

from .base import BaseScraper

logger = logging.getLogger(__name__)


class UGPEScraper(BaseScraper):
    """Scraper for ugpe.gov.cv/concursos"""

    BASE_URL = "https://ugpe.gov.cv/concursos"

    def fetch(self, url: Optional[str] = None, **kwargs) -> str:
        target = url or self.config.get('url', self.BASE_URL)
        if not self._check_robots_txt(target):
            raise PermissionError(f"robots.txt disallows: {target}")
        resp = self._http_get(target)
        return resp.text

    def parse(self, raw_data: str) -> List[Dict[str, Any]]:
        opportunities = []
        soup = BeautifulSoup(raw_data, 'html.parser')

        # Try multiple known selectors (UGPE may use tables or cards)
        selectors = self.config.get('item_selectors', [
            'table.concursos-table tbody tr',
            'div.concurso-item',
            'div.opportunity-item',
            'article.concurso',
        ])

        rows = []
        for sel in selectors:
            rows = soup.select(sel)
            if rows:
                logger.info(f"UGPE: matched selector '{sel}' with {len(rows)} rows")
                break

        if not rows:
            # Fallback: look for any table rows that contain deadline-like text
            all_rows = soup.find_all('tr')
            rows = [r for r in all_rows if r.get_text() and any(k in r.get_text().lower() for k in ['prazo', 'deadline', '202', 'consultor'])]
            logger.info(f"UGPE: fallback found {len(rows)} rows")

        for row in rows:
            try:
                opp = self._parse_row(row)
                if opp and opp.get('title'):
                    opportunities.append(self._standardize_item(opp, self.source))
            except Exception as e:
                logger.warning(f"UGPE: error parsing row: {e}")
                continue

        return opportunities

    def _parse_row(self, element) -> Optional[Dict[str, Any]]:
        """Parse a single UGPE row/card into raw data."""
        text = element.get_text(separator=' ', strip=True)
        if len(text) < 20:
            return None

        # Try structured selectors first
        title_elem = (
            element.select_one('h3, h4, .titulo, .title, td:nth-child(2)')
            or element.find(['h3', 'h4', 'a'])
        )
        deadline_elem = element.select_one('.prazo, .deadline, td:nth-child(3), .data-limite')
        ref_elem = element.select_one('.ref, .reference, td:nth-child(1)')
        link_elem = element.select_one('a[href]')

        title = self._clean_text(title_elem.get_text()) if title_elem else None
        if not title:
            # Fallback: use first sentence of text
            title = text.split('.')[0][:200]

        deadline_text = deadline_elem.get_text(strip=True) if deadline_elem else None
        if not deadline_text:
            # Try regex extraction from full text
            import re
            dm = re.search(r'(\d{1,2})[\s\/\-]([A-Za-zçáéíóú]+|\d{1,2})[\s\/\-](20\d{2})', text)
            if dm:
                deadline_text = f"{dm.group(1)}/{dm.group(2)}/{dm.group(3)}"

        ref = ref_elem.get_text(strip=True) if ref_elem else None
        detail_url = None
        if link_elem and link_elem.get('href'):
            detail_url = urljoin(self.BASE_URL, link_elem['href'])

        deadline = self._parse_date(deadline_text) if deadline_text else None

        # Sector/category inference from text
        sectors = []
        sector_keywords = {
            'digital': ['digital', 'tic', 'tecnologia', 'govtech', 'sistema de informação'],
            'saúde': ['saúde', 'saude', 'health', 'hospital'],
            'turismo': ['turismo', 'tourism', 'hotel'],
            'pescas': ['pesca', 'fisheries', 'mar'],
            'energia': ['energia', 'renewable', 'solar', 'eólica'],
            'educação': ['educação', 'escola', 'universidade'],
            'infraestrutura': ['infraestrutura', 'roads', 'port', 'aeroporto'],
        }
        text_lower = text.lower()
        for sector, keywords in sector_keywords.items():
            if any(kw in text_lower for kw in keywords):
                sectors.append(sector)

        return {
            'external_id': ref or self._make_external_id(self.source.name, title),
            'external_url': detail_url or self.BASE_URL,
            'title': title,
            'organization': 'UGPE - Cabo Verde',
            'client': 'UGPE / Governo de Cabo Verde',
            'sector': sectors[0] if sectors else 'Consultoria',
            'country': 'Cabo Verde',
            'region': 'África Ocidental',
            'description': text,
            'deadline': deadline.isoformat() if deadline else None,
            'published_at': timezone.now().isoformat(),
            'language': 'pt',
            'sector_tags': sectors,
            'geographic_scope': {'countries': ['CPV'], 'region': 'West Africa'},
            'source_metadata': {
                'scraped_from': 'ugpe.gov.cv',
                'reference': ref,
            },
        }
