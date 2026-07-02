from rest_framework.filters import BaseFilterBackend


class ExerciseFilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        card = request.query_params.get('card') or request.query_params.get('card_id')
        exercise_type = request.query_params.get('type')
        difficulty = request.query_params.get('difficulty')
        is_active = request.query_params.get('is_active')

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
