import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from apps.scraping.scrapers.afdb_scraper import AfDBScraper
from apps.scraping.scrapers.ecreee_scraper import ECREEEScraper
from apps.scraping.scrapers.eu_funding_scraper import EUFundingScraper
from apps.scraping.scrapers.generic_portal_scraper import GenericPortalScraper
from apps.scraping.scrapers.giz_scraper import GIZScraper
from apps.scraping.scrapers.luxdev_scraper import LuxDevScraper
from apps.scraping.scrapers.undp_scraper import UNDPScraper
from apps.scraping.scrapers.ugpe_scraper import UGPEScraper
from apps.scraping.scrapers.worldbank_scraper import WorldBankScraper


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
        scraper = GIZScraper(_make_source(url='https://www.giz.de', organization='GIZ'))

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

    def test_parse_procurement_table_rows(self):
        scraper = GIZScraper(_make_source(
            url='https://ausschreibungen.giz.de/Satellite/company/welcome.do',
            organization='GIZ',
            scraper_config={'item_selectors': ['table tr']},
        ))

        items = scraper.parse("""
            <table>
              <tr>
                <td><a href="/Satellite/public/tender/123">Consulting services for energy planning</a></td>
                <td>Deadline: 31/08/2026</td>
              </tr>
            </table>
        """)

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['title'], 'Consulting services for energy planning')
        self.assertEqual(items[0]['external_url'], 'https://ausschreibungen.giz.de/Satellite/public/tender/123')
        self.assertTrue(items[0]['deadline'])


