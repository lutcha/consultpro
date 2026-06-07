from smtplib import SMTPException
from unittest.mock import patch

from django.core import mail
from django.core.management import CommandError, call_command
from django.test import SimpleTestCase, TestCase, override_settings

from apps.users.emails import EmailDeliveryError, send_invitation_email, send_smtp_test_email
from apps.users.models import User, UserInvitation


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

