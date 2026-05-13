from unittest.mock import patch

from django.test import TestCase, override_settings

from ..models import Notification
from ..tasks import send_notification
from .factories import NotificationPreferenceFactory, UserFactory


@override_settings(DEFAULT_FROM_EMAIL='alerts@consultpro.test')
class SendNotificationTaskTests(TestCase):
    def test_creates_notification_and_sends_email_for_enabled_category(self):
        user = UserFactory(email='manager@example.com')

        with patch('apps.notifications.tasks.send_mail') as mocked_send_mail:
            notification_id = send_notification(
                user.id,
                'info',
                'Nova oportunidade',
                'Foi detectada uma oportunidade elegivel.',
                email_category='new_opportunity',
            )

        notification = Notification.objects.get(pk=notification_id)
        self.assertEqual(notification.user, user)
        mocked_send_mail.assert_called_once_with(
            subject='Nova oportunidade',
            message='Foi detectada uma oportunidade elegivel.',
            from_email='alerts@consultpro.test',
            recipient_list=['manager@example.com'],
            fail_silently=False,
        )

    def test_skips_email_when_preference_is_disabled(self):
        user = UserFactory(email='manager@example.com')
        NotificationPreferenceFactory(
            user=user,
            email_on_new_opportunity=False,
        )

        with patch('apps.notifications.tasks.send_mail') as mocked_send_mail:
            send_notification(
                user.id,
                'info',
                'Nova oportunidade',
                'Foi detectada uma oportunidade elegivel.',
                email_category='new_opportunity',
            )

        mocked_send_mail.assert_not_called()

    def test_skips_email_without_category(self):
        user = UserFactory(email='manager@example.com')

        with patch('apps.notifications.tasks.send_mail') as mocked_send_mail:
            send_notification(
                user.id,
                'info',
                'Aviso',
                'Mensagem interna.',
            )

        mocked_send_mail.assert_not_called()
