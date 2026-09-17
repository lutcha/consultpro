import json
from unittest.mock import patch

from django.test import TestCase, override_settings


class SupportFeedbackEndpointTests(TestCase):
    url = '/api/support/feedback/'

    @override_settings(SUPPORT_CONTACT_EMAIL='support@consultpro.test')
    @patch('apps.users.emails._send')
    def test_valid_submission_sends_email_to_support_contact(self, mocked_send):
        mocked_send.return_value = 1

        response = self.client.post(
            self.url,
            data=json.dumps({
                'name': 'Maria Silva',
                'email': 'maria@example.com',
                'category': 'bug',
                'message': 'O botão de exportar não funciona.',
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok'})
        mocked_send.assert_called_once()
        args, _ = mocked_send.call_args
        subject, body, recipients = args
        self.assertIn('bug', subject)
        self.assertIn('Maria Silva', subject)
        self.assertIn('maria@example.com', body)
        self.assertIn('não funciona', body)
        self.assertEqual(recipients, ['support@consultpro.test'])

    def test_missing_required_fields_returns_400(self):
        response = self.client.post(
            self.url,
            data=json.dumps({'name': '', 'email': '', 'message': ''}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_invalid_json_returns_400(self):
        response = self.client.post(
            self.url,
            data='not json',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    @patch('apps.users.emails._send', side_effect=RuntimeError('smtp down'))
    def test_delivery_failure_returns_502_not_misleading_success(self, _mocked_send):
        response = self.client.post(
            self.url,
            data=json.dumps({
                'name': 'Maria Silva',
                'email': 'maria@example.com',
                'message': 'Preciso de ajuda.',
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 502)

    def test_get_not_allowed(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
