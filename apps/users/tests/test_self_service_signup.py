from datetime import timedelta
from unittest.mock import Mock, patch

from django.core import mail
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from apps.tenants.models import Tenant, TenantMembership
from apps.users.models import User, UserInvitation

LOCMEM_EMAIL = dict(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DEFAULT_FROM_EMAIL='noreply@consultpro.test',
    FRONTEND_URL='https://consultpro.cv/',
)


@override_settings(**LOCMEM_EMAIL, TURNSTILE_SECRET_KEY='')
class SelfSignupViewTests(APITestCase):
    """TURNSTILE_SECRET_KEY='' — verification is skipped, matching local/CI behavior."""

    def setUp(self):
        from django.core.cache import cache
        cache.clear()  # SignupRateThrottle keys by IP; isolate each test's quota.
        self.client = APIClient()
        self.payload = {
            'organization_name': 'Acme Consulting',
            'email': 'founder@acme.test',
            'password': 'StrongPass123!',
            'confirm_password': 'StrongPass123!',
        }

    def test_signup_creates_pending_invitation_and_inactive_user(self):
        response = self.client.post(reverse('self-signup'), self.payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        user = User.objects.get(email='founder@acme.test')
        self.assertFalse(user.is_active)
        self.assertTrue(user.check_password('StrongPass123!'))

        invitation = UserInvitation.objects.get(email='founder@acme.test')
        self.assertEqual(invitation.signup_source, 'self_service')
        self.assertEqual(invitation.organization_name, 'Acme Consulting')
        self.assertFalse(invitation.is_used)

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(f'/verify-email/{invitation.token}/', mail.outbox[0].body)
        self.assertFalse(Tenant.objects.filter(name='Acme Consulting').exists())

    def test_signup_rejects_existing_active_email(self):
        User.objects.create_user(
            username='existing', email='founder@acme.test', password='x', is_active=True,
        )
        response = self.client.post(reverse('self-signup'), self.payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_signup_rejects_password_mismatch(self):
        payload = {**self.payload, 'confirm_password': 'Different123!'}
        response = self.client.post(reverse('self-signup'), payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_signup_repeat_with_valid_pending_invitation_resends_without_duplicating_user(self):
        first = self.client.post(reverse('self-signup'), self.payload, format='json')
        self.assertEqual(first.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(User.objects.filter(email='founder@acme.test').count(), 1)

        second = self.client.post(reverse('self-signup'), self.payload, format='json')
        self.assertEqual(second.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(User.objects.filter(email='founder@acme.test').count(), 1)
        self.assertEqual(UserInvitation.objects.filter(email='founder@acme.test').count(), 1)
        self.assertEqual(len(mail.outbox), 2)

    def test_signup_restarts_cleanly_after_stale_expired_attempt(self):
        stale_user = User.objects.create_user(
            username='stale', email='founder@acme.test', password='x', is_active=False,
        )
        UserInvitation.objects.create(
            email='founder@acme.test',
            role='manager',
            signup_source='self_service',
            organization_name='Old Name',
            expires_at=timezone.now() - timedelta(hours=1),
        )
        response = self.client.post(reverse('self-signup'), self.payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        stale_user.refresh_from_db()
        self.assertTrue(stale_user.check_password('StrongPass123!'))
        invitation = UserInvitation.objects.get(email='founder@acme.test', is_used=False)
        self.assertEqual(invitation.organization_name, 'Acme Consulting')

    def test_signup_does_not_delete_unrelated_inactive_user(self):
        inactive_user = User.objects.create_user(
            username='suspended',
            email='founder@acme.test',
            password='OriginalPass123!',
            is_active=False,
        )

        response = self.client.post(reverse('self-signup'), self.payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        inactive_user.refresh_from_db()
        self.assertTrue(inactive_user.check_password('OriginalPass123!'))
        self.assertFalse(
            UserInvitation.objects.filter(
                email='founder@acme.test',
                signup_source='self_service',
            ).exists()
        )

    def test_signup_rolls_back_user_and_invitation_on_email_failure(self):
        from apps.users.emails import EmailDeliveryError

        with patch(
            'apps.users.views.send_self_signup_verification_email',
            side_effect=EmailDeliveryError('SMTP down'),
        ):
            response = self.client.post(reverse('self-signup'), self.payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertFalse(User.objects.filter(email='founder@acme.test').exists())
        self.assertFalse(UserInvitation.objects.filter(email='founder@acme.test').exists())

    def test_expired_restart_preserves_user_and_pending_invitation_on_email_failure(self):
        from apps.users.emails import EmailDeliveryError

        stale_user = User.objects.create_user(
            username='stale', email='founder@acme.test', password='OldPass123!', is_active=False,
        )
        UserInvitation.objects.create(
            email='founder@acme.test',
            role='manager',
            signup_source='self_service',
            organization_name='Old Name',
            expires_at=timezone.now() - timedelta(hours=1),
        )

        with patch(
            'apps.users.views.send_self_signup_verification_email',
            side_effect=EmailDeliveryError('provider unavailable'),
        ):
            response = self.client.post(reverse('self-signup'), self.payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        stale_user.refresh_from_db()
        self.assertFalse(stale_user.is_active)
        self.assertTrue(stale_user.check_password('StrongPass123!'))
        self.assertTrue(
            UserInvitation.objects.filter(
                email='founder@acme.test',
                signup_source='self_service',
                is_used=False,
            ).exists()
        )


@override_settings(TURNSTILE_SECRET_KEY='')
class SelfSignupTurnstileTests(APITestCase):
    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        self.client = APIClient()
        self.payload = {
            'organization_name': 'Acme Consulting',
            'email': 'founder@acme.test',
            'password': 'StrongPass123!',
            'confirm_password': 'StrongPass123!',
        }

    @override_settings(TURNSTILE_SECRET_KEY='fake-secret', **LOCMEM_EMAIL)
    def test_signup_rejected_without_turnstile_token_when_configured(self):
        response = self.client.post(reverse('self-signup'), self.payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('turnstile_token', response.data)
        self.assertFalse(User.objects.filter(email='founder@acme.test').exists())

    @override_settings(TURNSTILE_SECRET_KEY='fake-secret', **LOCMEM_EMAIL)
    @patch('apps.users.turnstile.requests.post')
    def test_signup_accepted_with_valid_turnstile_token(self, mocked_post):
        mocked_post.return_value = Mock(
            status_code=200,
            raise_for_status=lambda: None,
            json=lambda: {'success': True},
        )
        response = self.client.post(
            reverse('self-signup'),
            {**self.payload, 'turnstile_token': 'valid-token'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        mocked_post.assert_called_once()

    @override_settings(TURNSTILE_SECRET_KEY='fake-secret', **LOCMEM_EMAIL)
    @patch('apps.users.turnstile.requests.post')
    def test_signup_rejected_with_invalid_turnstile_token(self, mocked_post):
        mocked_post.return_value = Mock(
            status_code=200,
            raise_for_status=lambda: None,
            json=lambda: {'success': False},
        )
        response = self.client.post(
            reverse('self-signup'),
            {**self.payload, 'turnstile_token': 'bad-token'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(email='founder@acme.test').exists())


class SelfSignupThrottleTests(APITestCase):
    def test_signup_view_uses_dedicated_signup_throttle_scope(self):
        from apps.users.throttles import SignupRateThrottle
        from apps.users.views import SelfSignupView

        self.assertIn(SignupRateThrottle, SelfSignupView.throttle_classes)
        self.assertEqual(SignupRateThrottle.scope, 'signup')

    @override_settings(**LOCMEM_EMAIL, TURNSTILE_SECRET_KEY='')
    def test_signup_throttled_after_scope_limit(self):
        from django.core.cache import cache
        from rest_framework.test import APIRequestFactory
        from apps.users.throttles import SignupRateThrottle
        from apps.users.views import SelfSignupView

        cache.clear()
        factory = APIRequestFactory()
        view = SelfSignupView.as_view()

        def signup(email):
            request = factory.post(
                reverse('self-signup'),
                {
                    'organization_name': 'Acme Consulting',
                    'email': email,
                    'password': 'StrongPass123!',
                    'confirm_password': 'StrongPass123!',
                },
                format='json',
            )
            return view(request)

        with patch.object(SignupRateThrottle, 'get_rate', return_value='1/min'):
            first = signup('first@acme.test')
            self.assertIn(first.status_code, (status.HTTP_202_ACCEPTED, status.HTTP_400_BAD_REQUEST))
            second = signup('second@acme.test')
            self.assertEqual(second.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


@override_settings(**LOCMEM_EMAIL, TURNSTILE_SECRET_KEY='')
class VerifyEmailViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='founder', email='founder@acme.test', password='StrongPass123!', is_active=False,
        )
        self.invitation = UserInvitation.objects.create(
            email='founder@acme.test',
            role='manager',
            signup_source='self_service',
            organization_name='Acme Consulting',
            expires_at=timezone.now() + timedelta(hours=48),
        )

    def test_verify_activates_user_and_creates_tenant_with_trial(self):
        response = self.client.post(reverse('verify-email'), {'token': str(self.invitation.token)}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

        tenant = Tenant.objects.get(id=response.data['tenant_id'])
        self.assertEqual(tenant.name, 'Acme Consulting')
        self.assertEqual(tenant.status, 'trialing')
        self.assertIsNotNone(tenant.trial_ends_at)
        expected = timezone.now() + timedelta(days=15)
        self.assertAlmostEqual(tenant.trial_ends_at, expected, delta=timedelta(minutes=5))

        membership = TenantMembership.objects.get(tenant=tenant, user=self.user)
        self.assertEqual(membership.role, 'owner')
        self.assertTrue(hasattr(tenant, 'profile'))
        self.assertTrue(hasattr(tenant, 'strategy'))
        self.assertTrue(hasattr(tenant, 'intelligence_profile'))

        self.invitation.refresh_from_db()
        self.assertTrue(self.invitation.is_used)
        self.assertIsNotNone(self.invitation.accepted_at)

        # Assisted-beta tenants created without trial_days keep trial_ends_at=None,
        # so a 15-day trial here must not be a global default.
        from apps.tenants.services import create_tenant_with_owner
        assisted_owner = User.objects.create_user(username='assisted', email='assisted@x.test', password='x')
        assisted_tenant = create_tenant_with_owner('Assisted Client', assisted_owner)
        self.assertIsNone(assisted_tenant.trial_ends_at)

    def test_verify_rejects_expired_token(self):
        self.invitation.expires_at = timezone.now() - timedelta(hours=1)
        self.invitation.save(update_fields=['expires_at'])

        response = self.client.post(reverse('verify-email'), {'token': str(self.invitation.token)}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_verify_rejects_already_used_token(self):
        self.invitation.is_used = True
        self.invitation.save(update_fields=['is_used'])

        response = self.client.post(reverse('verify-email'), {'token': str(self.invitation.token)}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_rejects_admin_invite_token(self):
        admin_invitation = UserInvitation.create_for(
            email='other@example.com', role='consultant', invited_by=None,
        )
        response = self.client.post(
            reverse('verify-email'), {'token': str(admin_invitation.token)}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_rejects_unknown_token(self):
        response = self.client.post(
            reverse('verify-email'), {'token': '00000000-0000-0000-0000-000000000000'}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_rolls_back_when_tenant_provisioning_fails(self):
        with patch(
            'apps.tenants.services.create_tenant_with_owner',
            side_effect=RuntimeError('provisioning failed'),
        ):
            with self.assertRaises(RuntimeError):
                self.client.post(
                    reverse('verify-email'),
                    {'token': str(self.invitation.token)},
                    format='json',
                )

        self.user.refresh_from_db()
        self.invitation.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertFalse(self.invitation.is_used)
        self.assertFalse(Tenant.objects.filter(name='Acme Consulting').exists())