class PriorityProcurementScraperTests(SimpleTestCase):
    def test_world_bank_accepts_list_fields_and_relative_urls(self):
        scraper = WorldBankScraper(_make_source(organization='World Bank'))
        items = scraper.parse(json.dumps({
            'response': {
                'docs': [{
                    'id': 'WB-1',
                    'title': 'Consulting services for digital procurement',
                    'deadline': '2026-09-30',
                    'pdate': '2026-05-01',
                    'countryname': ['Cabo Verde'],
                    'regionname': ['Africa'],
                    'sector': [{'name': 'Governance'}],
                    'project_name': ['Digital government programme'],
                    'url': '/procurement/noticedetail/WB-1',
                    'borrower': 'Government of Cabo Verde',
                }]
            }
        }))

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['country'], 'Cabo Verde')
        self.assertEqual(items[0]['sector'], 'Governance')
        self.assertEqual(items[0]['external_url'], 'https://projects.worldbank.org/procurement/noticedetail/WB-1')

    def test_world_bank_accepts_current_procnotices_payload(self):
        scraper = WorldBankScraper(_make_source(organization='World Bank'))
        items = scraper.parse(json.dumps({
            'total': '1',
            'procnotices': [{
                'id': 'OP00404566',
                'title': 'Consulting services for energy access planning',
                'submission_deadline_date': '2028-11-24T23:59:59Z',
                'pdate': '2026-06-01T00:00:00Z',
                'project_ctry_name': 'Cabo Verde',
                'regionname': 'Western And Central Africa',
                'procurement_group_desc': 'Consultant Services',
                'procurement_method_name': 'Individual Consultant Selection',
                'project_name': 'Renewable energy programme',
                'notice_type': 'Request for Expression of Interest',
                'url': 'https://projects.worldbank.org/en/projects-operations/procurement-detail/OP00404566',
            }]
        }))

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['external_id'], scraper._make_external_id('WorldBank', 'OP00404566'))
        self.assertEqual(items[0]['country'], 'Cabo Verde')
        self.assertEqual(items[0]['sector'], 'Consultant Services')
        self.assertTrue(items[0]['deadline'])

    def test_afdb_accepts_drupal_reference_fields(self):
        scraper = AfDBScraper(_make_source(organization='AfDB'))
        items = scraper.parse(json.dumps({
            'source': 'json_api',
            'items': [{
                'nid': 77,
                'title': 'Expression of interest for climate finance advisory',
                'path': {'alias': '/en/procurement/77'},
                'body': {'value': '<p>Deadline: 15 September 2026</p>'},
                'field_country': [{'name': 'Cabo Verde'}],
                'field_category': {'name': 'Consultancy'},
            }]
        }))

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['country'], 'Cabo Verde')
        self.assertEqual(items[0]['sector'], 'Consultancy')
        self.assertTrue(items[0]['deadline'])

    def test_ungm_accepts_wrapped_results_and_lowercase_keys(self):
        scraper = UNDPScraper(_make_source(
            organization='UNGM',
            scraper_config={'organization': 'UNGM', 'client': 'United Nations'},
        ))
        items = scraper.parse(json.dumps({
            'results': [{
                'noticeId': 1234,
                'title': 'Consultancy for public finance reform',
                'deadlineDate': '2026-10-12',
                'publishedDate': '2026-05-10',
                'agencyName': 'UNDP',
                'countryName': 'Guinea-Bissau',
                'noticeType': 'Request for proposal',
                'url': 'https://www.ungm.org/Public/Notice/1234',
            }]
        }))

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['organization'], 'UNGM')
        self.assertEqual(items[0]['client'], 'United Nations')
        self.assertEqual(items[0]['country'], 'Guinea-Bissau')

    def test_generic_portal_ecowas_deduplicates_and_parses_numeric_deadline(self):
        scraper = GenericPortalScraper(_make_source(
            name='ECOWAS - Procurement Portal',
            organization='ECOWAS',
            url='https://www.ecowas.int/procurement/',
            scraper_config={
                'item_selectors': ['article'],
                'title_selector': 'h3 a',
                'link_selector': 'a[href]',
                'deadline_selector': '.deadline',
                'organization': 'ECOWAS',
                'client': 'ECOWAS / CEDEAO',
                'country': 'West Africa',
            },
        ))
        html = """
            <article>
              <h3><a href="/procurement/eoi-1">Expression of interest for regional trade advisory</a></h3>
              <span class="deadline">Deadline: 31/08/2026</span>
            </article>
            <article>
              <h3><a href="/procurement/eoi-1">Expression of interest for regional trade advisory</a></h3>
              <span class="deadline">Deadline: 31/08/2026</span>
            </article>
            <article><a href="/about">Read more</a></article>
        """

        items = scraper.parse(html)

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['organization'], 'ECOWAS')
        self.assertTrue(items[0]['deadline'])

    def test_generic_portal_ecowas_parses_closing_date_embedded_in_title(self):
        scraper = GenericPortalScraper(_make_source(
            name='ECOWAS - Procurement Portal',
            organization='ECOWAS',
            url='https://www.ecowas.int/procurement/',
            scraper_config={
                'item_selectors': ['article'],
                'title_selector': 'h3 a',
                'link_selector': 'a[href]',
                'deadline_selector': '.deadline',
                'organization': 'ECOWAS',
                'client': 'ECOWAS / CEDEAO',
                'country': 'West Africa',
            },
        ))
        html = """
            <article>
              <h3>
                <a href="/procurement/regional-advisory">
                  Expression of interest for regional advisory services - Closing date: 30 Sep, 2026
                </a>
              </h3>
              <p>Consultancy support for ECOWAS institutions.</p>
            </article>
        """

        items = scraper.parse(html)

        self.assertEqual(len(items), 1)
        self.assertIn('2026-09-30', items[0]['deadline'])
        self.assertEqual(items[0]['organization'], 'ECOWAS')
        self.assertEqual(items[0]['country'], 'West Africa')
        self.assertEqual(
            items[0]['external_url'],
            'https://www.ecowas.int/procurement/regional-advisory',
        )

    def test_generic_portal_ecowas_parses_closing_date_text_variation(self):
        scraper = GenericPortalScraper(_make_source(
            name='ECOWAS - Procurement Portal',
            organization='ECOWAS',
            url='https://www.ecowas.int/procurement/',
            scraper_config={
                'item_selectors': ['article'],
                'title_selector': 'h3 a',
                'link_selector': 'a[href]',
                'deadline_selector': '.deadline',
                'organization': 'ECOWAS',
                'client': 'ECOWAS / CEDEAO',
                'country': 'West Africa',
            },
        ))
        html = """
            <article>
              <h3><a href="/procurement/digital-trade">Technical assistance for digital trade facilitation</a></h3>
              <p>Closing date - 30 September, 2026</p>
            </article>
        """

        items = scraper.parse(html)

        self.assertEqual(len(items), 1)
        self.assertIn('2026-09-30', items[0]['deadline'])

    def test_luxdev_deduplicates_rejects_navigation_and_parses_numeric_deadline(self):
        scraper = LuxDevScraper(_make_source(
            name='LuxDev - Marches',
            organization='LuxDev',
            url='https://luxdev.lu/fr/marches',
            scraper_config={'item_selectors': ['article']},
        ))
        html = """
            <article>
              <h3><a href="/fr/marches/cv-001">Assistance technique pour la gestion des finances publiques au Cabo Verde</a></h3>
              <span class="deadline">Date limite: 31/08/2026</span>
              <p>Mission de conseil et renforcement institutionnel.</p>
            </article>
            <article>
              <h3><a href="/fr/marches/cv-001">Assistance technique pour la gestion des finances publiques au Cabo Verde</a></h3>
              <span class="deadline">Date limite: 31/08/2026</span>
            </article>
            <article><a href="/fr/marches">Read more</a></article>
        """

        items = scraper.parse(html, base_url='https://luxdev.lu/fr/marches')

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['organization'], 'LuxDev')
        self.assertEqual(items[0]['country'], 'CPV')
        self.assertTrue(items[0]['deadline'])
        self.assertEqual(items[0]['external_url'], 'https://luxdev.lu/fr/marches/cv-001')

    def test_ugpe_deduplicates_rejects_navigation_and_uses_configured_url(self):
        scraper = UGPEScraper(_make_source(
            name='UGPE - Concursos Cabo Verde',
            organization='UGPE',
            url='https://ugpe.gov.cv/concursos',
            scraper_config={'url': 'https://ugpe.gov.cv/concursos', 'item_selectors': ['tr']},
        ))
        html = """
            <table>
              <tr>
                <td>UGPE-2026-01</td>
                <td><a href="/concursos/ugpe-2026-01">Contratação de consultor para transformação digital da administração pública</a></td>
                <td>Prazo: 15/09/2026</td>
              </tr>
              <tr>
                <td>UGPE-2026-01</td>
                <td><a href="/concursos/ugpe-2026-01">Contratação de consultor para transformação digital da administração pública</a></td>
                <td>Prazo: 15/09/2026</td>
              </tr>
              <tr><td><a href="/contactos">Read more</a></td></tr>
            </table>
        """

        items = scraper.parse(html)

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['title'], 'Contratação de consultor para transformação digital da administração pública')
        self.assertEqual(items[0]['external_id'], 'UGPE-2026-01')
        self.assertEqual(items[0]['external_url'], 'https://ugpe.gov.cv/concursos/ugpe-2026-01')
        self.assertEqual(items[0]['country'], 'Cabo Verde')
        self.assertTrue(items[0]['deadline'])


