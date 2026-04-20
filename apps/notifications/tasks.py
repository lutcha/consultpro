from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from apps.opportunities.models import Opportunity
from apps.users.models import User

from .models import ActivityLog, Notification


@shared_task
def send_notification(
    user_id,
    type,
    title,
    message,
    action_label='',
    action_url='',
):
    user = User.objects.filter(pk=user_id).first()
    if not user:
        return None
    notification = Notification.objects.create(
        user=user,
        type=type,
        title=title,
        message=message,
        action_label=action_label,
        action_url=action_url,
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
