from django.test import TestCase
from django.utils import timezone

from ..models import ActivityLog, Notification
from .factories import ActivityLogFactory, NotificationFactory, UserFactory


class NotificationModelTests(TestCase):
    def test_str_representation(self):
        notification = NotificationFactory(title='Test Notification', type='warning')
        self.assertEqual(str(notification), 'warning - Test Notification')

    def test_default_read_status(self):
        notification = NotificationFactory()
        self.assertFalse(notification.read)

    def test_ordering(self):
        user = UserFactory()
        older = NotificationFactory(user=user)
        older.created_at = timezone.now() - timezone.timedelta(days=1)
        older.save()

        newer = NotificationFactory(user=user)
        newer.created_at = timezone.now()
        newer.save()

        notifications = list(Notification.objects.all())
        self.assertEqual(notifications[0], newer)
        self.assertEqual(notifications[1], older)

    def test_related_user(self):
        user = UserFactory()
        notification = NotificationFactory(user=user)
        self.assertEqual(notification.user, user)
        self.assertIn(notification, user.notifications.all())

    def test_action_fields_blank(self):
        notification = NotificationFactory(action_label='', action_url='')
        self.assertEqual(notification.action_label, '')
        self.assertEqual(notification.action_url, '')


class ActivityLogModelTests(TestCase):
    def test_str_representation(self):
        activity = ActivityLogFactory(description='A short description')
        self.assertEqual(str(activity), 'proposal_created - A short description')

    def test_ordering(self):
        older = ActivityLogFactory()
        older.created_at = timezone.now() - timezone.timedelta(days=1)
        older.save()

        newer = ActivityLogFactory()
        newer.created_at = timezone.now()
        newer.save()

        activities = list(ActivityLog.objects.all())
        self.assertEqual(activities[0], newer)
        self.assertEqual(activities[1], older)

    def test_related_user(self):
        user = UserFactory()
        activity = ActivityLogFactory(user=user)
        self.assertEqual(activity.user, user)

    def test_null_user(self):
        activity = ActivityLogFactory(user=None)
        self.assertIsNone(activity.user)

    def test_metadata_default(self):
        activity = ActivityLogFactory()
        self.assertEqual(activity.metadata, {})