class ECREEEScraperTests(SimpleTestCase):
    @patch('apps.scraping.scrapers.ecreee_scraper.BaseScraper._http_get')
    def test_fetches_detail_deadline_when_listing_has_none(self, mock_get):
        mock_get.return_value = _response("""
            <html><body>
              <article>
                <p>Submission Deadline: 31 December 2028 at 23:59 GMT</p>
                <p>Regional renewable energy technical assistance.</p>
              </article>
            </body></html>
        """)
        scraper = ECREEEScraper(_make_source(
            name='ECREEE - Procurement Notices',
            organization='ECREEE',
            url='https://www.ecreee.org/category/procurement-notices/',
        ))

        items = scraper.parse("""
            <article class="post">
              <h2><a href="/procurement/energy-advisory/">Consulting services for renewable energy planning</a></h2>
              <p>Expression of interest for regional advisory support.</p>
            </article>
        """)

        self.assertEqual(len(items), 1)
        self.assertTrue(items[0]['deadline'])
        self.assertEqual(items[0]['source_metadata']['deadline_source'], 'detail')
        self.assertEqual(items[0]['source_metadata']['deadline_text'], '31 December 2028')
        self.assertEqual(
            items[0]['external_url'],
            'https://www.ecreee.org/procurement/energy-advisory/',
        )
        mock_get.assert_called_once_with(
            'https://www.ecreee.org/procurement/energy-advisory/',
            retries=0,
        )

    @patch('apps.scraping.scrapers.ecreee_scraper.BaseScraper._http_get')
    def test_detail_fetch_failure_does_not_crash(self, mock_get):
        mock_get.side_effect = TimeoutError('detail timeout')
        scraper = ECREEEScraper(_make_source(
            name='ECREEE - Procurement Notices',
            organization='ECREEE',
            url='https://www.ecreee.org/category/procurement-notices/',
        ))

        items = scraper.parse("""
            <article class="post">
              <h2><a href="/procurement/no-deadline/">Regional clean energy advisory</a></h2>
              <p>Request for expressions of interest.</p>
            </article>
        """)

        self.assertEqual(len(items), 1)
        self.assertIsNone(items[0]['deadline'])
        self.assertIsNone(items[0]['source_metadata']['deadline_source'])

    @patch('apps.scraping.scrapers.ecreee_scraper.BaseScraper._http_get')
    def test_listing_deadline_skips_detail_fetch_and_keeps_absolute_url(self, mock_get):
        scraper = ECREEEScraper(_make_source(
            name='ECREEE - Procurement Notices',
            organization='ECREEE',
            url='https://www.ecreee.org/category/procurement-notices/',
        ))

        items = scraper.parse("""
            <article class="post">
              <h2><a href="https://www.ecreee.org/procurement/solar-advisory/">Solar advisory services</a></h2>
              <p>Deadline: 15 January 2029</p>
            </article>
        """)

        self.assertEqual(len(items), 1)
        self.assertTrue(items[0]['deadline'])
        self.assertEqual(items[0]['source_metadata']['deadline_source'], 'listing')
        self.assertEqual(
            items[0]['external_url'],
            'https://www.ecreee.org/procurement/solar-advisory/',
        )
        mock_get.assert_not_called()

    @patch('apps.scraping.scrapers.ecreee_scraper.BaseScraper._http_get')
    def test_parses_no_later_than_submission_deadline_phrase(self, mock_get):
        scraper = ECREEEScraper(_make_source(
            name='ECREEE - Procurement Notices',
            organization='ECREEE',
            url='https://www.ecreee.org/category/procurement-notices/',
        ))

        items = scraper.parse("""
            <article class="post">
              <h2><a href="/procurement/regional-energy-consultancy/">Regional energy consultancy</a></h2>
              <p>The deadline for submission is no later than 13th of August 2026.</p>
            </article>
        """)

        self.assertEqual(len(items), 1)
        self.assertIn('2026-08-13', items[0]['deadline'])
        self.assertEqual(items[0]['source_metadata']['deadline_text'], '13th of august 2026')
        self.assertEqual(items[0]['source_metadata']['deadline_source'], 'listing')
        mock_get.assert_not_called()

    @patch('apps.scraping.scrapers.ecreee_scraper.BaseScraper._http_get')
    def test_parses_standalone_named_date_as_deadline(self, mock_get):
        scraper = ECREEEScraper(_make_source(
            name='ECREEE - Procurement Notices',
            organization='ECREEE',
            url='https://www.ecreee.org/category/procurement-notices/',
        ))

        items = scraper.parse("""
            <article class="post">
              <h2><a href="/procurement/solar-market-study/">Solar market study</a></h2>
              <p>Expressions of interest must be received by 30 July 2026.</p>
            </article>
        """)

        self.assertEqual(len(items), 1)
        self.assertIn('2026-07-30', items[0]['deadline'])
        self.assertEqual(items[0]['source_metadata']['deadline_text'], '30 july 2026')
        self.assertEqual(items[0]['source_metadata']['deadline_source'], 'listing')
        mock_get.assert_not_called()

    @patch('apps.scraping.scrapers.ecreee_scraper.BaseScraper._http_get')
    def test_parses_submission_deadline_with_weekday(self, mock_get):
        scraper = ECREEEScraper(_make_source(
            name='ECREEE - Procurement Notices',
            organization='ECREEE',
            url='https://www.ecreee.org/category/procurement-notices/',
        ))

        items = scraper.parse("""
            <article class="post">
              <h2><a href="/procurement/grid-integration-advisory/">Grid integration advisory</a></h2>
              <p>Submission deadline: Monday, 13 April 2026.</p>
            </article>
        """)

        self.assertEqual(len(items), 1)
        self.assertIn('2026-04-13', items[0]['deadline'])
        self.assertEqual(items[0]['source_metadata']['deadline_text'], 'monday, 13 april 2026')
        self.assertEqual(items[0]['source_metadata']['deadline_source'], 'listing')
        mock_get.assert_not_called()


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
