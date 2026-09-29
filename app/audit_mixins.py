from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.contrib.auth import get_user_model
from django.db import transaction

from app.audit import capturar_estado, registrar_alteracao


class AuditModelMixin:
    """Persiste a alteração e sua auditoria na mesma transação."""

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def get_object(self):
        instance = super().get_object()
        if self.request.method in {'PUT', 'PATCH', 'DELETE'}:
            # Bloqueia somente a linha alvo, inclusive em querysets com joins.
            instance = type(instance).objects.select_for_update().get(pk=instance.pk)
        return instance

    def _campos_sensiveis(self, serializer):
        return {
            field.source or name
            for name, field in serializer.fields.items() if field.write_only
        }

    @transaction.atomic
    def perform_create(self, serializer):
        instance = serializer.save()
        instance.refresh_from_db()
        autor = None
        if not self.request.user.is_authenticated:
            # O cadastro público tem como autor a própria conta criada.
            if isinstance(instance, get_user_model()):
                autor = instance
        registrar_alteracao(
            self.request, instance, {}, capturar_estado(instance), ADDITION,
            descricao='Objeto criado pela API', autor=autor,
            campos_sensiveis=self._campos_sensiveis(serializer),
        )

    @transaction.atomic
    def perform_update(self, serializer):
        antes = capturar_estado(serializer.instance)
        instance = serializer.save()
        instance.refresh_from_db()
        registrar_alteracao(
            self.request, instance, antes, capturar_estado(instance), CHANGE,
            campos_sensiveis=self._campos_sensiveis(serializer),
        )

    @transaction.atomic
    def perform_destroy(self, instance):
        autor = None
        if isinstance(instance, get_user_model()) and instance.pk == self.request.user.pk:
            from authentication.audit import obter_usuario_auditoria
            # LogEntry.user usa CASCADE; preserva o registro da autoexclusão.
            autor = obter_usuario_auditoria()
        registrar_alteracao(
            self.request, instance, capturar_estado(instance), {}, DELETION,
            descricao='Objeto excluído pela API', autor=autor,
        )
        instance.delete()
