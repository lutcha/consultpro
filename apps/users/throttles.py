from django.core.exceptions import ImproperlyConfigured
from rest_framework.throttling import AnonRateThrottle


class SignupRateThrottle(AnonRateThrottle):
    """
    Tighter-than-default throttle for the public self-service signup endpoint.

    config/settings/local.py wipes DEFAULT_THROTTLE_RATES to {} to keep local/CI
    runs free of throttling noise on every other viewset. That's the right
    default for internal/dev endpoints, but this one specifically exists to
    protect a scarce shared resource (outbound verification email) from
    unauthenticated abuse, so it keeps working even when the environment has
    otherwise disabled throttling.
    """
    scope = 'signup'
    DEFAULT_RATE = '5/hour'

    def get_rate(self):
        try:
            return super().get_rate()
        except ImproperlyConfigured:
            return self.DEFAULT_RATE
