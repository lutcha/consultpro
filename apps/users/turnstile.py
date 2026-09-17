import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

VERIFY_URL = 'https://challenges.cloudflare.com/turnstile/v0/siteverify'


def verify_turnstile_token(token: str, remote_ip: str | None = None) -> bool:
    """
    Verifies a Cloudflare Turnstile token server-side.

    When TURNSTILE_SECRET_KEY is not configured (local/test environments),
    verification is skipped and this returns True — signup stays usable
    without provisioning a Cloudflare account for every dev/CI run.

    Once a secret key is configured (production), this fails closed: any
    missing token, Cloudflare API error, or network failure returns False
    rather than letting the request through unverified.
    """
    secret_key = getattr(settings, 'TURNSTILE_SECRET_KEY', '')
    if not secret_key:
        return True

    if not token:
        return False

    payload = {'secret': secret_key, 'response': token}
    if remote_ip:
        payload['remoteip'] = remote_ip

    try:
        response = requests.post(VERIFY_URL, data=payload, timeout=5)
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError):
        logger.exception('Turnstile verification request failed')
        return False

    return bool(data.get('success'))
