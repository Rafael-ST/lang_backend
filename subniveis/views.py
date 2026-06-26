from rest_framework import filters, viewsets

from subniveis.filters import SubNivelFilterBackend
from subniveis.models import SubNivel
from subniveis.serializers import SubNivelSerializer
from rest_framework.permissions import IsAuthenticated

class SubNivelViewSet(viewsets.ModelViewSet):
    queryset = SubNivel.objects.select_related('subnivel').all().order_by('ordem', 'nome')
    permission_classes = [IsAuthenticated]
    serializer_class = SubNivelSerializer
    filter_backends = [
        SubNivelFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ['nome', 'subnivel__nome']
    ordering_fields = ['nome', 'ordem', 'subnivel__nome', 'created_at', 'updated_at', 'is_active']
    ordering = ['ordem', 'nome']
