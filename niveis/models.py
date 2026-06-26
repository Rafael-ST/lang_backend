from django.db import models
from app.models import BaseModel


class Nivel(BaseModel):
    nome = models.CharField(verbose_name='Nome', max_length=100, unique=True)


    class Meta:
        verbose_name = 'Nível'
        verbose_name_plural = 'Níveis'
        ordering = ['nome']

    def __str__(self):
        return self.nome
