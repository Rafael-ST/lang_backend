from django.db import models
from app.models import BaseModel

class Categoria(BaseModel):
    nome = models.CharField(max_length=255, verbose_name='Nome da Categoria')

    def __str__(self):
        return self.nome
