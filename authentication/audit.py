import json

from django.contrib.admin.models import LogEntry
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

from app.audit import obter_ip
from app.log_actions import LOGIN, LOGIN_FALHOU, REDEFINICAO_SENHA


# Caracteres rejeitados pelo validador de usernames do cadastro público.
USUARIO_AUDITORIA_USERNAME = '[sistema:auditoria]'


def obter_usuario_auditoria():
    usuario, _ = get_user_model().objects.get_or_create(
        username=USUARIO_AUDITORIA_USERNAME,
        defaults={
            'first_name': 'Sistema — auditoria', 'password': '!',
            'is_active': False, 'is_staff': False, 'is_superuser': False,
        },
    )
    return usuario


def registrar_evento(request, usuario, action_flag, descricao, **detalhes):
    return LogEntry.objects.create(
        user=usuario if usuario is not None else obter_usuario_auditoria(),
        content_type=ContentType.objects.get_for_model(get_user_model()),
        object_id=str(usuario.pk) if usuario is not None else None,
        object_repr=str(usuario)[:200] if usuario is not None else 'Login não identificado',
        action_flag=action_flag,
        change_message=json.dumps({
            'origem': 'api', 'ip': obter_ip(request),
            'descricao': descricao, **detalhes,
        }, ensure_ascii=False, sort_keys=True),
    )


def registrar_login(request, usuario):
    return registrar_evento(request, usuario, LOGIN, 'Login realizado com sucesso pela API')


def registrar_falha_login(request, username, motivo='Credenciais inválidas'):
    username = username[:150] if isinstance(username, str) else ''
    usuario = get_user_model().objects.filter(username=username).first()
    return registrar_evento(
        request, usuario, LOGIN_FALHOU, 'Tentativa de login malsucedida',
        identificador=username, motivo_descricao=motivo,
    )


def registrar_redefinicao_senha(request, usuario):
    return registrar_evento(
        request, usuario, REDEFINICAO_SENHA, 'Senha redefinida pela API',
        alteracoes={'password': {'alterado': True, 'valores_ocultos': True}},
    )
