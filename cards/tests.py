from io import BytesIO

from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from django.test import TestCase
from PIL import Image
from rest_framework import status
from rest_framework.test import APIClient

from cards.models import Card, UserCardAccess
from cards.serializers import CardSerializer
from categorias.models import Categoria


class CardApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username='card-admin',
            password='test-password',
            is_staff=True,
        )
        self.client.force_authenticate(self.user)
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

    def test_create_card_without_category(self):
        response = self.client.post(
            self.card_list_url,
            {
                'english_name': 'Uncategorized',
                'international_name': 'Sem categoria',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        card = Card.objects.get(english_name='Uncategorized')
        self.assertIsNone(card.categoria)

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


class MarkCardsSeenApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username='learner',
            password='test-password',
        )
        self.client.force_authenticate(self.user)
        self.categoria = Categoria.objects.create(nome='Test Category')
        self.card = Card.objects.create(
            english_name='Hello',
            international_name='Ola',
            categoria=self.categoria,
        )
        self.url = reverse('card-mark-seen')

    def test_marks_a_card_as_first_seen_only_once(self):
        payload = {'card_ids': [str(self.card.id)]}

        first_response = self.client.post(self.url, payload, format='json')
        second_response = self.client.post(self.url, payload, format='json')

        self.assertEqual(first_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            first_response.data['first_seen_card_ids'],
            [str(self.card.id)],
        )
        self.assertEqual(second_response.status_code, status.HTTP_200_OK)
        self.assertEqual(second_response.data['first_seen_card_ids'], [])
        self.assertEqual(
            UserCardAccess.objects.filter(user=self.user, card=self.card).count(),
            1,
        )

    def test_lists_only_cards_seen_by_authenticated_user(self):
        other_card = Card.objects.create(
            english_name='Goodbye',
            international_name='Tchau',
            categoria=self.categoria,
        )
        UserCardAccess.objects.create(user=self.user, card=self.card)

        response = self.client.get(reverse('card-seen'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([str(card['id']) for card in response.data], [str(self.card.id)])
        self.assertNotIn(str(other_card.id), [str(card['id']) for card in response.data])

    def test_does_not_list_cards_seen_by_another_user(self):
        other_user = get_user_model().objects.create_user(
            username='another-learner',
            password='test-password',
        )
        UserCardAccess.objects.create(user=other_user, card=self.card)

        response = self.client.get(reverse('card-seen'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_does_not_list_seen_card_without_category(self):
        uncategorized_card = Card.objects.create(
            english_name='Uncategorized',
            international_name='Sem categoria',
            categoria=None,
        )
        UserCardAccess.objects.create(user=self.user, card=uncategorized_card)

        response = self.client.get(reverse('card-seen'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])


class CardImageSerializerTests(TestCase):
    def setUp(self):
        category = Categoria.objects.create(nome='Images')
        self.card = Card.objects.create(
            english_name='Cat',
            international_name='Gato',
            categoria=category,
        )

    def test_normalizes_valid_card_image_as_jpeg(self):
        image_bytes = BytesIO()
        Image.new('RGB', (800, 600), '#446688').save(
            image_bytes,
            format='PNG',
        )
        upload = SimpleUploadedFile(
            'cat.png',
            image_bytes.getvalue(),
            content_type='image/png',
        )
        serializer = CardSerializer(
            self.card,
            data={'image': upload},
            partial=True,
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        normalized_image = serializer.validated_data['image']
        with Image.open(normalized_image) as image:
            self.assertEqual(image.format, 'JPEG')
            self.assertLessEqual(max(image.size), 1600)

    def test_rejects_file_disguised_as_card_image(self):
        upload = SimpleUploadedFile(
            'cat.png',
            b'not-an-image',
            content_type='image/png',
        )
        serializer = CardSerializer(
            self.card,
            data={'image': upload},
            partial=True,
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('image', serializer.errors)


class CardWritePermissionTests(TestCase):
    def setUp(self):
        category = Categoria.objects.create(nome='Permissions')
        self.card = Card.objects.create(
            english_name='Dog',
            international_name='Cachorro',
            categoria=category,
        )
        self.url = reverse('card-detail', args=[self.card.id])
        self.user = get_user_model().objects.create_user(
            username='student',
            password='test-password',
        )
        self.admin = get_user_model().objects.create_user(
            username='content-admin',
            password='test-password',
            is_staff=True,
        )

    def test_regular_user_cannot_change_card_content(self):
        client = APIClient()
        client.force_authenticate(self.user)

        response = client.patch(
            self.url,
            {'english_name': 'Changed'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_user_can_change_card_content(self):
        client = APIClient()
        client.force_authenticate(self.admin)

        response = client.patch(
            self.url,
            {'english_name': 'Puppy'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
