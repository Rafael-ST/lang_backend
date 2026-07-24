from django.db import models
from app.models import BaseModel


DEFAULT_PROFILE_POINTS = 20


class Perfil(BaseModel):
    user = models.OneToOneField(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='perfil'
    )
    pontos = models.IntegerField(default=DEFAULT_PROFILE_POINTS)
    pontos_recuperados_desde_ultimo_exercicio = models.IntegerField(default=0)
    ultima_recuperacao_pontos_em = models.DateTimeField(null=True, blank=True)
    profile_picture = models.ImageField(
        upload_to='profiles/',
        null=True,
        blank=True,
        verbose_name='Foto do perfil',
    )

    def __str__(self):
        return f"{self.user.username}'s Profile"
