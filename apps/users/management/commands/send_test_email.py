from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.users.emails import EmailDeliveryError, send_smtp_test_email


class Command(BaseCommand):
    help = 'Send a real SMTP test email using the configured Django email backend.'

    def add_arguments(self, parser):
        parser.add_argument('--to', required=True, help='Destination email address')

    def handle(self, *args, **options):
        backend = getattr(settings, 'EMAIL_BACKEND', '')
        host = getattr(settings, 'EMAIL_HOST', '')
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', '')

        if 'console.EmailBackend' in backend:
            raise CommandError('EMAIL_BACKEND is console.EmailBackend; configure SMTP before beta validation.')
        if not host:
            raise CommandError('EMAIL_HOST is empty; configure SMTP provider host.')
        if not from_email:
            raise CommandError('DEFAULT_FROM_EMAIL is empty; configure a verified sender.')

        try:
            delivered = send_smtp_test_email(options['to'])
        except EmailDeliveryError as exc:
            raise CommandError(f'SMTP test email failed: {exc}') from exc

        if delivered != 1:
            raise CommandError(f'SMTP test email was not delivered; send_mail returned {delivered}.')

        self.stdout.write(self.style.SUCCESS(f'SMTP test email sent to {options["to"]}.'))

