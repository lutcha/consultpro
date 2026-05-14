"""
Scraper for the EU Funding & Tenders opportunities portal.
"""
import json
import logging
from typing import Any, Dict, List, Optional

from django.utils import timezone

from .base import BaseScraper

logger = logging.getLogger(__name__)


class EUFundingScraper(BaseScraper):
    """Scraper for EU calls for proposals using the JSON portal response."""

    DEFAULT_URL = (
        "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/"
        "opportunities/calls-for-proposals;type=1;status=31,8"
    )

    def fetch(self, url: Optional[str] = None, **kwargs) -> str:
        target = url or self.config.get('url', self.DEFAULT_URL)
        response = self._http_get(
            target,
            headers={
                'Accept': 'application/json',
            },
        )
        return response.text

    def parse(self, raw_data: str) -> List[Dict[str, Any]]:
        try:
            payload = json.loads(raw_data or '')
        except (TypeError, ValueError):
            logger.warning("EU Funding: non-JSON response received; skipping")
            return []

        records = self._extract_records(payload)
        opportunities = []
        seen_ids = set()
        for record in records:
            try:
                item = self._parse_record(record)
                if item and item['external_id'] not in seen_ids:
                    seen_ids.add(item['external_id'])
                    standardized = self._standardize_item(item, self.source)
                    standardized['raw_payload'] = record
                    opportunities.append(standardized)
            except Exception as exc:
                logger.warning("EU Funding: error parsing record: %s", exc)
        return opportunities

    def _extract_records(self, payload: Any) -> List[Dict[str, Any]]:
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if not isinstance(payload, dict):
            return []

        for key in ('data', 'results', 'items', 'opportunities', 'calls'):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
            if isinstance(value, dict):
                nested = self._extract_records(value)
                if nested:
                    return nested

        if payload.get('identifier') or payload.get('title'):
            return [payload]
        return []

    def _parse_record(self, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        identifier = str(record.get('identifier') or record.get('callIdentifier') or '').strip()
        title = self._clean_text(record.get('title') or record.get('callTitle') or '')
        if not identifier and not title:
            return None

        deadline_text = record.get('deadlineDate') or record.get('deadline') or ''
        deadline = self._parse_date(deadline_text) if deadline_text else None
        description = self._budget_topic_description(record.get('budgetTopicActions'))
        sector_tags = self._as_list(record.get('programmePeriod'))
        funding_regions = self._as_list(record.get('fundingRegions'))
        cv_eligible = any(
            str(region).strip().lower() in ('cv', 'west africa')
            for region in funding_regions
        )

        external_id = self._make_external_id('EUFunding', identifier or title)
        external_url = record.get('url') or self.DEFAULT_URL

        return {
            'external_id': external_id,
            'external_url': external_url,
            'title': title or identifier,
            'organization': 'European Commission',
            'client': 'European Commission',
            'sector': ', '.join(sector_tags) if sector_tags else 'EU Funding',
            'country': ', '.join(funding_regions),
            'region': 'West Africa' if cv_eligible else '',
            'description': description,
            'deadline': deadline.isoformat() if deadline else None,
            'published_at': timezone.now().isoformat(),
            'language': 'en',
            'sector_tags': sector_tags,
            'geographic_scope': {
                'countries': funding_regions,
                'region': 'West Africa' if cv_eligible else '',
                'cv_eligible': cv_eligible,
            },
            'source_metadata': {
                'scraped_from': 'ec.europa.eu',
                'identifier': identifier,
                'programmePeriod': record.get('programmePeriod'),
                'budgetTopicActions': record.get('budgetTopicActions'),
            },
        }

    def _budget_topic_description(self, value: Any) -> str:
        parts = []
        for item in self._as_list(value):
            if isinstance(item, dict):
                text = item.get('description') or item.get('title') or item.get('name') or item.get('code')
                if text:
                    parts.append(self._clean_text(str(text)))
            elif item:
                parts.append(self._clean_text(str(item)))
        return ' '.join(part for part in parts if part)

    def _as_list(self, value: Any) -> List[Any]:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, tuple):
            return list(value)
        if isinstance(value, dict):
            return list(value.values())
        return [value]
