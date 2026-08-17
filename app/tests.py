import re
from urllib.parse import parse_qs, urlparse

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from authentication.models import AccountDeletionRequest


User = get_user_model()


class PrivacyPolicyViewTests(TestCase):
    @override_settings(PRIVACY_CONTACT_EMAIL='privacidade@example.com')
    def test_privacy_policy_is_public_and_displays_contact(self):
        response = self.client.get(reverse('privacy-policy'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Política de Privacidade')
        self.assertContains(response, 'privacidade@example.com')
        self.assertContains(response, 'Exclusão da conta')


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DEFAULT_FROM_EMAIL='no-reply@lang.test',
    PRIVACY_CONTACT_EMAIL='privacidade@lang.test',
)
class AccountDeletionRequestViewTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            username='pessoa@example.com',
            email='pessoa@example.com',
            password='SenhaSegura123!',
        )

    def test_request_page_is_public(self):
        response = self.client.get(reverse('account-deletion-request'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Excluir minha conta')

    def test_known_account_receives_confirmation_without_exposing_account(self):
        response = self.client.post(
            reverse('account-deletion-request'),
            {'email': self.user.email, 'reason': 'Não uso mais.'},
            REMOTE_ADDR='192.0.2.10',
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Se houver uma conta ativa')
        deletion_request = AccountDeletionRequest.objects.get()
        self.assertEqual(
            deletion_request.status,
            AccountDeletionRequest.Status.AWAITING_CONFIRMATION,
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('confirmar-exclusao-conta', mail.outbox[0].body)
        self.assertNotIn(
            deletion_request.confirmation_token_hash,
            mail.outbox[0].body,
        )

    def test_unknown_account_gets_same_response_without_creating_request(self):
        response = self.client.post(
            reverse('account-deletion-request'),
            {'email': 'desconhecido@example.com'},
            REMOTE_ADDR='192.0.2.20',
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Se houver uma conta ativa')
        self.assertFalse(AccountDeletionRequest.objects.exists())
        self.assertEqual(len(mail.outbox), 0)

    def test_confirmation_requires_post_and_valid_token(self):
        self.client.post(
            reverse('account-deletion-request'),
            {'email': self.user.email},
            REMOTE_ADDR='192.0.2.30',
        )
        deletion_request = AccountDeletionRequest.objects.get()
        confirmation_url = re.search(
            r'https?://\S+',
            mail.outbox[0].body,
        ).group(0)
        parsed_url = urlparse(confirmation_url)
        token = parse_qs(parsed_url.query)['token'][0]

        get_response = self.client.get(confirmation_url)
        self.assertEqual(get_response.status_code, 200)
        deletion_request.refresh_from_db()
        self.assertEqual(
            deletion_request.status,
            AccountDeletionRequest.Status.AWAITING_CONFIRMATION,
        )

        post_response = self.client.post(
            parsed_url.path,
            {'token': token},
        )
        self.assertEqual(post_response.status_code, 200)
        self.assertContains(post_response, 'Solicitação confirmada')
        deletion_request.refresh_from_db()
        self.assertEqual(
            deletion_request.status,
            AccountDeletionRequest.Status.CONFIRMED,
        )
        self.assertIsNotNone(deletion_request.confirmed_at)
        self.assertTrue(self.user.__class__.objects.filter(pk=self.user.pk).exists())

    def test_expired_confirmation_link_is_rejected(self):
        self.client.post(
            reverse('account-deletion-request'),
            {'email': self.user.email},
            REMOTE_ADDR='192.0.2.40',
        )
        deletion_request = AccountDeletionRequest.objects.get()
        confirmation_url = re.search(
            r'https?://\S+',
            mail.outbox[0].body,
        ).group(0)
        deletion_request.confirmation_expires_at = timezone.now()
        deletion_request.save(update_fields=['confirmation_expires_at'])

        response = self.client.get(confirmation_url)

        self.assertEqual(response.status_code, 404)
