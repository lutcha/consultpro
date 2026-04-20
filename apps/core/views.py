from django.utils import timezone
from django.db.models import Count, Q
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.permissions import IsConsultantOrManager
from apps.opportunities.models import Opportunity
from apps.proposals.models import Proposal
from apps.notifications.models import Notification, ActivityLog


class DashboardViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated, IsConsultantOrManager]

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        active_opportunities = Opportunity.objects.filter(
            status__in=['new', 'analyzing', 'go', 'proposal_draft', 'proposal_review']
        ).count()
        proposals_in_progress = Proposal.objects.filter(
            status__in=['draft', 'in_review', 'qc_check']
        ).count()
        won_proposals = Proposal.objects.filter(status='won').count()
        total_submitted = Proposal.objects.filter(
            status__in=['submitted', 'won', 'lost']
        ).count()
        win_rate = int((won_proposals / total_submitted) * 100) if total_submitted > 0 else 0
        upcoming_deadlines = Opportunity.objects.filter(
            deadline__lte=timezone.now() + timezone.timedelta(days=7),
            status__in=['new', 'analyzing', 'go', 'proposal_draft']
        ).count()

        data = {
            'active_opportunities': active_opportunities,
            'proposals_in_progress': proposals_in_progress,
            'win_rate': win_rate,
            'upcoming_deadlines': upcoming_deadlines,
        }
        return Response(data)

    @action(detail=False, methods=['get'], url_path='pipeline')
    def pipeline(self, request):
        proposals = Proposal.objects.filter(
            status__in=['draft', 'in_review', 'qc_check', 'approved']
        ).select_related('opportunity')

        data = []
        for prop in proposals:
            total = prop.sections.count()
            complete = prop.sections.filter(is_complete=True).count()
            progress = int((complete / total) * 100) if total > 0 else 0
            data.append({
                'id': prop.id,
                'title': prop.title,
                'client': prop.opportunity.client if prop.opportunity else '',
                'deadline': prop.opportunity.deadline.isoformat() if prop.opportunity and prop.opportunity.deadline else None,
                'status': prop.status,
                'value': float(prop.opportunity.value) if prop.opportunity else 0,
                'progress': progress,
            })
        return Response(data)

    @action(detail=False, methods=['get'], url_path='alerts')
    def alerts(self, request):
        notifications = Notification.objects.filter(
            user=request.user, read=False
        )[:10]

        data = []
        for notif in notifications:
            alert = {
                'id': str(notif.id),
                'type': notif.type,
                'message': notif.message,
            }
            if notif.action_label and notif.action_url:
                alert['action'] = {
                    'label': notif.action_label,
                    'href': notif.action_url,
                }
            data.append(alert)
        return Response(data)

    @action(detail=False, methods=['get'], url_path='activity')
    def activity(self, request):
        logs = ActivityLog.objects.select_related('user')[:20]

        data = []
        for log in logs:
            user_data = None
            if log.user:
                user_data = {
                    'id': str(log.user.id),
                    'name': f"{log.user.first_name} {log.user.last_name}",
                    'email': log.user.email,
                    'avatar': log.user.avatar.url if log.user.avatar else None,
                    'role': log.user.role,
                    'skills': log.user.skills,
                    'availability': log.user.availability,
                    'languages': log.user.languages,
                }
            data.append({
                'id': str(log.id),
                'type': log.type,
                'user': user_data,
                'description': log.description,
                'timestamp': log.created_at.isoformat(),
                'metadata': log.metadata,
            })
        return Response(data)
