from django.db import models
from rest_framework import settings
from app.models import BaseModel
from django.conf import settings


from ExerciseSet.models import ExerciseSet

class Exercise(models.Model):
    class Skill(models.TextChoices):
        LISTENING = "listening", "Listening"
        READING = "reading", "Reading"
        SPEAKING = "speaking", "Speaking"

    class ExerciseType(models.TextChoices):
        MULTIPLE_CHOICE_TRANSLATION = "multiple_choice_translation", "Multipla escolha"
        MULTIPLE_CHOICE_AUDIO_ENGLISH = "multiple_choice_audio_english", "Multipla escolha com audio em ingles"
        WRITE_FROM_TEXT_AUDIO = "write_translation_from_text_audio", "Escrever com texto e audio"
        WRITE_FROM_AUDIO = "write_translation_from_audio", "Escrever ouvindo audio"
        SPEAK_WRITTEN_TEXT = "speak_written_text", "Falar texto escrito"
        SPEAK_ENGLISH_FROM_TRANSLATION = (
            "speak_english_from_translation",
            "Falar em ingles a partir do portugues",
        )
        JUST_AUDIO = "just_audio", "Apenas audio"
        MATCHING_PAIRS = "matching_pairs", "Associar traducao e ingles"
        COMPLETE_AUDIO_TEXT = "complete_audio_text", "Completar texto ouvindo audio"
        IMAGE_PRESENTATION = "image_presentation", "Apresentacao com imagem"
        IMAGE_MULTIPLE_CHOICE_ENGLISH = (
            "image_multiple_choice_english",
            "Multipla escolha em ingles com imagem",
        )
        AUDIO_MULTIPLE_CHOICE_IMAGES = (
            "audio_multiple_choice_images",
            "Multipla escolha de imagens com audio",
        )

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

    pair_cards = models.ManyToManyField(
        "cards.Card",
        blank=True,
        related_name="matching_exercises",
        verbose_name="Cards para associacao",
    )

    type = models.CharField(
        max_length=50,
        choices=ExerciseType.choices,
    )
    skill = models.CharField(
        max_length=20,
        choices=Skill.choices,
        default=Skill.READING,
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

    @classmethod
    def default_skill_for_type(cls, exercise_type):
        if exercise_type in {
            cls.ExerciseType.SPEAK_WRITTEN_TEXT,
            cls.ExerciseType.SPEAK_ENGLISH_FROM_TRANSLATION,
        }:
            return cls.Skill.SPEAKING
        if exercise_type in {
            cls.ExerciseType.JUST_AUDIO,
            cls.ExerciseType.MULTIPLE_CHOICE_AUDIO_ENGLISH,
            cls.ExerciseType.WRITE_FROM_AUDIO,
            cls.ExerciseType.COMPLETE_AUDIO_TEXT,
            cls.ExerciseType.IMAGE_PRESENTATION,
            cls.ExerciseType.AUDIO_MULTIPLE_CHOICE_IMAGES,
        }:
            return cls.Skill.LISTENING

        return cls.Skill.READING

    def __str__(self):
        return f"{self.get_type_display()} - {self.card}"

class ExerciseAttempt(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    exercise_set = models.ForeignKey(ExerciseSet, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    is_correct = models.BooleanField(default=True)
    answer = models.JSONField(default=dict, blank=True)
