from rest_framework import viewsets

from apps.core.permissions import IsConsultantOrManager

from .models import Team
from .serializers import TeamSerializer


class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = [IsConsultantOrManager]
