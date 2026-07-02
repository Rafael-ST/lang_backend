from rest_framework import filters, viewsets
from rest_framework.permissions import IsAuthenticated

from exercicio.filters import ExerciseFilterBackend
from exercicio.models import Exercise
from exercicio.serializers import ExerciseSerializer


class ExerciseViewSet(viewsets.ModelViewSet):
    queryset = Exercise.objects.select_related('card').all().order_by('order', 'id')
    serializer_class = ExerciseSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [
        ExerciseFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ['card__english_name', 'card__international_name', 'type']
    ordering_fields = ['order', 'difficulty', 'type', 'created_at', 'updated_at', 'is_active']
    ordering = ['order', 'id']
