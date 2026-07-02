from django.db import models
from rest_framework import settings
from app.models import BaseModel
from django.conf import settings


from ExerciseSet.models import ExerciseSet

class Exercise(models.Model):
    class ExerciseType(models.TextChoices):
        MULTIPLE_CHOICE_TRANSLATION = "multiple_choice_translation", "Multipla escolha"
        WRITE_FROM_TEXT_AUDIO = "write_translation_from_text_audio", "Escrever com texto e audio"
        WRITE_FROM_AUDIO = "write_translation_from_audio", "Escrever ouvindo audio"
        SPEAK_WRITTEN_TEXT = "speak_written_text", "Falar texto escrito"
        JUST_AUDIO = "just_audio", "Apenas audio"

    exercise_set = models.ForeignKey(
        ExerciseSet,
        on_delete=models.CASCADE,
        related_name='exercises',
        verbose_name='Conjunto de exercicios',
        null=True,
        blank=True,
    )
    
    card = models.ForeignKey(
        "cards.Card",
        on_delete=models.CASCADE,
        related_name="exercises",
    )

    type = models.CharField(
        max_length=50,
        choices=ExerciseType.choices,
    )

    prompt = models.JSONField(default=dict, blank=True)
    options = models.JSONField(default=list, blank=True)
    answer_config = models.JSONField(default=dict, blank=True)

    is_active = models.BooleanField(default=True)
    difficulty = models.PositiveSmallIntegerField(default=1)
    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.get_type_display()} - {self.card}"

class ExerciseAttempt(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    exercise_set = models.ForeignKey(ExerciseSet, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    is_correct = models.BooleanField(default=True)
    answer = models.JSONField(default=dict, blank=True)