from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

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


class ProfilePointsSecurityTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='points-user',
            password='test-password',
        )
        self.client.force_authenticate(self.user)
        self.profile = self.user.perfil

    def test_cannot_patch_points_directly(self):
        response = self.client.patch(
            reverse('perfil-detail', args=[self.profile.id]),
            {'pontos': 999999},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.profile.refresh_from_db()
        self.assertNotEqual(self.profile.pontos, 999999)

    def test_spend_point_decrements_exactly_one(self):
        previous_points = self.profile.pontos
        response = self.client.post(
            reverse('perfil-spend-point', args=[self.profile.id]),
            {},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.pontos, previous_points - 1)
