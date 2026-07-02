from rest_framework.filters import BaseFilterBackend


class ExerciseSetFilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        sublevel = request.query_params.get('sublevel') or request.query_params.get('sublevel_id')
        is_active = request.query_params.get('is_active')

        if sublevel:
            queryset = queryset.filter(sublevel_id=sublevel)

        if is_active is not None:
            value = is_active.lower()
            if value in ['true', '1', 'sim']:
                queryset = queryset.filter(is_active=True)
            elif value in ['false', '0', 'nao']:
                queryset = queryset.filter(is_active=False)

        return queryset


class ExerciseSetProgressFilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        user = request.query_params.get('user') or request.query_params.get('user_id')
        exercise_set = request.query_params.get('exercise_set') or request.query_params.get('exercise_set_id')
        status = request.query_params.get('status')

        if user:
            queryset = queryset.filter(user_id=user)

        if exercise_set:
            queryset = queryset.filter(exercise_set_id=exercise_set)

        if status:
            queryset = queryset.filter(status=status)

        return queryset
