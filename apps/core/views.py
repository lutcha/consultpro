from django.utils import timezone
from django.db.models import Count, Q, Sum
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.permissions import IsConsultantOrManager
from apps.opportunities.models import Opportunity
from apps.proposals.models import Proposal
from apps.projects.models import Project
from apps.notifications.models import Notification, ActivityLog
from apps.scraping.models import ScrapedOpportunity


class DashboardViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated, IsConsultantOrManager]

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        now = timezone.now()
        deadline_cutoff = now + timezone.timedelta(days=7)

        active_opps = Opportunity.objects.filter(
            status__in=['new', 'analyzing', 'go', 'proposal_draft', 'proposal_review']
        )
        proposals_in_progress = Proposal.objects.filter(
            status__in=['draft', 'in_review', 'qc_check']
        ).count()
        won_proposals = Proposal.objects.filter(status='won').count()
        total_submitted = Proposal.objects.filter(
            status__in=['submitted', 'won', 'lost']
        ).count()
        win_rate = int((won_proposals / total_submitted) * 100) if total_submitted > 0 else 0

        upcoming_qs = Opportunity.objects.filter(
            deadline__lte=deadline_cutoff,
            deadline__gte=now,
            status__in=['new', 'analyzing', 'go', 'proposal_draft'],
        ).order_by('deadline')
        upcoming_deadlines = upcoming_qs.count()

        # Breakdown by status
        status_breakdown = {
            row['status']: row['total']
            for row in Opportunity.objects.values('status').annotate(total=Count('id'))
        }

        # Project stats
        project_stats = {
            row['status']: row['total']
            for row in Project.objects.values('status').annotate(total=Count('id'))
        }

        # Scraping — new items not yet imported
        scraping_new = ScrapedOpportunity.objects.filter(status='new').count()
        scraping_with_ai = ScrapedOpportunity.objects.filter(
            status='new', ai_summary__gt=''
        ).count()

        # Upcoming deadline items (for list widget)
        deadline_items = [
            {
                'id': opp.id,
                'title': opp.title,
                'client': opp.client,
                'deadline': opp.deadline.isoformat(),
                'status': opp.status,
                'days_left': max(0, (opp.deadline - now).days),
            }
            for opp in upcoming_qs[:10]
        ]

        data = {
            'active_opportunities': active_opps.count(),
            'proposals_in_progress': proposals_in_progress,
            'win_rate': win_rate,
            'upcoming_deadlines': upcoming_deadlines,
            'opportunities_by_status': status_breakdown,
            'projects_active': project_stats.get('active', 0),
            'projects_completed': project_stats.get('completed', 0),
            'projects_on_hold': project_stats.get('on_hold', 0),
            'scraping_new': scraping_new,
            'scraping_with_ai': scraping_with_ai,
            'deadline_items': deadline_items,
        }
        return Response(data)

    @action(detail=False, methods=['get'], url_path='pipeline')
    def pipeline(self, request):
        opportunities = Opportunity.objects.filter(
            status__in=['new', 'analyzing', 'go', 'proposal_draft', 'proposal_review']
        ).order_by('-created_at')[:20]
        proposals = Proposal.objects.filter(
            status__in=['draft', 'in_review', 'qc_check', 'approved']
        ).select_related('opportunity')

        data = []
        for opp in opportunities:
            data.append({
                'id': f'opportunity-{opp.id}',
                'title': opp.title,
                'client': opp.client,
                'deadline': opp.deadline.isoformat() if opp.deadline else None,
                'status': opp.status,
                'value': float(opp.value),
                'progress': 0,
            })
        for prop in proposals:
            total = prop.sections.count()
            complete = prop.sections.filter(is_complete=True).count()
            progress = int((complete / total) * 100) if total > 0 else 0
            data.append({
                'id': f'proposal-{prop.id}',
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
