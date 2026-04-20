from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response

from apps.core.permissions import IsConsultantOrManager, IsManager

from .models import Project, ProjectTeamMember, ProjectMilestone, ProjectRisk, ProjectDeliverable
from .serializers import (
    ProjectListSerializer,
    ProjectDetailSerializer,
    ProjectTeamMemberSerializer,
    ProjectMilestoneSerializer,
    ProjectRiskSerializer,
    ProjectDeliverableSerializer,
)


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

    def get_permissions(self):
        if self.action in ['create', 'destroy', 'update', 'partial_update']:
            permission_classes = [IsManager]
        else:
            permission_classes = [IsConsultantOrManager]
        return [permission() for permission in permission_classes]

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        project = self.get_object()
        project.status = Project.Status.ACTIVE
        project.save(update_fields=['status'])
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
        total = Project.objects.count()
        active = Project.objects.filter(status=Project.Status.ACTIVE).count()
        planning = Project.objects.filter(status=Project.Status.PLANNING).count()
        completed = Project.objects.filter(status=Project.Status.COMPLETED).count()
        on_hold = Project.objects.filter(status=Project.Status.ON_HOLD).count()
        overdue = sum(1 for p in Project.objects.all() if p.is_overdue)

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


class ProjectMilestoneViewSet(viewsets.ModelViewSet):
    queryset = ProjectMilestone.objects.all()
    serializer_class = ProjectMilestoneSerializer
    permission_classes = [IsConsultantOrManager]
    filterset_fields = ['project', 'status']


class ProjectRiskViewSet(viewsets.ModelViewSet):
    queryset = ProjectRisk.objects.all()
    serializer_class = ProjectRiskSerializer
    permission_classes = [IsConsultantOrManager]
    filterset_fields = ['project', 'severity', 'status']


class ProjectDeliverableViewSet(viewsets.ModelViewSet):
    queryset = ProjectDeliverable.objects.all()
    serializer_class = ProjectDeliverableSerializer
    permission_classes = [IsConsultantOrManager]
    filterset_fields = ['project', 'status']
