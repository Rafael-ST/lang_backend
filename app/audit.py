import json
from ipaddress import ip_address

from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.fields.files import FieldFile

from app.log_actions import ACESSO_NEGADO


def obter_ip(request):
    try:
        return str(ip_address(request.META.get("REMOTE_ADDR")))
    except (ValueError, AttributeError):
        return "não informado"


def registrar_acesso_negado(request, model, permissoes):
    return LogEntry.objects.create(
        user_id=request.user.pk,
        content_type=ContentType.objects.get_for_model(model),
        object_id=None,
        object_repr=f"{request.method} {request.path}"[:200],
        action_flag=ACESSO_NEGADO,
        change_message=json.dumps({
            "origem": "api", "ip": obter_ip(request),
            "descricao": "Tentativa de acesso sem permissão de classe",
            "metodo": request.method, "caminho": request.path,
            "permissoes_exigidas": permissoes,
        }, ensure_ascii=False, sort_keys=True),
    )


def capturar_estado(instance):
    estado = {
        field.name: (
            str(field.value_from_object(instance))
            if isinstance(field.value_from_object(instance), FieldFile)
            else field.value_from_object(instance)
        )
        for field in instance._meta.concrete_fields
        if not field.primary_key and field.name not in {"created_at", "updated_at", "password_history"}
    }
    for field in instance._meta.many_to_many:
        estado[field.name] = sorted(
            str(pk) for pk in getattr(instance, field.name).values_list("pk", flat=True)
        )
    return estado


def registrar_alteracao(request, instance, antes, depois, action_flag, *,
                       descricao="Objeto alterado pela API", campos_sensiveis=(), autor=None):
    alteracoes = {}
    for campo in antes.keys() | depois.keys():
        anterior, atual = antes.get(campo), depois.get(campo)
        if anterior == atual:
            continue
        sensivel = campo in campos_sensiveis or any(
            termo in campo.lower()
            for termo in ("password", "senha", "token", "secret", "api_key", "chave_privada", "code_hash")
        )
        alteracoes[campo] = (
            {"alterado": True, "valores_ocultos": True}
            if sensivel else {"antes": anterior, "depois": atual}
        )
    if not alteracoes:
        return None
    return LogEntry.objects.create(
        user_id=autor.pk if autor is not None else request.user.pk,
        content_type=ContentType.objects.get_for_model(instance),
        object_id=str(instance.pk),
        object_repr=str(instance)[:200],
        action_flag=action_flag,
        change_message=json.dumps({
            "origem": "api", "ip": obter_ip(request),
            "descricao": descricao, "alteracoes": alteracoes,
        }, cls=DjangoJSONEncoder, ensure_ascii=False, sort_keys=True),
    )
