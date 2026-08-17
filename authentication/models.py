from django.conf import settings
from django.db import models

from app.models import BaseModel


class PasswordResetCode(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='password_reset_codes',
    )
    code_hash = models.CharField(max_length=128)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']


class AccountDeletionRequest(BaseModel):
    class Status(models.TextChoices):
        AWAITING_CONFIRMATION = (
            'awaiting_confirmation',
            'Aguardando confirmação',
        )
        CONFIRMED = 'confirmed', 'Confirmada'
        COMPLETED = 'completed', 'Concluída'
        CANCELLED = 'cancelled', 'Cancelada'

    email = models.EmailField(db_index=True)
    reason = models.TextField(blank=True, max_length=1000)
    confirmation_token_hash = models.CharField(max_length=64)
    confirmation_expires_at = models.DateTimeField()
    confirmed_at = models.DateTimeField(null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.AWAITING_CONFIRMATION,
        db_index=True,
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Solicitação de exclusão de conta'
        verbose_name_plural = 'Solicitações de exclusão de conta'

    def __str__(self):
        return f'{self.email} - {self.get_status_display()}'
