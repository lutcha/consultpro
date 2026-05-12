"""
Scraper for UK FCDO procurement notices via the Find a Tender Service (FTS) public OCDS API.

API docs: https://www.find-tender.service.gov.uk/api/1.0/swagger-ui/
No authentication required for read access.
"""
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

from .base import BaseScraper

logger = logging.getLogger(__name__)

FTS_API_BASE = "https://www.find-tender.service.gov.uk/api/1.0/ocds"


class FCDOScraper(BaseScraper):
    """
    Scraper for FCDO / UK Aid procurement via the Find a Tender Service OCDS API.

    Config keys:
        api_base        Override the FTS base URL.
        buyer_id        OCDS buyer identifier (default: GB-GOV-13 = FCDO).
        days_back       How many days back to search (default: 90).
        max_items       Maximum notices to fetch (default: 200).
        include_services_only  If True, filter mainProcurementCategory=services (default: True).
    """

    DEFAULT_BUYER_ID = "GB-GOV-13"
    DEFAULT_DAYS_BACK = 90
    DEFAULT_MAX_ITEMS = 200

    def fetch(self, url: Optional[str] = None, **kwargs) -> str:
        api_base = self.config.get("api_base", FTS_API_BASE)
        buyer_id = self.config.get("buyer_id", self.DEFAULT_BUYER_ID)
        days_back = int(self.config.get("days_back", self.DEFAULT_DAYS_BACK))
        max_items = int(self.config.get("max_items", self.DEFAULT_MAX_ITEMS))

        published_from = (
            datetime.now(tz=timezone.utc) - timedelta(days=days_back)
        ).strftime("%Y-%m-%d")

        releases: List[Dict[str, Any]] = []
        cursor: Optional[str] = None

        while len(releases) < max_items:
            params: Dict[str, Any] = {
                "publishedFrom": published_from,
                "limit": min(100, max_items - len(releases)),
            }
            if buyer_id:
                params["buyer.identifier.id"] = buyer_id
            if cursor:
                params["cursor"] = cursor

            endpoint = f"{api_base}/opportunities?{urlencode(params)}"
            resp = self._http_get(endpoint)
            payload = resp.json()

            page_releases = payload.get("releases") or []
            releases.extend(page_releases[: max_items - len(releases)])

            next_link = (payload.get("links") or {}).get("next")
            if not next_link or not page_releases:
                break
            # Extract cursor from next link
            cursor = _extract_cursor(next_link)
            if not cursor:
                break

        return json.dumps({"releases": releases})

    def parse(self, raw_data: str) -> List[Dict[str, Any]]:
        try:
            payload = json.loads(raw_data)
            releases = payload.get("releases") or []
        except (TypeError, json.JSONDecodeError) as exc:
            logger.warning("FCDO: could not decode fetch payload: %s", exc)
            return []

        opportunities: List[Dict[str, Any]] = []
        seen_ids: set = set()

        for release in releases:
            try:
                opp = self._parse_release(release)
                if opp and opp["external_id"] not in seen_ids:
                    seen_ids.add(opp["external_id"])
                    opportunities.append(self._standardize_item(opp, self.source))
            except Exception as exc:
                logger.warning("FCDO: error parsing release: %s", exc)

        return opportunities

    def _parse_release(self, release: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        tender = release.get("tender") or {}
        ocid = release.get("ocid") or tender.get("id") or ""
        title = self._clean_text(tender.get("title"))
        if not ocid or not title:
            return None

        status = (tender.get("status") or "").lower()
        if status not in ("active", "planned", ""):
            return None

        description = self._clean_text(tender.get("description")) or title
        procuring_entity = tender.get("procuringEntity") or {}
        buyer_name = self._clean_text(procuring_entity.get("name")) or "FCDO"

        tender_period = tender.get("tenderPeriod") or {}
        deadline = self._parse_date(tender_period.get("endDate"))
        published_at = self._parse_date(release.get("date"))

        value_obj = tender.get("value") or {}
        amount = value_obj.get("amount")
        currency = (value_obj.get("currency") or "GBP").upper()

        category = self._clean_text(tender.get("mainProcurementCategory")) or "services"
        cpv_codes = [
            c.get("description") or c.get("id")
            for c in (tender.get("classification") or [])
            if c.get("description") or c.get("id")
        ]

        # Build external URL — FTS notice page
        notice_id = tender.get("id") or ocid
        external_url = (
            f"https://www.find-tender.service.gov.uk/Notice/{notice_id}"
        )

        return {
            "external_id": self._make_external_id("FCDO", ocid),
            "external_url": external_url,
            "title": title,
            "organization": buyer_name,
            "client": "UK FCDO / UK Aid",
            "sector": category,
            "country": "International",
            "region": "Global",
            "description": description[:2000],
            "value": float(amount) if amount is not None else None,
            "currency": currency,
            "deadline": deadline.isoformat() if deadline else None,
            "published_at": published_at.isoformat() if published_at else None,
            "language": "en",
            "sector_tags": cpv_codes[:5],
            "geographic_scope": {"countries": ["International"], "region": "Global"},
            "source_metadata": {
                "ocid": ocid,
                "status": status,
                "category": category,
                "scraped_from": "find-tender.service.gov.uk",
            },
        }


def _extract_cursor(next_link: str) -> Optional[str]:
    """Pull the cursor value out of a FTS pagination link."""
    try:
        from urllib.parse import urlparse, parse_qs
        qs = parse_qs(urlparse(next_link).query)
        values = qs.get("cursor") or qs.get("_cursor")
        return values[0] if values else None
    except Exception:
        return None
