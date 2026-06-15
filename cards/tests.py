from django.urls import reverse

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from cards.models import Card
from categorias.models import Categoria


class CardApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.categoria = Categoria.objects.create(nome='Test Category')
        self.card_list_url = reverse('card-list')

    def test_create_card(self):
        payload = {
            'english_name': 'Hello',
            'international_name': 'Olá',
            'categoria': str(self.categoria.id),
        }
        response = self.client.post(self.card_list_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Card.objects.count(), 1)
        card = Card.objects.first()
        self.assertEqual(card.english_name, payload['english_name'])
        self.assertEqual(card.international_name, payload['international_name'])
        self.assertEqual(str(card.categoria.id), payload['categoria'])

    def test_retrieve_card(self):
        card = Card.objects.create(
            english_name='Hello',
            international_name='Olá',
            categoria=self.categoria,
        )
        url = reverse('card-detail', args=[card.id])

        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['english_name'], card.english_name)
        self.assertEqual(response.data['international_name'], card.international_name)

    def test_update_card(self):
        card = Card.objects.create(
            english_name='Hello',
            international_name='Olá',
            categoria=self.categoria,
        )
        url = reverse('card-detail', args=[card.id])
        payload = {
            'english_name': 'Hi',
            'international_name': 'Olá',
            'categoria': str(self.categoria.id),
        }

        response = self.client.put(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        card.refresh_from_db()
        self.assertEqual(card.english_name, payload['english_name'])

    def test_partial_update_card(self):
        card = Card.objects.create(
            english_name='Hello',
            international_name='Olá',
            categoria=self.categoria,
        )
        url = reverse('card-detail', args=[card.id])
        payload = {'english_name': 'Hi'}

        response = self.client.patch(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        card.refresh_from_db()
        self.assertEqual(card.english_name, payload['english_name'])

    def test_delete_card(self):
        card = Card.objects.create(
            english_name='Hello',
            international_name='Olá',
            categoria=self.categoria,
        )
        url = reverse('card-detail', args=[card.id])

        response = self.client.delete(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Card.objects.filter(id=card.id).exists())

    def test_filter_cards_by_categoria(self):
        outra_categoria = Categoria.objects.create(nome='Other Category')
        expected_card = Card.objects.create(
            english_name='Hello',
            international_name='Ola',
            categoria=self.categoria,
        )
        Card.objects.create(
            english_name='Bye',
            international_name='Tchau',
            categoria=outra_categoria,
        )

        response = self.client.get(
            self.card_list_url,
            {'categoria': str(self.categoria.id)},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], str(expected_card.id))
