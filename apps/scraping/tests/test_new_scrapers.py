import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from apps.scraping.scrapers.eu_funding_scraper import EUFundingScraper
from apps.scraping.scrapers.giz_scraper import GIZScraper


def _make_source(**kwargs):
    defaults = {
        'name': 'Test Source',
        'url': 'https://example.com',
        'organization': 'Test Org',
        'scraper_config': {},
        'verify_ssl': True,
        'respect_robots_txt': False,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _response(text):
    response = MagicMock()
    response.text = text
    return response


class GIZScraperTests(SimpleTestCase):
    @patch('apps.scraping.scrapers.giz_scraper.BaseScraper._http_get')
    def test_parse_real_html_structure(self, mock_get):
        mock_get.return_value = _response("""
            <html><body>
              <article>
                <h2><a href="/en/jobs/123.html">Energy Advisor Cabo Verde</a></h2>
                <span class="country">Cabo Verde</span>
                <span class="sector">Renewable Energy</span>
                <time datetime="2026-08-31">31 August 2026</time>
              </article>
            </body></html>
        """)
        scraper = GIZScraper(_make_source(organization='GIZ'))

        items = scraper.execute()['items']

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['title'], 'Energy Advisor Cabo Verde')
        self.assertEqual(items[0]['external_url'], 'https://www.giz.de/en/jobs/123.html')

    @patch('apps.scraping.scrapers.giz_scraper.BaseScraper._http_get')
    def test_graceful_fallback_empty_body(self, mock_get):
        mock_get.return_value = _response('<html><body></body></html>')
        scraper = GIZScraper(_make_source(organization='GIZ'))

        result = scraper.execute()

        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['items'], [])

    def test_standardized_item_shape(self):
        scraper = GIZScraper(_make_source(organization='GIZ'))
        item = scraper._parse_article(_article("""
            <article>
              <h2><a href="/en/jobs/456.html">Procurement Specialist</a></h2>
              <span class="country">Cabo Verde</span>
              <span class="sector">Governance</span>
            </article>
        """))
        standardized = scraper._standardize_item(item, scraper.source)
        standardized['raw_payload'] = item

        for key in [
            'external_id', 'external_url', 'title', 'organization', 'deadline',
            'raw_payload', 'source_metadata'
        ]:
            self.assertIn(key, standardized)


class EUFundingScraperTests(SimpleTestCase):
    @patch('apps.scraping.scrapers.eu_funding_scraper.BaseScraper._http_get')
    def test_parse_json_api_response(self, mock_get):
        payload = {
            'data': [
                {
                    'identifier': 'EU-CALL-1',
                    'title': 'Digital public services',
                    'deadlineDate': '2026-09-15',
                    'budgetTopicActions': [{'description': 'Support for digital transformation'}],
                    'programmePeriod': ['2021-2027'],
                    'fundingRegions': ['West Africa'],
                }
            ]
        }
        mock_get.return_value = _response(json.dumps(payload))
        scraper = EUFundingScraper(_make_source(organization='European Commission'))

        items = scraper.execute()['items']

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['title'], 'Digital public services')
        self.assertIn('Support for digital transformation', items[0]['description'])

    @patch('apps.scraping.scrapers.eu_funding_scraper.BaseScraper._http_get')
    def test_graceful_fallback_non_json_response(self, mock_get):
        mock_get.return_value = _response('<html><body>Error</body></html>')
        scraper = EUFundingScraper(_make_source(organization='European Commission'))

        result = scraper.execute()

        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['items'], [])

    def test_cv_eligibility_flag_set_for_west_africa(self):
        scraper = EUFundingScraper(_make_source(organization='European Commission'))
        items = scraper.parse(json.dumps({
            'data': [{
                'identifier': 'EU-CALL-CV',
                'title': 'Regional resilience',
                'deadlineDate': '2026-09-15',
                'budgetTopicActions': ['Climate adaptation'],
                'programmePeriod': ['2021-2027'],
                'fundingRegions': ['CV'],
            }]
        }))

        self.assertEqual(len(items), 1)
        self.assertTrue(items[0]['geographic_scope']['cv_eligible'])


class ProxyManagerTests(SimpleTestCase):
    def test_no_proxies_returns_plain_session(self):
        with patch.dict('os.environ', {}, clear=True):
            from apps.scraping.services.proxy_manager import get_proxy_session

            session = get_proxy_session()

        self.assertEqual(session.proxies, {})

    def test_proxy_session_cycles_round_robin(self):
        with patch.dict(
            'os.environ',
            {'SCRAPING_PROXIES': 'http://user:pass@proxy1:8080,http://user:pass@proxy2:8080'},
            clear=True,
        ):
            from apps.scraping.services import proxy_manager
            proxy_manager._proxy_index = 0
            proxy_manager._proxy_cache_raw = None

            first = proxy_manager.get_proxy_session()
            second = proxy_manager.get_proxy_session()
            third = proxy_manager.get_proxy_session()

        self.assertEqual(first.proxies['http'], 'http://user:pass@proxy1:8080')
        self.assertEqual(second.proxies['http'], 'http://user:pass@proxy2:8080')
        self.assertEqual(third.proxies['http'], 'http://user:pass@proxy1:8080')

    def test_proxy_format_validation(self):
        with patch.dict(
            'os.environ',
            {'SCRAPING_PROXIES': 'not-a-url,http://user:pass@proxy1:8080'},
            clear=True,
        ):
            from apps.scraping.services import proxy_manager
            proxy_manager._proxy_index = 0
            proxy_manager._proxy_cache_raw = None

            with self.assertLogs('apps.scraping.services.proxy_manager', level='WARNING'):
                session = proxy_manager.get_proxy_session()

        self.assertEqual(session.proxies['http'], 'http://user:pass@proxy1:8080')


class FailedScrapeLoggerTests(SimpleTestCase):
    def test_log_writes_valid_json_line(self):
        from apps.scraping.services.failed_scrapes_logger import (
            FAILED_LOG_PATH,
            _failed_logger,
            log_failed_scrape,
        )

        log_failed_scrape('Source A', 1, 'boom', job_id=10)
        for handler in _failed_logger.handlers:
            handler.flush()

        line = Path(FAILED_LOG_PATH).read_text(encoding='utf-8').splitlines()[-1]
        data = json.loads(line)
        self.assertEqual(data['source_name'], 'Source A')
        self.assertEqual(data['source_id'], 1)
        self.assertEqual(data['job_id'], 10)
        self.assertEqual(data['error'], 'boom')

    def test_log_truncates_long_error_messages(self):
        from apps.scraping.services.failed_scrapes_logger import (
            FAILED_LOG_PATH,
            _failed_logger,
            log_failed_scrape,
        )

        log_failed_scrape('Source B', 2, 'x' * 2500)
        for handler in _failed_logger.handlers:
            handler.flush()

        line = Path(FAILED_LOG_PATH).read_text(encoding='utf-8').splitlines()[-1]
        data = json.loads(line)
        self.assertEqual(len(data['error']), 2000)


def _article(html):
    from bs4 import BeautifulSoup

    return BeautifulSoup(html, 'lxml').find('article')
