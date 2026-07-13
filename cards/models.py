from django.db import models
from django.conf import settings
from app.models import BaseModel
from categorias.models import Categoria


class Card(BaseModel):
    english_name = models.CharField(max_length=255, verbose_name='Nome em inglês')
    international_name = models.CharField(max_length=255, verbose_name='Nome internacional')
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, verbose_name='Categoria')
    audio = models.FileField(
        upload_to='cards/audios/',
        null=True,
        blank=True,
        verbose_name='Áudio',
    )


    def __str__(self):
        return self.english_name


class UserCardAccess(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='card_accesses',
        verbose_name='Usuario',
    )
    card = models.ForeignKey(
        Card,
        on_delete=models.CASCADE,
        related_name='user_accesses',
        verbose_name='Card',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'card'],
                name='unique_user_card_access',
            ),
        ]
        ordering = ['created_at']
        verbose_name = 'Primeiro acesso ao card'
        verbose_name_plural = 'Primeiros acessos aos cards'

    def __str__(self):
        return f'{self.user} - {self.card}'
