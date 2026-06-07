from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response

from apps.core.permissions import IsConsultantOrManager, IsManager
from apps.tenants.utils import get_request_tenant, scope_queryset_to_request_tenant

from .models import (
    Project,
    ProjectTeamMember,
    ProjectMilestone,
    ProjectTask,
    ProjectRisk,
    ProjectDeliverable,
    ProjectPhase,
    ProjectArtifact,
)
from .serializers import (
    ProjectListSerializer,
    ProjectDetailSerializer,
    ProjectTeamMemberSerializer,
    ProjectMilestoneSerializer,
    ProjectTaskSerializer,
    ProjectRiskSerializer,
    ProjectDeliverableSerializer,
    ProjectPhaseSerializer,
    ProjectArtifactSerializer,
)


def _scope_project_child_queryset(queryset, request):
    tenant = get_request_tenant(request)
    if tenant is not None:
        return queryset.filter(project__tenant=tenant)
    return queryset


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'client', 'sector', 'country', 'risk_level', 'manager']
    search_fields = ['title', 'description', 'client']
    ordering_fields = ['start_date', 'end_date', 'created_at', 'progress']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return ProjectListSerializer
        return ProjectDetailSerializer

    def get_queryset(self):
        return scope_queryset_to_request_tenant(super().get_queryset(), self.request)

    def get_permissions(self):
        if self.action in ['create', 'destroy', 'update', 'partial_update']:
            permission_classes = [IsManager]
        else:
            permission_classes = [IsConsultantOrManager]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        tenant = get_request_tenant(self.request)
        tenant_kwargs = {'tenant': tenant} if tenant else {}
        if serializer.validated_data.get('manager') is None:
            serializer.save(manager=self.request.user, **tenant_kwargs)
        else:
            serializer.save(**tenant_kwargs)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        project = Project.objects.get(pk=response.data['id'])
        # Auto-create PMI phases
        phases = [
            ('initiating', 0),
            ('planning', 1),
            ('executing', 2),
            ('monitoring', 3),
            ('closing', 4),
        ]
        for name, order in phases:
            ProjectPhase.objects.get_or_create(
                project=project,
                name=name,
                defaults={'order': order},
            )
        return response

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        project = self.get_object()
        project.status = Project.Status.ACTIVE
        update_fields = ['status']
        if not project.start_date:
            project.start_date = timezone.localdate()
            update_fields.append('start_date')
        project.save(update_fields=update_fields)
        return Response({'status': 'active'})

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        project = self.get_object()
        project.status = Project.Status.COMPLETED
        project.save(update_fields=['status'])
        return Response({'status': 'completed'})

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        project = self.get_object()
        project.status = Project.Status.CLOSED
        project.save(update_fields=['status'])
        return Response({'status': 'closed'})

    @action(detail=True, methods=['post'])
    def hold(self, request, pk=None):
        project = self.get_object()
        project.status = Project.Status.ON_HOLD
        project.save(update_fields=['status'])
        return Response({'status': 'on_hold'})

    @action(detail=True, methods=['post'])
    def add_team_member(self, request, pk=None):
        project = self.get_object()
        data = {**request.data, 'project': project.id}
        serializer = ProjectTeamMemberSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get', 'post'])
    def milestones(self, request, pk=None):
        project = self.get_object()
        if request.method == 'GET':
            queryset = project.milestones.all()
            serializer = ProjectMilestoneSerializer(queryset, many=True)
            return Response(serializer.data)
        serializer = ProjectMilestoneSerializer(data={**request.data, 'project': project.id})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get', 'post'])
    def risks(self, request, pk=None):
        project = self.get_object()
        if request.method == 'GET':
            queryset = project.project_risks.all()
            serializer = ProjectRiskSerializer(queryset, many=True)
            return Response(serializer.data)
        serializer = ProjectRiskSerializer(data={**request.data, 'project': project.id})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get', 'post'])
    def deliverables(self, request, pk=None):
        project = self.get_object()
        if request.method == 'GET':
            queryset = project.project_deliverables.all()
            serializer = ProjectDeliverableSerializer(queryset, many=True)
            return Response(serializer.data)
        serializer = ProjectDeliverableSerializer(data={**request.data, 'project': project.id})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        from django.db.models import Count, Q
        queryset = self.get_queryset()
        total = queryset.count()
        active = queryset.filter(status=Project.Status.ACTIVE).count()
        planning = queryset.filter(status=Project.Status.PLANNING).count()
        completed = queryset.filter(status=Project.Status.COMPLETED).count()
        on_hold = queryset.filter(status=Project.Status.ON_HOLD).count()
        overdue = sum(1 for p in queryset if p.is_overdue)

        return Response({
            'total_projects': total,
            'active_projects': active,
            'planning_projects': planning,
            'completed_projects': completed,
            'on_hold_projects': on_hold,
            'overdue_projects': overdue,
        })


