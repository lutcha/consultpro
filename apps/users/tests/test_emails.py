from smtplib import SMTPException
from unittest.mock import Mock, patch

import requests
from django.core import mail
from django.core.management import CommandError, call_command
from django.test import SimpleTestCase, TestCase, override_settings

from apps.users.emails import EmailDeliveryError, send_invitation_email, send_smtp_test_email
from apps.users.mail_backends import SendGridAPIBackend
from apps.users.models import User, UserInvitation

SENDGRID_API_BACKEND = 'apps.users.mail_backends.SendGridAPIBackend'


class EmailServiceTests(SimpleTestCase):
    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        DEFAULT_FROM_EMAIL='noreply@consultpro.test',
        FRONTEND_URL='https://consultpro.cv/',
    )
    def test_smtp_test_email_uses_frontend_url_and_sender(self):
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

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend',
        EMAIL_HOST='smtp.example.com',
        EMAIL_HOST_USER='',
        EMAIL_HOST_PASSWORD='',
        DEFAULT_FROM_EMAIL='noreply@consultpro.test',
    )
    def test_send_test_email_command_rejects_missing_smtp_credentials(self):
        with self.assertRaisesMessage(CommandError, 'EMAIL_HOST_USER is empty'):
            call_command('send_test_email', to='admin@example.com')

    @override_settings(
        EMAIL_BACKEND=SENDGRID_API_BACKEND,
        SENDGRID_API_KEY='',
        DEFAULT_FROM_EMAIL='noreply@consultpro.test',
    )
    def test_send_test_email_command_rejects_missing_sendgrid_api_key(self):
        with self.assertRaisesMessage(CommandError, 'SENDGRID_API_KEY is empty'):
            call_command('send_test_email', to='admin@example.com')


class SendGridAPIBackendTests(SimpleTestCase):
    @override_settings(SENDGRID_API_KEY='SG.fake-key', EMAIL_TIMEOUT=15)
    @patch('apps.users.mail_backends.requests.post')
    def test_send_messages_posts_to_sendgrid_api(self, mocked_post):
        mocked_post.return_value = Mock(status_code=202, raise_for_status=lambda: None)
        message = mail.EmailMessage(
            subject='Subject',
            body='Body',
            from_email='noreply@consultpro.cv',
            to=['dest@example.com'],
        )

        sent = SendGridAPIBackend().send_messages([message])

        self.assertEqual(sent, 1)
        mocked_post.assert_called_once()
        _, kwargs = mocked_post.call_args
        self.assertEqual(kwargs['headers']['Authorization'], 'Bearer SG.fake-key')
        self.assertEqual(kwargs['json']['from'], {'email': 'noreply@consultpro.cv'})
        self.assertEqual(kwargs['json']['personalizations'][0]['to'], [{'email': 'dest@example.com'}])

    @override_settings(SENDGRID_API_KEY='')
    def test_send_messages_raises_when_api_key_missing(self):
        message = mail.EmailMessage(
            subject='Subject', body='Body', from_email='noreply@consultpro.cv', to=['dest@example.com']
        )
        with self.assertRaises(OSError):
            SendGridAPIBackend().send_messages([message])

    @override_settings(SENDGRID_API_KEY='SG.fake-key')
    @patch('apps.users.mail_backends.requests.post', side_effect=requests.ConnectionError('boom'))
    def test_send_messages_wraps_request_errors_as_oserror(self, _mocked_post):
        message = mail.EmailMessage(
            subject='Subject', body='Body', from_email='noreply@consultpro.cv', to=['dest@example.com']
        )
        with self.assertRaises(OSError):
            SendGridAPIBackend().send_messages([message])


class InvitationEmailTests(TestCase):
    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        DEFAULT_FROM_EMAIL='noreply@consultpro.test',
        FRONTEND_URL='https://consultpro.cv/',
    )
    def test_invitation_email_uses_frontend_url_and_sender(self):
        inviter = User.objects.create_user(
            username='manager',
            email='manager@example.com',
            password='StrongPass123!',
            role='manager',
        )
        invitation = UserInvitation.create_for(
            email='invitee@example.com',
            role='consultant',
            invited_by=inviter,
        )

        delivered = send_invitation_email(invitation)

        self.assertEqual(delivered, 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].from_email, 'noreply@consultpro.test')
        self.assertIn(f'https://consultpro.cv/accept-invitation/{invitation.token}/', mail.outbox[0].body)

    @override_settings(DEFAULT_FROM_EMAIL='noreply@consultpro.test')
    @patch('apps.users.emails.send_mail', side_effect=SMTPException('SMTP down'))
    def test_invitation_email_raises_delivery_error_on_smtp_failure(self, _mocked_send):
        inviter = User.objects.create_user(
            username='manager2',
            email='manager2@example.com',
            password='StrongPass123!',
            role='manager',
        )
        invitation = UserInvitation.create_for(
            email='invitee2@example.com',
            role='consultant',
            invited_by=inviter,
        )

        with self.assertRaises(EmailDeliveryError):
            send_invitation_email(invitation)

