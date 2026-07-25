from django.test import TestCase

from cards.models import Card
from categorias.models import Categoria
from ExerciseSet.models import ExerciseSet
from exercicio.models import Exercise
from exercicio.serializers import ExerciseSerializer
from niveis.models import Nivel
from subniveis.models import SubNivel


class CompleteAudioTextSerializerTests(TestCase):
    def setUp(self):
        category = Categoria.objects.create(nome='Greetings')
        level = Nivel.objects.create(nome='A1')
        sublevel = SubNivel.objects.create(
            nome='Introducao',
            subnivel=level,
        )
        self.exercise_set = ExerciseSet.objects.create(
            sublevel=sublevel,
            title='Saudacoes',
        )
        self.card = Card.objects.create(
            english_name='How are you?',
            international_name='Como voce esta?',
            categoria=category,
            audio='cards/audios/how-are-you.mp3',
        )

    def build_payload(self, template='How __ you?', answer='are'):
        return {
            'exercise_set': str(self.exercise_set.id),
            'card': str(self.card.id),
            'type': Exercise.ExerciseType.COMPLETE_AUDIO_TEXT,
            'prompt': {'text': template},
            'answer_config': {'correct_text': answer},
            'difficulty': 1,
            'order': 0,
        }

    def test_accepts_one_blank_and_an_answer(self):
        serializer = ExerciseSerializer(data=self.build_payload())

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_rejects_template_without_exactly_one_blank(self):
        serializer = ExerciseSerializer(
            data=self.build_payload(template='How are you?')
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('prompt', serializer.errors)

    def test_rejects_empty_blank_answer(self):
        serializer = ExerciseSerializer(data=self.build_payload(answer=''))

        self.assertFalse(serializer.is_valid())
        self.assertIn('answer_config', serializer.errors)

    def test_accepts_image_presentation_with_image_audio_and_translation(self):
        self.card.image = 'cards/images/how-are-you.jpg'
        self.card.save(update_fields=['image'])
        payload = self.build_payload()
        payload.update({
            'type': Exercise.ExerciseType.IMAGE_PRESENTATION,
            'prompt': {},
            'answer_config': {},
        })
        serializer = ExerciseSerializer(data=payload)

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_rejects_image_presentation_without_image(self):
        payload = self.build_payload()
        payload.update({
            'type': Exercise.ExerciseType.IMAGE_PRESENTATION,
            'prompt': {},
            'answer_config': {},
        })
        serializer = ExerciseSerializer(data=payload)

        self.assertFalse(serializer.is_valid())
        self.assertIn('card', serializer.errors)
