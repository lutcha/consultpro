from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from apps.opportunities.models import Opportunity
from apps.users.models import User

from .models import ActivityLog, Notification, NotificationPreference


EMAIL_CATEGORY_FIELDS = {
    'new_opportunity': 'email_on_new_opportunity',
    'proposal_status': 'email_on_proposal_status',
    'scrape_complete': 'email_on_scrape_complete',
}


def _email_enabled(user, email_category):
    if email_category not in EMAIL_CATEGORY_FIELDS:
        return False
    preferences, _ = NotificationPreference.objects.get_or_create(user=user)
    return getattr(preferences, EMAIL_CATEGORY_FIELDS[email_category])


@shared_task
def send_notification(
    user_id,
    type,
    title,
    message,
    action_label='',
    action_url='',
    email_category=None,
    tenant_id=None,
):
    user = User.objects.filter(pk=user_id).first()
    if not user:
        return None
    notification = Notification.objects.create(
        user=user,
        tenant_id=tenant_id,
        type=type,
        title=title,
        message=message,
        action_label=action_label,
        action_url=action_url,
    )
    if user.email and _email_enabled(user, email_category):
        send_mail(
            subject=title,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
    return notification.id


@shared_task
def log_activity(user_id, activity_type, description, metadata=None):
    if metadata is None:
        metadata = {}
    user = User.objects.filter(pk=user_id).first()
    activity = ActivityLog.objects.create(
        user=user,
        type=activity_type,
        description=description,
        metadata=metadata,
    )
    return activity.id


@shared_task
def check_upcoming_deadlines():
    threshold = timezone.now() + timedelta(days=7)
    opportunities = Opportunity.objects.filter(
        deadline__lte=threshold,
        deadline__gte=timezone.now(),
    )
    created_count = 0
    for opportunity in opportunities:
        assigned_users = opportunity.assigned_to.all()
        if not assigned_users.exists() and opportunity.created_by:
            assigned_users = [opportunity.created_by]
        for user in assigned_users:
            _, created = Notification.objects.get_or_create(
                user=user,
                type='warning',
                title=f'Prazo aproximado: {opportunity.title}',
                message=(
                    f'A oportunidade "{opportunity.title}" '
                    f'tem prazo em {opportunity.deadline.strftime("%d/%m/%Y %H:%M")}.'
                ),
                defaults={
                    'action_label': 'Ver Oportunidade',
                    'action_url': f'/opportunities/{opportunity.id}/',
                },
            )
            if created:
                created_count += 1
    return created_count
