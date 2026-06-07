"""
API scraper for World Bank active procurement notices.
"""
import json
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

from .base import BaseScraper

logger = logging.getLogger(__name__)


class WorldBankScraper(BaseScraper):
    """Scraper for the World Bank public procurement search API."""

    API_URL = "https://search.worldbank.org/api/v2/procnotices"
    DETAIL_URL = "https://projects.worldbank.org/procurement/noticedetail/{notice_id}"
    DEFAULT_FIELDS = (
        "id,title,submission_deadline_date,pdate,project_ctry_name,regionname,"
        "project_name,url,borrower,sector,notice_type,notice_text,"
        "procurement_group_desc,procurement_method_name"
    )

    def fetch(self, url: Optional[str] = None, **kwargs) -> str:
        api_url = url or self.config.get('api_url', self.API_URL)
        if not self._check_robots_txt(api_url):
            raise PermissionError(f"robots.txt disallows: {api_url}")

        page_size = int(self.config.get('page_size', 50))
        max_items = int(self.config.get('max_items', 200))
        docs: List[Dict[str, Any]] = []
        num_found = None
        start = 0

        while len(docs) < max_items:
            params = {
                'format': 'json',
                'fl': self.config.get('fields', self.DEFAULT_FIELDS),
                'rows': page_size,
                'os': start,
                'srce': self.config.get('srce', 'both'),
                'srt': self.config.get('sort_field', 'submission_deadline_date'),
                'order': self.config.get('order', 'desc'),
                'apilang': self.config.get('apilang', 'en'),
            }
            params.update(self.config.get('query_params') or {})
            filter_query = self.config.get('filter_query')
            if filter_query:
                params['fq'] = filter_query
            resp = self._http_get(api_url, params=params)
            payload = resp.json()
            page_docs = self._extract_docs(payload)

            if num_found is None:
                num_found = self._extract_total(payload)

            if not page_docs:
                break

            remaining = max_items - len(docs)
            docs.extend(page_docs[:remaining])

            start += page_size
            if len(docs) >= num_found or len(page_docs) < page_size:
                break

        return json.dumps({'response': {'numFound': num_found or len(docs), 'docs': docs}})

    def parse(self, raw_data: str) -> List[Dict[str, Any]]:
        opportunities: List[Dict[str, Any]] = []
        try:
            payload = json.loads(raw_data)
            docs = self._extract_docs(payload)
        except (TypeError, json.JSONDecodeError) as exc:
            logger.warning(f"WorldBank: could not parse API response: {exc}")
            return []

        seen_ids = set()
        for doc in docs:
            try:
                opp = self._parse_doc(doc)
                if opp and opp['external_id'] not in seen_ids:
                    seen_ids.add(opp['external_id'])
                    opportunities.append(self._standardize_item(opp, self.source))
            except Exception as exc:
                logger.warning(f"WorldBank: error parsing notice: {exc}")

        return opportunities

    def _parse_doc(self, doc: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        notice_id = self._clean_text(str(doc.get('id') or ''))
        title = self._clean_text(
            doc.get('title') or doc.get('assignment_title') or
            doc.get('project_name') or doc.get('notice_type')
        )
        if not notice_id or not title:
            return None

        country = self._clean_text(
            doc.get('project_ctry_name') or doc.get('countryname') or doc.get('country')
        )
        region = self._clean_text(doc.get('regionname') or doc.get('region'))
        sector = self._clean_text(
            doc.get('sector') or doc.get('sectorname') or
            doc.get('procurement_group_desc') or doc.get('procurement_method_name')
        )
        deadline = self._parse_date(
            doc.get('submission_deadline_date') or doc.get('deadline') or doc.get('closing_date')
        )
        published_at = self._parse_date(doc.get('pdate') or doc.get('publishdate'))
        external_url = self._build_notice_url(doc, notice_id)
        description = self._clean_text(
            doc.get('notice_text') or doc.get('project_name') or doc.get('projectname') or
            doc.get('description') or title
        )
        notice_type = doc.get('notice_type') or doc.get('docty')

        return {
            'external_id': self._make_external_id('WorldBank', notice_id),
            'external_url': external_url,
            'title': title,
            'organization': 'World Bank Group',
            'client': self._clean_text(doc.get('borrower')) or 'World Bank',
            'sector': sector,
            'country': country,
            'region': region,
            'description': description,
            'value': None,
            'currency': 'USD',
            'deadline': deadline.isoformat() if deadline else None,
            'published_at': published_at.isoformat() if published_at else None,
            'language': 'en',
            'sector_tags': [sector] if sector else [],
            'geographic_scope': {
                'countries': [country] if country else [],
                'region': region,
            },
            'source_metadata': {
                'api_id': notice_id,
                'document_type': notice_type,
                'procurement_method': doc.get('procurement_method_name'),
                'scraped_from': 'search.worldbank.org',
            },
        }

    def _build_notice_url(self, doc: Dict[str, Any], notice_id: str) -> str:
        raw_url = self._clean_text(doc.get('url') or doc.get('notice_url'))
        if raw_url:
            return urljoin("https://projects.worldbank.org", raw_url)
        return self.DETAIL_URL.format(notice_id=notice_id)

    @staticmethod
    def _extract_docs(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not isinstance(payload, dict):
            return []
        procnotices = payload.get('procnotices')
        if isinstance(procnotices, list):
            return procnotices
        response_docs = (payload.get('response') or {}).get('docs')
        if isinstance(response_docs, list):
            return response_docs
        docs = payload.get('docs')
        return docs if isinstance(docs, list) else []

    @staticmethod
    def _extract_total(payload: Dict[str, Any]) -> int:
        total = payload.get('total')
        if total is None:
            total = (payload.get('response') or {}).get('numFound')
        try:
            return int(total)
        except (TypeError, ValueError):
            return 0
