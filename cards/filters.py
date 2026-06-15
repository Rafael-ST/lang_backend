from rest_framework.filters import BaseFilterBackend


class CardFilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        categoria = request.query_params.get('categoria') or request.query_params.get('categoria_id')

        if categoria:
            queryset = queryset.filter(categoria_id=categoria)

        return queryset