class ProjectTeamMemberViewSet(viewsets.ModelViewSet):
    queryset = ProjectTeamMember.objects.all()
    serializer_class = ProjectTeamMemberSerializer
    permission_classes = [IsConsultantOrManager]

    def get_queryset(self):
        return _scope_project_child_queryset(super().get_queryset(), self.request)


class ProjectMilestoneViewSet(viewsets.ModelViewSet):
    queryset = ProjectMilestone.objects.all()
    serializer_class = ProjectMilestoneSerializer
    permission_classes = [IsConsultantOrManager]
    filterset_fields = ['project', 'status']

    def get_queryset(self):
        return _scope_project_child_queryset(super().get_queryset(), self.request)

    def perform_create(self, serializer):
        milestone = serializer.save()
        self._sync_completed_date(milestone)

    def perform_update(self, serializer):
        milestone = serializer.save()
        self._sync_completed_date(milestone)

    def _sync_completed_date(self, milestone):
        if milestone.status == ProjectMilestone.Status.COMPLETED and not milestone.completed_date:
            milestone.completed_date = timezone.localdate()
            milestone.save(update_fields=['completed_date', 'updated_at'])
        elif milestone.status != ProjectMilestone.Status.COMPLETED and milestone.completed_date:
            milestone.completed_date = None
            milestone.save(update_fields=['completed_date', 'updated_at'])


class ProjectTaskViewSet(viewsets.ModelViewSet):
    queryset = ProjectTask.objects.all()
    serializer_class = ProjectTaskSerializer
    permission_classes = [IsConsultantOrManager]
    filterset_fields = ['project', 'status', 'priority', 'assignee']

    def get_queryset(self):
        return _scope_project_child_queryset(super().get_queryset(), self.request)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ProjectRiskViewSet(viewsets.ModelViewSet):
    queryset = ProjectRisk.objects.all()
    serializer_class = ProjectRiskSerializer
    permission_classes = [IsConsultantOrManager]
    filterset_fields = ['project', 'severity', 'status']

    def get_queryset(self):
        return _scope_project_child_queryset(super().get_queryset(), self.request)


class ProjectDeliverableViewSet(viewsets.ModelViewSet):
    queryset = ProjectDeliverable.objects.select_related('phase').all()
    serializer_class = ProjectDeliverableSerializer
    permission_classes = [IsConsultantOrManager]
    filterset_fields = ['project', 'phase', 'status']

    def get_queryset(self):
        return _scope_project_child_queryset(super().get_queryset(), self.request)


class ProjectArtifactViewSet(viewsets.ModelViewSet):
    queryset = ProjectArtifact.objects.all()
    serializer_class = ProjectArtifactSerializer
    permission_classes = [IsConsultantOrManager]
    filterset_fields = ['project', 'phase', 'artifact_type', 'status']

    def get_queryset(self):
        return _scope_project_child_queryset(super().get_queryset(), self.request)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ProjectPhaseViewSet(viewsets.ModelViewSet):
    queryset = ProjectPhase.objects.all()
    serializer_class = ProjectPhaseSerializer
    permission_classes = [IsConsultantOrManager]
    filterset_fields = ['project', 'name', 'is_completed']

    def get_queryset(self):
        return _scope_project_child_queryset(super().get_queryset(), self.request)

    def perform_update(self, serializer):
        phase = serializer.save()
        update_fields = []
        if phase.is_completed and phase.completion_percentage < 100:
            phase.completion_percentage = 100
            update_fields.append('completion_percentage')
        elif phase.completion_percentage >= 100 and not phase.is_completed:
            phase.is_completed = True
            update_fields.append('is_completed')
        if update_fields:
            phase.save(update_fields=update_fields + ['updated_at'])

        phases = list(phase.project.phases.all())
        if phases:
            phase.project.progress = int(
                sum(p.completion_percentage for p in phases) / len(phases)
            )
            phase.project.save(update_fields=['progress', 'updated_at'])
