import logging
from smtplib import SMTPException

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


class EmailDeliveryError(RuntimeError):
    pass


def _frontend_url() -> str:
    return str(getattr(settings, 'FRONTEND_URL', 'https://consultpro.cv')).rstrip('/')


def _send(subject: str, message: str, recipients: list[str]) -> int:
    try:
        return send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            fail_silently=False,
        )
    except (SMTPException, OSError, TimeoutError) as exc:
        logger.exception('Email delivery failed to %s', recipients)
        raise EmailDeliveryError(str(exc)) from exc


def send_invitation_email(invitation) -> int:
    accept_url = f'{_frontend_url()}/accept-invitation/{invitation.token}/'
    invited_by_name = (
        f'{invitation.invited_by.first_name} {invitation.invited_by.last_name}'.strip()
        if invitation.invited_by
        else 'ConsultPro'
    )
    role_display = dict(invitation.ROLE_CHOICES).get(invitation.role, invitation.role)
    tenant_name = getattr(invitation.tenant, 'name', '') if invitation.tenant_id else ''
    tenant_line = f' para {tenant_name}' if tenant_name else ''
    subject = f'Convite para ConsultPro - {role_display}'
    message = (
        f'Ola,\n\n'
        f'{invited_by_name} convidou-te para a plataforma ConsultPro{tenant_line} como {role_display}.\n\n'
        f'Clica no link abaixo para activar a tua conta. O convite e valido por 7 dias:\n'
        f'{accept_url}\n\n'
        f'Se nao esperavas este convite, podes ignorar este email.\n\n'
        f'Equipa ConsultPro'
    )
    return _send(subject, message, [invitation.email])


def send_welcome_email(user) -> int:
    subject = 'Bem-vindo ao ConsultPro'
    message = (
        f'Ola {user.first_name or user.username},\n\n'
        f'A tua conta foi criada com sucesso na plataforma ConsultPro.\n\n'
        f'Podes iniciar sessao em: {_frontend_url()}\n\n'
        f'Equipa ConsultPro'
    )
    return _send(subject, message, [user.email])


def send_smtp_test_email(to_email: str) -> int:
    frontend = _frontend_url()
    subject = 'ConsultPro SMTP test'
    message = (
        'Este e um email de teste SMTP do ConsultPro.\n\n'
        f'FRONTEND_URL configurado: {frontend}\n'
        f'DEFAULT_FROM_EMAIL configurado: {settings.DEFAULT_FROM_EMAIL}\n'
    )
    return _send(subject, message, [to_email])

