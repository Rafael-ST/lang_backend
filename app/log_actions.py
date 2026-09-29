from django.contrib.admin.models import ACTION_FLAG_CHOICES


LOGIN = 4
LOGIN_FALHOU = 5
ACESSO_NEGADO = 6
REDEFINICAO_SENHA = 7
LOG_ACTION_CHOICES = (
    *ACTION_FLAG_CHOICES,
    (LOGIN, 'Login'),
    (LOGIN_FALHOU, 'Login malsucedido'),
    (ACESSO_NEGADO, 'Acesso negado'),
    (REDEFINICAO_SENHA, 'Redefinição de senha'),
)
