"""
Tests for scraping robustness: SSL handling, retry logic, and robots.txt.
All tests use mocks — no network or DB access required.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch, PropertyMock

import requests
import requests.exceptions
from django.test import SimpleTestCase

from apps.scraping.scrapers.base import BaseScraper
from apps.scraping.services.deep_extraction import extract_deep_content, _http_get


def _make_source(**kwargs):
    defaults = {
        'name': 'Test Source',
        'url': 'https://example.com',
        'organization': 'Test Org',
        'scraper_config': {},
        'verify_ssl': True,
        'respect_robots_txt': False,  # off by default in tests to avoid robots HTTP
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


class FakeScraper(BaseScraper):
    """Minimal concrete scraper for testing BaseScraper internals."""

    def fetch(self, url=None, **kwargs):
        return ''

    def parse(self, raw_data):
        return []


# ── SSL session config ────────────────────────────────────────────────────────

class SSLSessionConfigTests(SimpleTestCase):
    def test_verify_ssl_true_sets_session_verify(self):
        scraper = FakeScraper(_make_source(verify_ssl=True))
        self.assertTrue(scraper.session.verify)

    def test_verify_ssl_false_sets_session_verify_false(self):
        scraper = FakeScraper(_make_source(verify_ssl=False))
        self.assertFalse(scraper.session.verify)


# ── Exponential backoff ───────────────────────────────────────────────────────

class ExponentialBackoffTests(SimpleTestCase):
    def test_retries_on_connection_error(self):
        scraper = FakeScraper(_make_source(scraper_config={'max_retries': 2}))

        call_count = 0

        def flaky_get(url, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise requests.exceptions.ConnectionError('connection refused')
            resp = MagicMock()
            resp.raise_for_status = MagicMock()
            return resp

        with patch.object(scraper.session, 'get', side_effect=flaky_get), \
             patch('time.sleep'):
            result = scraper._http_get('https://example.com/page')

        self.assertEqual(call_count, 3)

    def test_raises_after_max_retries(self):
        scraper = FakeScraper(_make_source(scraper_config={'max_retries': 1}))

        with patch.object(scraper.session, 'get',
                          side_effect=requests.exceptions.Timeout('timeout')), \
             patch('time.sleep'), \
             self.assertRaises(requests.exceptions.Timeout):
            scraper._http_get('https://example.com/page')

    def test_ssl_error_not_retried(self):
        scraper = FakeScraper(_make_source())
        call_count = 0

        def ssl_fail(url, **kwargs):
            nonlocal call_count
            call_count += 1
            raise requests.exceptions.SSLError('cert verify failed')

        with patch.object(scraper.session, 'get', side_effect=ssl_fail), \
             patch('time.sleep'), \
             self.assertRaises(requests.exceptions.SSLError):
            scraper._http_get('https://bad-ssl.example.com')

        self.assertEqual(call_count, 1, "SSL errors must not be retried")

    def test_429_retried(self):
        scraper = FakeScraper(_make_source(scraper_config={'max_retries': 2}))
        call_count = 0

        def rate_limited(url, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                mock_resp = MagicMock()
                mock_resp.status_code = 429
                raise requests.exceptions.HTTPError(response=mock_resp)
            resp = MagicMock()
            resp.raise_for_status = MagicMock()
            return resp

        with patch.object(scraper.session, 'get', side_effect=rate_limited), \
             patch('time.sleep'):
            scraper._http_get('https://example.com/page')

        self.assertEqual(call_count, 3)


# ── robots.txt ────────────────────────────────────────────────────────────────

class RobotsTxtTests(SimpleTestCase):
    def test_allowed_when_no_robots_txt(self):
        scraper = FakeScraper(_make_source())
        resp = MagicMock()
        resp.status_code = 404
        resp.text = ''

        with patch.object(scraper.session, 'get', return_value=resp):
            self.assertTrue(scraper._check_robots_txt('https://example.com/page'))

    def test_blocked_by_disallow_all(self):
        scraper = FakeScraper(_make_source())
        resp = MagicMock()
        resp.status_code = 200
        resp.text = 'User-agent: *\nDisallow: /'

        with patch.object(scraper.session, 'get', return_value=resp):
            self.assertFalse(scraper._check_robots_txt('https://example.com/page'))

    def test_allowed_when_robots_ssl_error(self):
        scraper = FakeScraper(_make_source())

        with patch.object(scraper.session, 'get',
                          side_effect=requests.exceptions.SSLError('cert error')):
            self.assertTrue(scraper._check_robots_txt('https://example.com/page'))

    def test_allowed_when_robots_request_fails(self):
        scraper = FakeScraper(_make_source())

        with patch.object(scraper.session, 'get',
                          side_effect=requests.exceptions.ConnectionError('refused')):
            self.assertTrue(scraper._check_robots_txt('https://example.com/page'))

    def test_execute_skipped_when_robots_blocks(self):
        source = _make_source(respect_robots_txt=True)
        scraper = FakeScraper(source)

        resp = MagicMock()
        resp.status_code = 200
        resp.text = 'User-agent: *\nDisallow: /'

        with patch.object(scraper.session, 'get', return_value=resp):
            result = scraper.execute()

        self.assertEqual(result['status'], 'robots_blocked')
        self.assertEqual(result['items'], [])


# ── deep_extraction ───────────────────────────────────────────────────────────

class DeepExtractionSSLTests(SimpleTestCase):
    def test_ssl_error_returns_ssl_error_status(self):
        with patch('apps.scraping.services.deep_extraction._http_get',
                   side_effect=requests.exceptions.SSLError('cert verify failed')):
            result = extract_deep_content('https://bad-ssl.example.com', verify_ssl=True)

        self.assertEqual(result['status'], 'ssl_error')
        self.assertIn('SSL', result['error'])

    def test_connection_error_returns_failed_status(self):
        with patch('apps.scraping.services.deep_extraction._http_get',
                   side_effect=requests.exceptions.ConnectionError('refused')):
            result = extract_deep_content('https://example.com/page')

        self.assertEqual(result['status'], 'failed')

    def test_missing_url_returns_skipped(self):
        result = extract_deep_content('')
        self.assertEqual(result['status'], 'skipped')

    def test_verify_ssl_false_passed_through(self):
        captured = {}

        def fake_http_get(url, verify_ssl=True, **kwargs):
            captured['verify_ssl'] = verify_ssl
            resp = MagicMock()
            resp.raise_for_status = MagicMock()
            resp.headers = {'content-type': 'text/html'}
            resp.url = url
            resp.text = '<html><body>hello world content here</body></html>'
            return resp

        with patch('apps.scraping.services.deep_extraction._http_get', side_effect=fake_http_get):
            extract_deep_content('https://example.com/page', verify_ssl=False)

        self.assertFalse(captured.get('verify_ssl'))


# ── deep_extraction retry ─────────────────────────────────────────────────────

class DeepExtractionRetryTests(SimpleTestCase):
    def test_retries_on_timeout(self):
        call_count = 0

        def flaky(url, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise requests.exceptions.Timeout('timed out')
            resp = MagicMock()
            resp.raise_for_status = MagicMock()
            resp.headers = {'content-type': 'text/html'}
            resp.url = url
            resp.text = '<html><body>recovered content</body></html>'
            return resp

        with patch('apps.scraping.services.deep_extraction.requests.get', side_effect=flaky), \
             patch('time.sleep'):
            # Call _http_get directly to test retry logic
            from apps.scraping.services.deep_extraction import _http_get as deep_get
            result = deep_get('https://example.com/page')

        self.assertEqual(call_count, 3)
