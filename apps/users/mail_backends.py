import requests
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend


class SendGridAPIBackend(BaseEmailBackend):
    """Sends email via SendGrid's HTTPS Web API v3 instead of raw SMTP.

    DigitalOcean App Platform drops outbound SMTP connections (port 587) mid
    AUTH handshake, so the standard Django SMTP backend cannot deliver mail
    from this deployment target even with valid credentials. The HTTPS API
    uses the same SendGrid API key and is not affected by that restriction.
    """

    api_url = 'https://api.sendgrid.com/v3/mail/send'

    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        api_key = str(getattr(settings, 'SENDGRID_API_KEY', ''))
        if not api_key:
            if self.fail_silently:
                return 0
            raise OSError('SENDGRID_API_KEY is not configured.')

        sent_count = 0
        for message in email_messages:
            try:
                response = requests.post(
                    self.api_url,
                    json=self._build_payload(message),
                    headers={'Authorization': f'Bearer {api_key}'},
                    timeout=getattr(settings, 'EMAIL_TIMEOUT', 15),
                )
                response.raise_for_status()
            except requests.RequestException as exc:
                if self.fail_silently:
                    continue
                raise OSError(f'SendGrid API request failed: {exc}') from exc
            sent_count += 1
        return sent_count

    @staticmethod
    def _build_payload(message):
        return {
            'personalizations': [{'to': [{'email': addr} for addr in message.to]}],
            'from': {'email': message.from_email},
            'subject': message.subject,
            'content': [{'type': 'text/plain', 'value': message.body}],
        }
