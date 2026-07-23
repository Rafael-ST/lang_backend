from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from perfil.models import DEFAULT_PROFILE_POINTS, Perfil


User = get_user_model()


@override_settings(GOOGLE_OAUTH_CLIENT_IDS=['android-client-id'])
class GoogleAuthViewTests(APITestCase):
    google_claims = {
        'aud': 'android-client-id',
        'sub': 'google-user-id',
        'email': 'google@example.com',
        'email_verified': True,
        'given_name': 'Google',
        'family_name': 'User',
    }

    @patch('authentication.views.google_id_token.verify_oauth2_token')
    def test_creates_user_profile_and_api_tokens(self, verify_token):
        verify_token.return_value = self.google_claims

        response = self.client.post(
            reverse('google_auth'),
            {'id_token': 'valid-google-token'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['usuario']['email'], 'google@example.com')

        user = User.objects.get(email='google@example.com')
        self.assertFalse(user.has_usable_password())
        self.assertEqual(user.first_name, 'Google')
        self.assertEqual(user.last_name, 'User')
        self.assertEqual(
            Perfil.objects.get(user=user).pontos,
            DEFAULT_PROFILE_POINTS,
        )

    @patch('authentication.views.google_id_token.verify_oauth2_token')
    def test_reuses_existing_user_with_same_verified_email(self, verify_token):
        existing_user = User.objects.create_user(
            username='existing-user',
            email='google@example.com',
            password='a-valid-test-password',
        )
        verify_token.return_value = self.google_claims

        response = self.client.post(
            reverse('google_auth'),
            {'id_token': 'valid-google-token'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['usuario']['id'], existing_user.id)
        self.assertEqual(User.objects.count(), 1)

    @patch('authentication.views.google_id_token.verify_oauth2_token')
    def test_rejects_token_for_another_oauth_client(self, verify_token):
        verify_token.return_value = {
            **self.google_claims,
            'aud': 'another-client-id',
        }

        response = self.client.post(
            reverse('google_auth'),
            {'id_token': 'token-for-another-app'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(User.objects.exists())


class CurrentUserViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='user@example.com',
            email='user@example.com',
            password='a-valid-test-password',
        )
        self.other_user = User.objects.create_user(
            username='other@example.com',
            email='other@example.com',
            password='a-valid-test-password',
        )
        Perfil.objects.get_or_create(user=self.user)
        Perfil.objects.get_or_create(user=self.other_user)

    def test_authenticated_user_can_delete_own_account_and_profile(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.delete(reverse('usuario-me'))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(pk=self.user.pk).exists())
        self.assertFalse(Perfil.objects.filter(user_id=self.user.pk).exists())
        self.assertTrue(User.objects.filter(pk=self.other_user.pk).exists())

    def test_unauthenticated_user_cannot_delete_account(self):
        response = self.client.delete(reverse('usuario-me'))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())


class CredentialLoginTests(APITestCase):
    def test_returns_portuguese_message_when_account_does_not_exist(self):
        response = self.client.post(
            reverse('token_obtain_pair'),
            {
                'username': 'naoexiste@example.com',
                'password': 'senha-invalida',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'], 'E-mail ou senha inválidos.')
