from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from ..models import ActivityLog, Notification
from .factories import ActivityLogFactory, NotificationFactory, UserFactory


class NotificationViewSetTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)

    def test_list_returns_only_current_user_notifications(self):
        NotificationFactory(user=self.user, title='My Notification')
        other_user = UserFactory()
        NotificationFactory(user=other_user, title='Other Notification')

        url = reverse('notification-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'My Notification')

    def test_retrieve_notification(self):
        notification = NotificationFactory(user=self.user)
        url = reverse('notification-detail', kwargs={'pk': notification.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], notification.title)

    def test_mark_as_read_action(self):
        notification = NotificationFactory(user=self.user, read=False)
        url = reverse('notification-read', kwargs={'pk': notification.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'marked as read')
        notification.refresh_from_db()
        self.assertTrue(notification.read)

    def test_unread_count_action(self):
        NotificationFactory(user=self.user, read=False)
        NotificationFactory(user=self.user, read=False)
        NotificationFactory(user=self.user, read=True)

        url = reverse('notification-unread-count')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['unread_count'], 2)

    def test_cannot_access_other_user_notification_detail(self):
        other_user = UserFactory()
        notification = NotificationFactory(user=other_user)
        url = reverse('notification-detail', kwargs={'pk': notification.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ActivityLogViewSetTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)

    def test_list_activity_logs(self):
        ActivityLogFactory.create_batch(3)
        url = reverse('activitylog-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)

    def test_list_read_only(self):
        url = reverse('activitylog-list')
        response = self.client.post(url, {
            'type': 'proposal_created',
            'description': 'Test',
        })
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_filter_by_type(self):
        ActivityLogFactory(type='proposal_created')
        ActivityLogFactory(type='status_changed')
        url = reverse('activitylog-list')
        response = self.client.get(url, {'type': 'proposal_created'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['type'], 'proposal_created')

    def test_user_nested_field(self):
        activity = ActivityLogFactory(user=self.user)
        url = reverse('activitylog-detail', kwargs={'pk': activity.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.data)
        self.assertIsNotNone(response.data['user'])
        self.assertIn('avatar', response.data['user'])
