from django.db import models
from app.models import BaseModel
from categorias.models import Categoria


class Card(BaseModel):
    english_name = models.CharField(max_length=255, verbose_name='Nome em inglês')
    international_name = models.CharField(max_length=255, verbose_name='Nome internacional')
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, verbose_name='Categoria')

    def __str__(self):
        return self.english_name
