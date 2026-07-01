from rest_framework.filters import BaseFilterBackend


class SubNivelFilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        nome = request.query_params.get('nome')
        nivel = request.query_params.get('nivel') or request.query_params.get('subnivel')
        is_active = request.query_params.get('is_active')

        if nome:
            queryset = queryset.filter(nome__icontains=nome)

        if nivel:
            queryset = queryset.filter(subnivel_id=nivel)

        if is_active is not None:
            value = is_active.lower()
            if value in ['true', '1', 'sim']:
                queryset = queryset.filter(is_active=True)
            elif value in ['false', '0', 'nao', 'não']:
                queryset = queryset.filter(is_active=False)

        return queryset
