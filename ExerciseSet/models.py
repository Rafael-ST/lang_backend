from django.db import models
from app.models import BaseModel
# from exercicio.models import Exercise
from subniveis.models import SubNivel
from django.conf import settings


class ExerciseSetImage(BaseModel):
    name = models.CharField(max_length=255, verbose_name='Nome')
    image = models.ImageField(
        upload_to='exercise_sets/images/',
        verbose_name='Imagem',
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Imagem de conjunto de exercicios'
        verbose_name_plural = 'Imagens de conjuntos de exercicios'

    def __str__(self):
        return self.name


class ExerciseSet(BaseModel):
    sublevel = models.ForeignKey(
        SubNivel,
        on_delete=models.CASCADE,
        related_name='exercise_sets',
        verbose_name='Subnivel',
    )
    title = models.CharField(
        max_length=255,
        verbose_name='Titulo',
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descricao',
    )
    image = models.ForeignKey(
        ExerciseSetImage,
        on_delete=models.SET_NULL,
        related_name='exercise_sets',
        null=True,
        blank=True,
        verbose_name='Imagem',
    )
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return self.title


class ExerciseSetProgress(BaseModel):
    class Status(models.TextChoices):
        NOT_STARTED = "not_started", "Não iniciado"
        IN_PROGRESS = "in_progress", "Em andamento"
        COMPLETED = "completed", "Concluido"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    exercise_set = models.ForeignKey(
        ExerciseSet,
        on_delete=models.CASCADE,
        related_name="progresses",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NOT_STARTED,
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_ms = models.PositiveBigIntegerField(null=True, blank=True)

    class Meta:
        unique_together = ["user", "exercise_set"]


