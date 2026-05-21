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
from urllib.parse import urljoin, urlparse

import requests
import urllib3
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

_TRANSIENT_EXCEPTIONS = (
    requests.exceptions.Timeout,
    requests.exceptions.ConnectionError,
    requests.exceptions.ChunkedEncodingError,
)


class BaseScraper:
    """Base class for all web scrapers."""

    def __init__(self, source):
        self.source = source
        self.config = source.scraper_config or {}
        self.verify_ssl = getattr(source, 'verify_ssl', True)
        self.respect_robots = getattr(source, 'respect_robots_txt', True)

        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self.session.verify = self.verify_ssl

        if not self.verify_ssl:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def fetch(self, url: Optional[str] = None, **kwargs) -> str:
        """Fetch the raw data (HTML, JSON, etc.) from the source."""
        raise NotImplementedError("Subclasses must implement fetch()")

    def parse(self, raw_data: str) -> List[Dict[str, Any]]:
        """Parse the raw data into a list of standardized dictionaries."""
        raise NotImplementedError("Subclasses must implement parse()")

    def execute(self) -> Dict[str, Any]:
        """Execute the full scraping pipeline: robots check → fetch → parse."""
        try:
            logger.info("Starting scrape for %s", self.source.name)

            if self.respect_robots and not self._check_robots_txt(self.source.url):
                logger.warning("robots.txt blocks %s — skipping", self.source.url)
                return {
                    'status': 'robots_blocked',
                    'items': [],
                    'error': f'robots.txt disallows {self.source.url}',
                }

            raw_data = self.fetch()
            items = self.parse(raw_data)
            logger.info("Successfully scraped %d items from %s", len(items), self.source.name)
            return {'status': 'success', 'items': items, 'error': None}

        except Exception as e:
            logger.error("Error scraping %s: %s", self.source.name, e, exc_info=True)
            return {'status': 'error', 'items': [], 'error': str(e)}

    # ── HTTP helpers ──────────────────────────────────────────────────────────

    def _http_get(self, url: str, retries: int = None, backoff: float = 1.0, **kwargs) -> requests.Response:
        """HTTP GET with exponential backoff retry.

        SSL errors are never retried — they require source-level config (verify_ssl=False).
        Transient network errors (timeout, connection reset) are retried up to `retries` times.
        """
        if retries is None:
            retries = int(self.config.get('max_retries', 2))
        timeout = int(self.config.get('request_timeout', 30))

        for attempt in range(retries + 1):
            try:
                resp = self.session.get(url, timeout=timeout, **kwargs)
                resp.raise_for_status()
                return resp
            except requests.exceptions.SSLError as exc:
                # Not transient — raise immediately so the source can be flagged
                logger.error("SSL error fetching %s: %s", url, exc)
                raise
            except _TRANSIENT_EXCEPTIONS as exc:
                if attempt == retries:
                    raise
                sleep_time = backoff * (2 ** attempt)   # 1s, 2s, 4s …
                logger.warning(
                    "Transient error (attempt %d/%d) for %s — retry in %.1fs: %s",
                    attempt + 1, retries + 1, url, sleep_time, exc,
                )
                time.sleep(sleep_time)
            except requests.exceptions.HTTPError as exc:
                # 4xx/5xx — only retry on 429 / 5xx
                status_code = exc.response.status_code if exc.response is not None else 0
                if status_code in (429, 500, 502, 503, 504) and attempt < retries:
                    sleep_time = backoff * (2 ** attempt)
                    logger.warning(
                        "HTTP %d for %s — retry in %.1fs", status_code, url, sleep_time
                    )
                    time.sleep(sleep_time)
                else:
                    raise

    # ── robots.txt ────────────────────────────────────────────────────────────

    def _check_robots_txt(self, url: str) -> bool:
        """Return True if the URL is allowed by robots.txt.

        Fetches robots.txt via our session (respects verify_ssl).
        Returns True (allowed) on any fetch/parse error — conservative default.
        """
        try:
            parsed = urlparse(url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

            try:
                resp = self.session.get(robots_url, timeout=10)
            except requests.exceptions.SSLError:
                logger.warning("SSL error fetching robots.txt for %s — assuming allowed", url)
                return True
            except requests.exceptions.RequestException as exc:
                logger.warning("Could not fetch robots.txt for %s: %s — assuming allowed", url, exc)
                return True

            if resp.status_code == 404:
                return True  # No robots.txt → no restriction

            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.parse(resp.text.splitlines())
            can_fetch = rp.can_fetch(DEFAULT_HEADERS['User-Agent'], url)
            if not can_fetch:
                logger.warning("robots.txt disallows fetching %s", url)
            return can_fetch

        except Exception as exc:
            logger.warning("robots.txt check failed for %s: %s — assuming allowed", url, exc)
            return True

    # ── Data helpers ──────────────────────────────────────────────────────────

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
        except Exception as exc:
            logger.warning("Date parsing failed for '%s': %s", date_str, exc)
            return fallback

    @staticmethod
    def _clean_text(text: Optional[str]) -> str:
        if not text:
            return ""
        if isinstance(text, (list, tuple, set)):
            text = ' '.join(BaseScraper._clean_text(item) for item in text if item)
        elif isinstance(text, dict):
            preferred = [
                text.get('value'), text.get('name'), text.get('title'),
                text.get('label'), text.get('alias'), text.get('url'),
            ]
            text = ' '.join(BaseScraper._clean_text(item) for item in preferred if item)
        return re.sub(r'\s+', ' ', str(text)).strip()

    @staticmethod
    def _extract_value(text: str) -> tuple:
        """Extract numeric value and currency from text."""
        if not text:
            return None, 'USD'
        patterns = [
            r'([\$€£])\s*([\d\.,]+)\s*([kKmMbB]?)',
            r'([\d\.,]+)\s*([kKmMbB]?)\s*(USD|EUR|GBP|€|\$|£)',
            r'(USD|EUR|GBP)\s*([\d\.,]+)\s*([kKmMbB]?)',
        ]
        for pat in patterns:
            m = re.search(pat, text, re.I)
            if m:
                groups = m.groups()
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
        return hashlib.md5(f"{source_name}:{raw_id}".encode()).hexdigest()

    @staticmethod
    def _standardize_item(data: Dict[str, Any], source) -> Dict[str, Any]:
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
