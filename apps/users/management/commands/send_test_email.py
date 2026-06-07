from django.core.management.base import BaseCommand, CommandError

from apps.users.emails import (
    EmailConfigurationError,
    EmailDeliveryError,
    send_smtp_test_email,
    validate_smtp_configuration,
)


class Command(BaseCommand):
    help = 'Send a real SMTP test email using the configured Django email backend.'

    def add_arguments(self, parser):
        parser.add_argument('--to', required=True, help='Destination email address')

    def handle(self, *args, **options):
        try:
            validate_smtp_configuration()
        except EmailConfigurationError as exc:
            raise CommandError(str(exc)) from exc

        try:
            delivered = send_smtp_test_email(options['to'])
        except EmailDeliveryError as exc:
            raise CommandError(f'SMTP test email failed: {exc}') from exc

        if delivered != 1:
            raise CommandError(f'SMTP test email was not delivered; send_mail returned {delivered}.')

        self.stdout.write(self.style.SUCCESS(f'SMTP test email sent to {options["to"]}.'))

