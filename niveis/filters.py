from rest_framework.filters import BaseFilterBackend


class NivelFilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        nome = request.query_params.get('nome')
        is_active = request.query_params.get('is_active')

        if nome:
            queryset = queryset.filter(nome__icontains=nome)

        if is_active is not None:
            value = is_active.lower()
            if value in ['true', '1', 'sim']:
                queryset = queryset.filter(is_active=True)
            elif value in ['false', '0', 'nao', 'não']:
                queryset = queryset.filter(is_active=False)

        return queryset
