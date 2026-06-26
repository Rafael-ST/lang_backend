from rest_framework import filters, viewsets

from niveis.filters import NivelFilterBackend
from niveis.models import Nivel
from niveis.serializers import NivelSerializer


class NivelViewSet(viewsets.ModelViewSet):
    queryset = Nivel.objects.all().order_by('nome')
    serializer_class = NivelSerializer
    filter_backends = [
        NivelFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ['nome']
    ordering_fields = ['nome', 'created_at', 'updated_at', 'is_active']
    ordering = ['nome']
