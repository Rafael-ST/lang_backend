from django.db import transaction
from django.utils import timezone
import unicodedata
import re
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from ExerciseSet.models import ExerciseSetProgress
from exercicio.filters import ExerciseAttemptFilterBackend, ExerciseFilterBackend
from exercicio.models import Exercise, ExerciseAttempt
from exercicio.serializers import ExerciseAttemptSerializer, ExerciseSerializer
from perfil.models import Perfil


MULTIPLE_CHOICE_TYPES = {
    Exercise.ExerciseType.MULTIPLE_CHOICE_TRANSLATION,
    Exercise.ExerciseType.MULTIPLE_CHOICE_AUDIO_ENGLISH,
    Exercise.ExerciseType.IMAGE_MULTIPLE_CHOICE_ENGLISH,
    Exercise.ExerciseType.AUDIO_MULTIPLE_CHOICE_IMAGES,
}
WRITTEN_TYPES = {
    Exercise.ExerciseType.WRITE_FROM_TEXT_AUDIO,
    Exercise.ExerciseType.WRITE_FROM_AUDIO,
    Exercise.ExerciseType.COMPLETE_AUDIO_TEXT,
}
SPEAKING_TYPES = {
    Exercise.ExerciseType.SPEAK_WRITTEN_TEXT,
    Exercise.ExerciseType.SPEAK_ENGLISH_FROM_TRANSLATION,
}
PRESENTATION_TYPES = {
    Exercise.ExerciseType.JUST_AUDIO,
    Exercise.ExerciseType.IMAGE_PRESENTATION,
}


def normalize_answer(value):
    normalized = unicodedata.normalize('NFD', str(value or ''))
    normalized = ''.join(
        char for char in normalized if unicodedata.category(char) != 'Mn'
    )
    normalized = re.sub(r"[^a-z0-9\s']", '', normalized.casefold())
    return ' '.join(normalized.strip().split())


def normalize_written_answer(value, config):
    value = str(value or '')
    if config.get('trim', True) not in (False, 'false'):
        value = value.strip()
    if config.get('case_sensitive') not in (True, 'true'):
        value = value.casefold()
    return value


def validate_exercise_answer(exercise, answer):
    answer = answer if isinstance(answer, dict) else {}
    config = exercise.answer_config if isinstance(exercise.answer_config, dict) else {}

    if exercise.type in PRESENTATION_TYPES:
        return True

    if exercise.type in MULTIPLE_CHOICE_TYPES:
        return str(answer.get('selected_option_id', '')) == str(
            config.get('correct_card_id', '')
        )

    if exercise.type in WRITTEN_TYPES:
        accepted = [config.get('correct_text'), *(config.get('accept') or [])]
        submitted = normalize_written_answer(answer.get('text'), config)
        return bool(submitted) and submitted in {
            normalize_written_answer(value, config) for value in accepted if value
        }

    if exercise.type in SPEAKING_TYPES:
        if answer.get('skipped') is True:
            return True
        accepted = [
            config.get('expected_transcript'),
            config.get('correct_text'),
            *(config.get('accept') or []),
            exercise.card.english_name,
        ]
        submitted = normalize_answer(answer.get('transcript'))
        return bool(submitted) and submitted in {
            normalize_answer(value) for value in accepted if value
        }

    if exercise.type == Exercise.ExerciseType.MATCHING_PAIRS:
        matched_ids = {str(value) for value in answer.get('matched_card_ids', [])}
        expected_ids = {
            str(value)
            for value in exercise.pair_cards.values_list('id', flat=True)
        }
        return bool(expected_ids) and matched_ids == expected_ids

    return False


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

    def get_permissions(self):
        if self.action in {'create', 'update', 'partial_update', 'destroy'}:
            return [IsAdminUser()]
        return [IsAuthenticated()]

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

        if not exercise.is_active or not exercise.exercise_set_id:
            return Response(
                {'detail': 'Este exercicio nao possui conjunto vinculado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        answer = request.data.get('answer', {})
        is_correct = validate_exercise_answer(exercise, answer)

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
            profile = Perfil.objects.select_for_update().filter(
                user=request.user,
            ).first()
            if not profile or profile.pontos <= 0:
                return Response(
                    {'detail': 'Voce nao possui pontos disponiveis.'},
                    status=status.HTTP_409_CONFLICT,
                )

            profile.pontos -= 1
            profile.save(update_fields=['pontos', 'updated_at'])

            ExerciseAttempt.objects.create(
                user=request.user,
                exercise_set=exercise.exercise_set,
                exercise=exercise,
                is_correct=is_correct,
                answer=answer,
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
                'profile_points': profile.pontos,
            },
            status=status.HTTP_200_OK,
        )


class ExerciseAttemptViewSet(viewsets.ReadOnlyModelViewSet):
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
