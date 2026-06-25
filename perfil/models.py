from django.db import models
from app.models import BaseModel


class Perfil(BaseModel):
    user = models.OneToOneField(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='perfil'
    )
    pontos = models.IntegerField(default=20)

    def __str__(self):
        return f"{self.user.username}'s Profile"
