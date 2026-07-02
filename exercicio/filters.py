from rest_framework.filters import BaseFilterBackend


class ExerciseFilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        exercise_set = request.query_params.get('exercise_set') or request.query_params.get('exercise_set_id')
        card = request.query_params.get('card') or request.query_params.get('card_id')
        exercise_type = request.query_params.get('type')
        difficulty = request.query_params.get('difficulty')
        is_active = request.query_params.get('is_active')

        if exercise_set:
            queryset = queryset.filter(exercise_set_id=exercise_set)

        if card:
            queryset = queryset.filter(card_id=card)

        if exercise_type:
            queryset = queryset.filter(type=exercise_type)

        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)

        if is_active is not None:
            value = is_active.lower()
            if value in ['true', '1', 'sim']:
                queryset = queryset.filter(is_active=True)
            elif value in ['false', '0', 'nao']:
                queryset = queryset.filter(is_active=False)

        return queryset


class ExerciseAttemptFilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        user = request.query_params.get('user') or request.query_params.get('user_id')
        exercise_set = request.query_params.get('exercise_set') or request.query_params.get('exercise_set_id')
        exercise = request.query_params.get('exercise') or request.query_params.get('exercise_id')
        is_correct = request.query_params.get('is_correct')

        if user:
            queryset = queryset.filter(user_id=user)

        if exercise_set:
            queryset = queryset.filter(exercise_set_id=exercise_set)

        if exercise:
            queryset = queryset.filter(exercise_id=exercise)

        if is_correct is not None:
            value = is_correct.lower()
            if value in ['true', '1', 'sim']:
                queryset = queryset.filter(is_correct=True)
            elif value in ['false', '0', 'nao']:
                queryset = queryset.filter(is_correct=False)

        return queryset
