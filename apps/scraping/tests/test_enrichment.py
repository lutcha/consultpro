from types import SimpleNamespace
from django.test import TestCase

from apps.scraping.services.enrichment import (
    detect_sector,
    detect_country,
    detect_region,
    detect_consortium_type,
    detect_eligible_countries,
    enrich_for_import,
)


class DetectSectorTests(TestCase):
    def test_existing_valid_sector_returned_as_is(self):
        self.assertEqual(detect_sector('anything', 'health'), 'health')

    def test_invalid_existing_falls_through_to_keyword(self):
        result = detect_sector('solar energy project', 'garbage')
        self.assertEqual(result, 'renewable_energy')

    def test_keyword_match_portuguese(self):
        self.assertEqual(detect_sector('projeto de saneamento e água'), 'water_sanitation')

    def test_keyword_match_english(self):
        self.assertEqual(detect_sector('capacity building for public officials'), 'capacity_building')

    def test_fallback_when_no_match(self):
        self.assertEqual(detect_sector('lorem ipsum dolor'), 'governance')

    def test_specificity_renewable_over_energy(self):
        result = detect_sector('installation of solar panels and energy grid')
        self.assertEqual(result, 'renewable_energy')


class DetectCountryTests(TestCase):
    def test_existing_valid_code_returned(self):
        self.assertEqual(detect_country('', 'cv'), 'cv')

    def test_existing_country_name_resolved(self):
        self.assertEqual(detect_country('', 'Cabo Verde'), 'cv')

    def test_longest_match_wins(self):
        # 'south sudan' must win over 'sudan'
        self.assertEqual(detect_country('project in south sudan'), 'ss')

    def test_english_name_in_text(self):
        self.assertEqual(detect_country('assignment in mozambique'), 'mz')

    def test_portuguese_name_in_text(self):
        self.assertEqual(detect_country('actividade em angola'), 'ao')

    def test_unknown_defaults_to_int(self):
        self.assertEqual(detect_country('lorem ipsum'), 'int')


class DetectRegionTests(TestCase):
    def test_cv_returns_west_africa(self):
        self.assertIn('west_africa', detect_region('cv').split() or [detect_region('cv')])

    def test_mz_primary_region(self):
        region = detect_region('mz')
        self.assertIn(region, ('east_africa', 'southern_africa', 'lusophone_africa'))

    def test_unknown_country(self):
        self.assertEqual(detect_region('xx'), 'international')


class DetectConsortiumTypeTests(TestCase):
    def test_lead(self):
        self.assertEqual(detect_consortium_type('the lead firm must have 10 years'), 'lead')

    def test_partner(self):
        self.assertEqual(detect_consortium_type('looking for a partner firm to join'), 'partner')

    def test_open(self):
        self.assertEqual(detect_consortium_type('bids from a consortium are accepted'), 'open')

    def test_solo_default(self):
        self.assertEqual(detect_consortium_type('individual consultant required'), 'solo')


class DetectEligibleCountriesTests(TestCase):
    def _make_opp(self, **kwargs):
        defaults = {
            'country': '',
            'region': '',
            'description': '',
            'geographic_scope': {},
        }
        defaults.update(kwargs)
        return SimpleNamespace(**defaults)

    def test_primary_country_included(self):
        opp = self._make_opp(country='cv')
        result = detect_eligible_countries(opp)
        self.assertIn('cv', result)

    def test_geographic_scope_countries_included(self):
        opp = self._make_opp(
            country='cv',
            geographic_scope={'countries': ['mz', 'ao']},
        )
        result = detect_eligible_countries(opp)
        self.assertIn('mz', result)
        self.assertIn('ao', result)

    def test_int_excluded_from_list(self):
        opp = self._make_opp(country='international')
        result = detect_eligible_countries(opp)
        self.assertNotIn('int', result)


class EnrichForImportTests(TestCase):
    def _make_opp(self, **kwargs):
        defaults = {
            'id': 1,
            'title': '',
            'description': '',
            'deep_content_text': '',
            'organization': '',
            'sector': '',
            'country': '',
            'region': '',
            'geographic_scope': {},
        }
        defaults.update(kwargs)
        return SimpleNamespace(**defaults)

    def test_full_enrichment(self):
        opp = self._make_opp(
            title='Construction of solar mini-grids in Mozambique',
            description='The lead firm must form a consortium. '
                        'The project targets rural communities in Mozambique.',
            country='mz',
        )
        result = enrich_for_import(opp)
        self.assertEqual(result['sector'], 'renewable_energy')
        self.assertEqual(result['country'], 'mz')
        self.assertIn('mz', result['eligible_countries'])
        self.assertEqual(result['consortium_type'], 'lead')

    def test_never_raises_on_broken_input(self):
        opp = self._make_opp()
        result = enrich_for_import(opp)
        self.assertIn('sector', result)
        self.assertIn('country', result)
        self.assertIn('eligible_countries', result)
        self.assertIn('consortium_type', result)
