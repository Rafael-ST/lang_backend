from rest_framework import filters, viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticated

from niveis.filters import NivelFilterBackend
from niveis.models import Nivel
from niveis.serializers import NivelSerializer


class NivelViewSet(viewsets.ModelViewSet):
    queryset = Nivel.objects.all().order_by('nome')
    permission_classes = [IsAuthenticated]
    serializer_class = NivelSerializer
    filter_backends = [
        NivelFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ['nome']
    ordering_fields = ['nome', 'created_at', 'updated_at', 'is_active']
    ordering = ['nome']

    def get_permissions(self):
        if self.action in {'create', 'update', 'partial_update', 'destroy'}:
            return [IsAdminUser()]
        return [IsAuthenticated()]
