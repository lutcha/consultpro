from django.db.models import Count
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.permissions import IsConsultantOrManager

from .models import IssueTreeNode, IssueTreeSnapshot
from .serializers import IssueTreeNodeSerializer, IssueTreeSnapshotSerializer
from .services import create_issue_tree_snapshot, generate_issue_tree


class IssueTreeNodeViewSet(viewsets.ModelViewSet):
    serializer_class = IssueTreeNodeSerializer
    permission_classes = [IsConsultantOrManager]

    def get_queryset(self):
        queryset = (
            IssueTreeNode.objects.select_related('proposal', 'parent', 'assigned_to', 'proposal_section', 'created_by')
            .annotate(children_count=Count('children'))
            .order_by('parent_id', 'order', 'id')
        )
        proposal_id = self.request.query_params.get('proposal')
        parent_id = self.request.query_params.get('parent')
        if proposal_id:
            queryset = queryset.filter(proposal_id=proposal_id)
        if parent_id == 'root':
            queryset = queryset.filter(parent__isnull=True)
        elif parent_id:
            queryset = queryset.filter(parent_id=parent_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['post'])
    def generate(self, request):
        proposal_id = request.data.get('proposal_id') or request.data.get('proposal')
        if not proposal_id:
            return Response({'detail': 'proposal_id is required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            root = generate_issue_tree(int(proposal_id), generated_by=request.user)
        except (TypeError, ValueError):
            return Response({'detail': 'proposal_id must be a valid integer.'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(root)
        return Response(serializer.data, status=status.HTTP_200_OK)


class IssueTreeSnapshotViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = IssueTreeSnapshotSerializer
    permission_classes = [IsConsultantOrManager]

    def get_queryset(self):
        queryset = IssueTreeSnapshot.objects.select_related('proposal', 'created_by')
        proposal_id = self.request.query_params.get('proposal')
        if proposal_id:
            queryset = queryset.filter(proposal_id=proposal_id)
        return queryset

    @action(detail=False, methods=['post'])
    def create_snapshot(self, request):
        proposal_id = request.data.get('proposal_id') or request.data.get('proposal')
        if not proposal_id:
            return Response({'detail': 'proposal_id is required.'}, status=status.HTTP_400_BAD_REQUEST)
        snapshot = create_issue_tree_snapshot(
            int(proposal_id),
            label=request.data.get('label', ''),
            created_by=request.user,
        )
        serializer = self.get_serializer(snapshot)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
