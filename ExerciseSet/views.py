from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from ExerciseSet.filters import ExerciseSetFilterBackend, ExerciseSetProgressFilterBackend
from ExerciseSet.models import ExerciseSet, ExerciseSetImage, ExerciseSetProgress
from ExerciseSet.serializers import ExerciseSetImageSerializer, ExerciseSetProgressSerializer, ExerciseSetSerializer
from exercicio.models import ExerciseAttempt


class ExerciseSetViewSet(viewsets.ModelViewSet):
    queryset = ExerciseSet.objects.select_related('sublevel', 'image').prefetch_related('exercises', 'progresses').all().order_by('order', 'created_at')
    serializer_class = ExerciseSetSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [
        ExerciseSetFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ['title', 'description', 'sublevel__nome']
    ordering_fields = ['title', 'order', 'created_at', 'updated_at', 'is_active']
    ordering = ['order', 'created_at']

    def get_permissions(self):
        if self.action in {'create', 'update', 'partial_update', 'destroy'}:
            return [IsAdminUser()]

        return [IsAuthenticated()]


class ExerciseSetImageViewSet(viewsets.ModelViewSet):
    queryset = ExerciseSetImage.objects.all().order_by('name')
    serializer_class = ExerciseSetImageSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at', 'updated_at', 'is_active']
    ordering = ['name']

    @action(detail=True, methods=['post'], url_path='reset')
    def reset(self, request, pk=None):
        exercise_set = self.get_object()
        progress = ExerciseSetProgress.objects.filter(
            user=request.user,
            exercise_set=exercise_set,
        ).first()

        if progress and progress.status == ExerciseSetProgress.Status.COMPLETED:
            return Response(
                {
                    'reset': False,
                    'status': progress.status,
                    'detail': 'Conjunto ja concluido; progresso preservado.',
                },
                status=status.HTTP_200_OK,
            )

        deleted_attempts, _ = ExerciseAttempt.objects.filter(
            user=request.user,
            exercise_set=exercise_set,
        ).delete()

        if progress:
            progress.delete()

        return Response(
            {
                'reset': True,
                'deleted_attempts': deleted_attempts,
                'status': ExerciseSetProgress.Status.NOT_STARTED,
            },
            status=status.HTTP_200_OK,
        )


class ExerciseSetProgressViewSet(viewsets.ModelViewSet):
    serializer_class = ExerciseSetProgressSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [
        ExerciseSetProgressFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ['user__username', 'user__email', 'exercise_set__title', 'status']
    ordering_fields = ['status', 'completed_at', 'created_at', 'updated_at']
    ordering = ['created_at']

    def get_queryset(self):
        queryset = ExerciseSetProgress.objects.select_related('user', 'exercise_set').all().order_by('created_at')

        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
