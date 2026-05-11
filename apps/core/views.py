from django.utils import timezone
from django.db.models import Count, Q, Sum, DecimalField
from django.db.models.functions import Coalesce
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.permissions import IsConsultantOrManager
from apps.opportunities.models import Opportunity
from apps.proposals.models import Proposal, Budget, BudgetItem
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

    @action(detail=False, methods=['get'], url_path='funnel')
    def funnel(self, request):
        """
        Conversion funnel: Opportunities → Proposals → Projects
        plus financial summary (pipeline value, proposals value,
        portfolio in execution, personnel costs, estimated margin).
        """
        zero = Coalesce(Sum('value', output_field=DecimalField()), 0, output_field=DecimalField())

        # ── Stage counts ──────────────────────────────────────────────────────
        active_statuses = ['new', 'analyzing', 'go', 'proposal_draft', 'proposal_review']
        opp_active = Opportunity.objects.filter(status__in=active_statuses)
        opp_count = opp_active.count()

        submitted_statuses = ['submitted', 'under_evaluation', 'shortlisted',
                              'clarifications_requested', 'bafo', 'awarded',
                              'contract_negotiation', 'contract_signed',
                              'project_initiation', 'won', 'lost']
        proposals_submitted = Proposal.objects.filter(status__in=submitted_statuses).count()
        proposals_won       = Proposal.objects.filter(status__in=['won', 'awarded', 'contract_signed']).count()
        proposals_total     = Proposal.objects.count()

        projects_active    = Project.objects.filter(status=Project.Status.ACTIVE).count()
        projects_planning  = Project.objects.filter(status=Project.Status.PLANNING).count()
        projects_total     = Project.objects.count()

        # ── Conversion rates ─────────────────────────────────────────────────
        opp_to_proposal = round(proposals_submitted / opp_count * 100) if opp_count else 0
        proposal_to_project = round(projects_total / proposals_total * 100) if proposals_total else 0

        # ── Financial pipeline (opportunities selected / go stage) ───────────
        pipeline_value = float(
            opp_active.filter(status__in=['go', 'proposal_draft', 'proposal_review'])
            .aggregate(total=zero)['total']
        )

        # ── Proposals value: sum of Budget.total for submitted proposals ──────
        submitted_budget_qs = Budget.objects.filter(
            proposal__status__in=submitted_statuses
        ).aggregate(total=Coalesce(Sum('total', output_field=DecimalField()), 0, output_field=DecimalField()))
        proposals_value = float(submitted_budget_qs['total'])

        # ── Portfolio in execution: sum of Project.budget_total (active) ─────
        portfolio_value = float(
            Project.objects.filter(status=Project.Status.ACTIVE)
            .aggregate(total=Coalesce(Sum('budget_total', output_field=DecimalField()), 0, output_field=DecimalField()))['total']
        )

        # ── Personnel costs: BudgetItem category=personnel for active projects ─
        personnel_costs = float(
            BudgetItem.objects.filter(
                category='personnel',
                budget__proposal__status__in=['won', 'awarded', 'contract_signed', 'project_initiation'],
            ).aggregate(total=Coalesce(Sum('amount', output_field=DecimalField()), 0, output_field=DecimalField()))['total']
        )

        estimated_margin = portfolio_value - personnel_costs

        return Response({
            'funnel': {
                'opportunities': {'count': opp_count,          'label': 'Oportunidades Ativas'},
                'proposals':     {'count': proposals_submitted, 'label': 'Propostas Submetidas', 'won': proposals_won},
                'projects':      {'count': projects_active + projects_planning, 'label': 'Projetos em Carteira', 'active': projects_active},
            },
            'conversion': {
                'opp_to_proposal':   opp_to_proposal,
                'proposal_to_project': proposal_to_project,
            },
            'financial': {
                'pipeline_value':   pipeline_value,
                'proposals_value':  proposals_value,
                'portfolio_value':  portfolio_value,
                'personnel_costs':  personnel_costs,
                'estimated_margin': estimated_margin,
                'currency':         'USD',
            },
        })

    @action(detail=False, methods=['post'], url_path='seed')
    def seed(self, request):
        """
        Seed initial data for testing.
        Only available for superusers.
        """
        if not request.user.is_superuser:
            return Response(
                {'error': 'Apenas superusers podem executar esta ação.'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            from django.core.management import call_command
            call_command('loaddata', 'initial_data.json')
            return Response({'status': 'ok', 'message': 'Seed data carregado com sucesso.'})
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
