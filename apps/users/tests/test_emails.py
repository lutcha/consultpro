from django.test import SimpleTestCase, override_settings
from django.core.management import CommandError, call_command

from apps.users.emails import send_smtp_test_email


class EmailServiceTests(SimpleTestCase):
    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        DEFAULT_FROM_EMAIL='noreply@consultpro.test',
        FRONTEND_URL='https://consultpro.cv/',
    )
    def test_smtp_test_email_uses_frontend_url_and_sender(self):
        from django.core import mail

        delivered = send_smtp_test_email('admin@example.com')

        self.assertEqual(delivered, 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('https://consultpro.cv', mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].from_email, 'noreply@consultpro.test')

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend',
        EMAIL_HOST='smtp.example.com',
        DEFAULT_FROM_EMAIL='noreply@consultpro.test',
    )
    def test_send_test_email_command_rejects_console_backend(self):
        with self.assertRaises(CommandError):
            call_command('send_test_email', to='admin@example.com')

