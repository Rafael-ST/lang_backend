from django.db import models
from app.models import BaseModel
from niveis.models import Nivel


class SubNivel(BaseModel):
    nome = models.CharField(verbose_name='Nome', max_length=100)
    description = models.TextField(verbose_name='Descricao', blank=True)
    subnivel = models.ForeignKey(Nivel, verbose_name='Nível', on_delete=models.CASCADE, related_name='subniveis')
    ordem = models.PositiveIntegerField(verbose_name='Ordem', default=0)

    class Meta:
        verbose_name = 'Subnível'
        verbose_name_plural = 'Subníveis'
        ordering = ['ordem', 'nome']

    def __str__(self):
        return self.nome
