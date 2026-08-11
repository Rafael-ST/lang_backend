from django.db import transaction
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from perfil.models import Perfil
from perfil.serializers import PerfilSerializer
from perfil.services import recover_profile_points_for_user


class PerfilViewSet(viewsets.ReadOnlyModelViewSet):
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

    def list(self, request, *args, **kwargs):
        if not request.user.is_staff:
            recover_profile_points_for_user(request.user)

        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        if not request.user.is_staff:
            recover_profile_points_for_user(request.user)

        return super().retrieve(request, *args, **kwargs)

    @action(detail=True, methods=['post'], url_path='spend-point')
    def spend_point(self, request, pk=None):
        with transaction.atomic():
            profile = self.get_queryset().select_for_update().get(pk=pk)

            if profile.pontos <= 0:
                return Response(
                    {'detail': 'Voce nao possui pontos disponiveis.'},
                    status=status.HTTP_409_CONFLICT,
                )

            profile.pontos -= 1
            profile.save(update_fields=['pontos', 'updated_at'])

        return Response(self.get_serializer(profile).data)
