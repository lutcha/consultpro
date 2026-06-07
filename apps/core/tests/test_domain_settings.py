from django.conf import settings
from django.test import SimpleTestCase

from config.settings.base import _origin_from_url, _unique_list


class DomainSettingsTests(SimpleTestCase):
    def test_frontend_url_origin_is_allowed_for_cors_and_csrf(self):
        self.assertEqual(settings.FRONTEND_URL, 'https://consultpro.cv')
        self.assertIn('https://consultpro.cv', settings.CORS_ALLOWED_ORIGINS)
        self.assertIn('https://consultpro.cv', settings.CSRF_TRUSTED_ORIGINS)

    def test_origin_from_url_strips_path(self):
        self.assertEqual(
            _origin_from_url('https://consultpro.cv/invite/abc'),
            'https://consultpro.cv',
        )

    def test_unique_list_preserves_order(self):
        self.assertEqual(_unique_list(['a', 'b', 'a', '', 'c']), ['a', 'b', 'c'])
