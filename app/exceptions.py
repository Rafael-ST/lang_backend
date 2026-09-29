from rest_framework.exceptions import PermissionDenied
from rest_framework.views import exception_handler

from app.audit import registrar_acesso_negado


def audited_exception_handler(exc, context):
    response = exception_handler(exc, context)
    request, view = context.get('request'), context.get('view')
    if isinstance(exc, PermissionDenied) and request and request.user.is_authenticated:
        serializer_class = getattr(view, 'serializer_class', None)
        model = getattr(getattr(serializer_class, 'Meta', None), 'model', None)
        if model is not None:
            registrar_acesso_negado(
                request, model, [type(permission).__name__ for permission in view.get_permissions()],
            )
    return response
