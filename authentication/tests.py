from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core import mail
from django.test import override_settings
from django.urls import reverse
from PIL import Image
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
        self.assertNotIn('refresh', response.data)
        self.assertIn('refresh_token', response.cookies)
        self.assertTrue(response.cookies['refresh_token']['httponly'])
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
        self.media_directory = TemporaryDirectory()
        self.media_override = override_settings(
            MEDIA_ROOT=self.media_directory.name,
        )
        self.media_override.enable()
        self.addCleanup(self.media_override.disable)
        self.addCleanup(self.media_directory.cleanup)
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

    def make_image_upload(self, size=(1400, 900), image_format='PNG'):
        output = BytesIO()
        Image.new('RGB', size, '#7a4b2e').save(output, format=image_format)
        return SimpleUploadedFile(
            f'profile.{image_format.lower()}',
            output.getvalue(),
            content_type=f'image/{image_format.lower()}',
        )

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

    def test_authenticated_user_can_upload_normalized_profile_picture(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            reverse('usuario-profile-picture'),
            {'photo': self.make_image_upload()},
            format='multipart',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('/media/profiles/', response.data['profile_picture_url'])
        self.user.perfil.refresh_from_db()
        picture_path = Path(self.user.perfil.profile_picture.path)
        self.assertEqual(picture_path.suffix, '.jpg')
        self.assertTrue(picture_path.exists())
        with Image.open(picture_path) as image:
            self.assertEqual(image.format, 'JPEG')
            self.assertLessEqual(max(image.size), 1024)

    def test_rejects_file_disguised_as_image(self):
        self.client.force_authenticate(user=self.user)
        fake_image = SimpleUploadedFile(
            'profile.png',
            b'this is not an image',
            content_type='image/png',
        )

        response = self.client.post(
            reverse('usuario-profile-picture'),
            {'photo': fake_image},
            format='multipart',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.perfil.refresh_from_db()
        self.assertFalse(self.user.perfil.profile_picture)

    def test_rejects_profile_picture_larger_than_five_megabytes(self):
        self.client.force_authenticate(user=self.user)
        oversized_image = SimpleUploadedFile(
            'profile.png',
            b'0' * (5 * 1024 * 1024 + 1),
            content_type='image/png',
        )

        response = self.client.post(
            reverse('usuario-profile-picture'),
            {'photo': oversized_image},
            format='multipart',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.perfil.refresh_from_db()
        self.assertFalse(self.user.perfil.profile_picture)

    def test_authenticated_user_can_remove_profile_picture(self):
        self.client.force_authenticate(user=self.user)
        upload_response = self.client.post(
            reverse('usuario-profile-picture'),
            {'photo': self.make_image_upload(size=(256, 256))},
            format='multipart',
        )
        self.assertEqual(upload_response.status_code, status.HTTP_200_OK)
        self.user.perfil.refresh_from_db()
        picture_path = Path(self.user.perfil.profile_picture.path)

        response = self.client.delete(reverse('usuario-profile-picture'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.perfil.refresh_from_db()
        self.assertFalse(self.user.perfil.profile_picture)
        self.assertFalse(picture_path.exists())


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


class UserPrivilegeSecurityTests(APITestCase):
    def test_public_registration_cannot_create_admin(self):
        response = self.client.post(
            reverse('usuario-list'),
            {
                'username': 'attacker@example.com',
                'email': 'attacker@example.com',
                'password': 'a-valid-test-password',
                'is_staff': True,
                'is_superuser': True,
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username='attacker@example.com')
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_user_cannot_promote_self_through_me_endpoint(self):
        user = User.objects.create_user(
            username='regular@example.com',
            password='a-valid-test-password',
        )
        self.client.force_authenticate(user)
        response = self.client.patch(
            reverse('usuario-me'),
            {'is_staff': True, 'is_superuser': True},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class PasswordResetTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='reset@example.com',
            email='reset@example.com',
            password='old-valid-password',
        )

    def request_code(self):
        return self.client.post(
            reverse('password_reset_request'),
            {'email': self.user.email},
            format='json',
        )

    def test_requests_code_without_exposing_account_existence(self):
        known_response = self.request_code()
        unknown_response = self.client.post(
            reverse('password_reset_request'),
            {'email': 'unknown@example.com'},
            format='json',
        )

        self.assertEqual(known_response.status_code, status.HTTP_200_OK)
        self.assertEqual(unknown_response.status_code, status.HTTP_200_OK)
        self.assertEqual(known_response.data, unknown_response.data)
        self.assertEqual(len(mail.outbox), 1)

    def test_confirms_code_and_changes_password_once(self):
        self.request_code()
        code = next(
            part for part in mail.outbox[0].body.split() if part.isdigit()
        )
        payload = {
            'email': self.user.email,
            'code': code,
            'new_password': 'new-valid-password-2026',
        }

        response = self.client.post(
            reverse('password_reset_confirm'),
            payload,
            format='json',
        )
        repeated_response = self.client.post(
            reverse('password_reset_confirm'),
            payload,
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(repeated_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('new-valid-password-2026'))

    def test_rejects_invalid_code(self):
        self.request_code()
        response = self.client.post(
            reverse('password_reset_confirm'),
            {
                'email': self.user.email,
                'code': '000000',
                'new_password': 'new-valid-password-2026',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('old-valid-password'))
