from django.db import transaction
from django.utils import timezone
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ExerciseSet.models import ExerciseSetProgress
from exercicio.filters import ExerciseAttemptFilterBackend, ExerciseFilterBackend
from exercicio.models import Exercise, ExerciseAttempt
from exercicio.serializers import ExerciseAttemptSerializer, ExerciseSerializer


class ExerciseViewSet(viewsets.ModelViewSet):
    serializer_class = ExerciseSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [
        ExerciseFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ['card__english_name', 'card__international_name', 'exercise_set__title', 'type', 'skill']
    ordering_fields = ['order', 'difficulty', 'type', 'skill', 'created_at', 'updated_at', 'is_active']
    ordering = ['order', 'id']

    def get_queryset(self):
        queryset = Exercise.objects.select_related(
            'card', 'exercise_set'
        ).prefetch_related('pair_cards').all().order_by('order', 'id')
        include_completed = self.request.query_params.get('include_completed')
        exercise_set = self.request.query_params.get('exercise_set') or self.request.query_params.get('exercise_set_id')

        if exercise_set and str(include_completed).lower() not in ['true', '1', 'sim']:
            completed_exercise_ids = ExerciseAttempt.objects.filter(
                user=self.request.user,
                exercise_set_id=exercise_set,
                is_correct=True,
            ).values('exercise_id')
            queryset = queryset.exclude(id__in=completed_exercise_ids)

        return queryset

    @action(detail=True, methods=['post'], url_path='complete')
    def complete(self, request, pk=None):
        exercise = self.get_object()

        if not exercise.exercise_set_id:
            return Response(
                {'detail': 'Este exercicio nao possui conjunto vinculado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        is_correct = request.data.get('is_correct', True)
        if isinstance(is_correct, str):
            is_correct = is_correct.lower() in ['true', '1', 'sim']
        else:
            is_correct = bool(is_correct)

        review = request.data.get('review', False)
        if isinstance(review, str):
            review = review.lower() in ['true', '1', 'sim']
        else:
            review = bool(review)

        duration_ms = request.data.get('duration_ms')
        try:
            duration_ms = max(0, int(duration_ms)) if duration_ms is not None else None
        except (TypeError, ValueError):
            return Response(
                {'duration_ms': 'Informe uma duracao valida em milissegundos.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if review:
            return Response(
                {
                    'exercise_completed': is_correct,
                    'review': True,
                    'set_completed': False,
                },
                status=status.HTTP_200_OK,
            )

        with transaction.atomic():
            ExerciseAttempt.objects.create(
                user=request.user,
                exercise_set=exercise.exercise_set,
                exercise=exercise,
                is_correct=is_correct,
                answer=request.data.get('answer', {}),
            )

            total_count = Exercise.objects.filter(
                exercise_set=exercise.exercise_set,
                is_active=True,
            ).count()
            completed_count = ExerciseAttempt.objects.filter(
                user=request.user,
                exercise_set=exercise.exercise_set,
                exercise__is_active=True,
                is_correct=True,
            ).values('exercise_id').distinct().count()

            if total_count > 0 and completed_count >= total_count:
                progress_status = ExerciseSetProgress.Status.COMPLETED
                completed_at = timezone.now()
            else:
                progress_status = ExerciseSetProgress.Status.IN_PROGRESS
                completed_at = None

            progress, _ = ExerciseSetProgress.objects.get_or_create(
                user=request.user,
                exercise_set=exercise.exercise_set,
                defaults={
                    'status': progress_status,
                    'completed_at': completed_at,
                    'duration_ms': duration_ms if completed_at else None,
                },
            )

            if progress.status != ExerciseSetProgress.Status.COMPLETED:
                progress.status = progress_status
                progress.completed_at = completed_at
                if completed_at:
                    progress.duration_ms = duration_ms
                progress.save(update_fields=['status', 'completed_at', 'duration_ms', 'updated_at'])

        return Response(
            {
                'exercise_completed': is_correct,
                'set_completed': progress_status == ExerciseSetProgress.Status.COMPLETED,
                'status': progress_status,
                'completed_count': completed_count,
                'total_count': total_count,
                'completed_at': completed_at,
                'duration_ms': progress.duration_ms,
            },
            status=status.HTTP_200_OK,
        )


class ExerciseAttemptViewSet(viewsets.ModelViewSet):
    serializer_class = ExerciseAttemptSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [
        ExerciseAttemptFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ['user__username', 'user__email', 'exercise_set__title', 'exercise__type']
    ordering_fields = ['is_correct', 'created_at', 'updated_at']
    ordering = ['created_at']

    def get_queryset(self):
        queryset = ExerciseAttempt.objects.select_related('user', 'exercise_set', 'exercise').all().order_by('created_at')

        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
