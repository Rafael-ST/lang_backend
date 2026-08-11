from rest_framework import filters, viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticated

from categorias.filters import CategoriaFilterBackend
from categorias.models import Categoria
from categorias.serializers import CategoriaSerializer


class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all().order_by('nome')
    serializer_class = CategoriaSerializer
    filter_backends = [
        CategoriaFilterBackend,
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
