from rest_framework import filters, permissions, viewsets

from perfil.models import Perfil
from perfil.serializers import PerfilSerializer


class PerfilViewSet(viewsets.ModelViewSet):
    queryset = Perfil.objects.select_related('user').all().order_by('user__username')
    serializer_class = PerfilSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    ordering_fields = ['user__username', 'pontos', 'created_at', 'updated_at', 'is_active']
    ordering = ['user__username']

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.request.user.is_staff:
            return queryset

        return queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        if self.request.user.is_staff:
            serializer.save()
            return

        serializer.save(user=self.request.user)
