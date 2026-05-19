from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.permissions import IsConsultantOrManager

from .models import ComplianceMatrix, ComplianceMatrixRow
from .serializers import ComplianceMatrixRowSerializer, ComplianceMatrixSerializer
from .services import generate_compliance_matrix


class ComplianceMatrixViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ComplianceMatrixSerializer
    permission_classes = [IsConsultantOrManager]

    def get_queryset(self):
        queryset = ComplianceMatrix.objects.select_related('opportunity', 'generated_by').prefetch_related(
            'rows',
            'rows__proposal_section',
        )
        opportunity_id = self.request.query_params.get('opportunity')
        if opportunity_id:
            queryset = queryset.filter(opportunity_id=opportunity_id)
        return queryset

    @action(detail=False, methods=['post'])
    def generate(self, request):
        opportunity_id = request.data.get('opportunity_id') or request.data.get('opportunity')
        if not opportunity_id:
            return Response({'detail': 'opportunity_id is required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            matrix = generate_compliance_matrix(int(opportunity_id), generated_by=request.user)
        except (TypeError, ValueError):
            return Response({'detail': 'opportunity_id must be a valid integer.'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(matrix)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ComplianceMatrixRowViewSet(viewsets.ModelViewSet):
    serializer_class = ComplianceMatrixRowSerializer
    permission_classes = [IsConsultantOrManager]
    http_method_names = ['get', 'patch', 'head', 'options']

    def get_queryset(self):
        queryset = ComplianceMatrixRow.objects.select_related(
            'matrix',
            'matrix__opportunity',
            'proposal_section',
        )
        matrix_id = self.request.query_params.get('matrix')
        if matrix_id:
            queryset = queryset.filter(matrix_id=matrix_id)
        return queryset

    def perform_update(self, serializer):
        row = serializer.save(human_override=True)
        matrix = row.matrix
        matrix.human_override_count = matrix.rows.filter(human_override=True).count()
        matrix.save(update_fields=['human_override_count', 'updated_at'])
