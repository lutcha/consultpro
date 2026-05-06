"""
Base scraper with common utilities for fetching, parsing, and normalizing data.
"""
import logging
import re
import time
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
from django.utils import timezone

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 '
        'ConsultProBot/1.0 (+https://consultpro.cv/bot)'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'pt-PT,pt;q=0.9,en;q=0.8',
}


class BaseScraper:
    """Base class for all web scrapers."""

    def __init__(self, source):
        self.source = source
        self.config = source.scraper_config or {}
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)

    def fetch(self, url: Optional[str] = None, **kwargs) -> str:
        """Fetch the raw data (HTML, JSON, etc.) from the source."""
        raise NotImplementedError("Subclasses must implement fetch()")

    def parse(self, raw_data: str) -> List[Dict[str, Any]]:
        """Parse the raw data into a list of standardized dictionaries."""
        raise NotImplementedError("Subclasses must implement parse()")

    def execute(self) -> Dict[str, Any]:
        """Execute the full scraping pipeline: fetch -> parse -> return data."""
        try:
            logger.info(f"Starting scrape for {self.source.name}")
            raw_data = self.fetch()
            items = self.parse(raw_data)
            logger.info(f"Successfully scraped {len(items)} items from {self.source.name}")
            return {
                'status': 'success',
                'items': items,
                'error': None,
            }
        except Exception as e:
            logger.error(f"Error scraping {self.source.name}: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'items': [],
                'error': str(e),
            }

    # === Utility methods ===

    def _http_get(self, url: str, retries: int = 2, backoff: float = 1.5, **kwargs) -> requests.Response:
        """HTTP GET with retry logic and rate limiting."""
        for attempt in range(retries + 1):
            try:
                resp = self.session.get(url, timeout=30, **kwargs)
                resp.raise_for_status()
                return resp
            except requests.RequestException as exc:
                if attempt == retries:
                    raise exc
                sleep_time = backoff * (attempt + 1)
                logger.warning(f"Request failed (attempt {attempt + 1}), retrying in {sleep_time}s: {exc}")
                time.sleep(sleep_time)

    def _check_robots_txt(self, url: str) -> bool:
        """Check if scraping is allowed by robots.txt."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            can_fetch = rp.can_fetch("*", url)
            if not can_fetch:
                logger.warning(f"robots.txt disallows fetching {url}")
            return can_fetch
        except Exception as e:
            logger.warning(f"Could not parse robots.txt for {url}: {e}")
            return True  # Conservative: assume allowed if we can't parse

    @staticmethod
    def _parse_date(date_str: str, fallback: Optional[datetime] = None) -> Optional[datetime]:
        """Safely parse a date string."""
        if not date_str:
            return fallback
        try:
            parsed = date_parser.parse(date_str, fuzzy=True)
            if parsed.tzinfo is None:
                parsed = timezone.make_aware(parsed, timezone.get_default_timezone())
            return parsed
        except Exception as e:
            logger.warning(f"Date parsing failed for '{date_str}': {e}")
            return fallback

    @staticmethod
    def _clean_text(text: Optional[str]) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    @staticmethod
    def _extract_value(text: str) -> tuple:
        """Extract numeric value and currency from text."""
        if not text:
            return None, 'USD'
        # Match patterns like $50,000, 100.000 EUR, USD 1.2M, etc.
        patterns = [
            r'([\$€£])\s*([\d\.,]+)\s*([kKmMbB]?)',
            r'([\d\.,]+)\s*([kKmMbB]?)\s*(USD|EUR|GBP|€|\$|£)',
            r'(USD|EUR|GBP)\s*([\d\.,]+)\s*([kKmMbB]?)',
        ]
        for pat in patterns:
            m = re.search(pat, text, re.I)
            if m:
                groups = m.groups()
                # Simplistic extraction
                try:
                    val_str = [g for g in groups if g.replace('.', '').replace(',', '').isdigit()][0]
                    val = float(val_str.replace(',', ''))
                    curr = [g for g in groups if g.upper() in ('USD', 'EUR', 'GBP', '$', '€', '£')][0]
                    curr_map = {'$': 'USD', '€': 'EUR', '£': 'GBP'}
                    curr = curr_map.get(curr, curr.upper())
                    return val, curr
                except (IndexError, ValueError):
                    continue
        return None, 'USD'

    @staticmethod
    def _make_external_id(source_name: str, raw_id: str) -> str:
        """Create a stable, fixed-length external ID by hashing source + identifier."""
        return hashlib.md5(f"{source_name}:{raw_id}".encode()).hexdigest()

    @staticmethod
    def _standardize_item(data: Dict[str, Any], source) -> Dict[str, Any]:
        """Normalize a raw scraped item into the standard dictionary format."""
        return {
            'external_id': data.get('external_id', ''),
            'external_url': data.get('external_url', source.url),
            'title': data.get('title', ''),
            'organization': data.get('organization', source.organization),
            'client': data.get('client', ''),
            'sector': data.get('sector', ''),
            'country': data.get('country', ''),
            'region': data.get('region', ''),
            'description': data.get('description', ''),
            'value': data.get('value'),
            'currency': data.get('currency', 'USD'),
            'deadline': data.get('deadline'),
            'published_at': data.get('published_at'),
            'language': data.get('language', ''),
            'sector_tags': data.get('sector_tags', []),
            'geographic_scope': data.get('geographic_scope', {}),
            'source_metadata': data.get('source_metadata', {}),
            'requirements': data.get('requirements', []),
        }
