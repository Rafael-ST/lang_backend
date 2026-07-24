from django.contrib.auth import get_user_model
from django.test import TestCase

from cards.models import Card, UserCardAccess
from categorias.models import Categoria
from perfil.serializers import PerfilSerializer


class PerfilSerializerTests(TestCase):
    def test_returns_learned_words_count(self):
        user = get_user_model().objects.create_user(
            username='learner',
            password='test-password',
        )
        profile = user.perfil
        category = Categoria.objects.create(nome='Vocabulary')
        learned_card = Card.objects.create(
            english_name='Hello',
            international_name='Ola',
            categoria=category,
        )
        UserCardAccess.objects.create(user=user, card=learned_card)

        data = PerfilSerializer(profile).data

        self.assertEqual(data['learned_words_count'], 1)
        self.assertEqual(data['completed_exercises_count'], 0)
