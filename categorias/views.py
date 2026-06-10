from rest_framework import filters, viewsets

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
