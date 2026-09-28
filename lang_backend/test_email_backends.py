import json
from io import BytesIO
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

from django.core.exceptions import ImproperlyConfigured
from django.core.mail import EmailMessage, send_mail
from django.test import SimpleTestCase, override_settings

from .email_backends import ResendEmailBackend


@override_settings(
    EMAIL_BACKEND='lang_backend.email_backends.ResendEmailBackend',
    RESEND_API_KEY='re_test_key',
    EMAIL_TIMEOUT=10,
)
class ResendEmailBackendTests(SimpleTestCase):
    @patch('lang_backend.email_backends.urlopen')
    def test_send_mail_uses_https_and_preserves_reset_code(self, open_url):
        response = MagicMock()
        response.read.return_value = b'{"id": "email-id"}'
        open_url.return_value.__enter__.return_value = response

        count = send_mail(
            subject='Redefinir senha',
            message='Seu codigo: 123456',
            from_email='Lang <no-reply@example.com>',
            recipient_list=['user@example.com'],
        )

        self.assertEqual(count, 1)
        request = open_url.call_args.args[0]
        self.assertEqual(request.full_url, 'https://api.resend.com/emails')
        self.assertEqual(request.get_method(), 'POST')
        self.assertEqual(request.get_header('Authorization'), 'Bearer re_test_key')
        self.assertEqual(open_url.call_args.kwargs['timeout'], 10)
        self.assertEqual(json.loads(request.data), {
            'from': 'Lang <no-reply@example.com>',
            'to': ['user@example.com'],
            'subject': 'Redefinir senha',
            'text': 'Seu codigo: 123456',
        })

    @patch('lang_backend.email_backends.urlopen')
    def test_http_error_is_not_counted_as_success(self, open_url):
        open_url.side_effect = HTTPError(
            'https://api.resend.com/emails', 403, 'Forbidden', {},
            BytesIO(b'private provider response'),
        )
        with self.assertRaisesRegex(RuntimeError, 'HTTP 403'):
            self.message().send()

    @patch('lang_backend.email_backends.urlopen', side_effect=TimeoutError)
    def test_timeout_raises_or_returns_zero_when_fail_silently(self, open_url):
        with self.assertRaisesRegex(RuntimeError, 'timeout'):
            self.message().send()
        self.assertEqual(self.message().send(fail_silently=True), 0)

    @override_settings(RESEND_API_KEY='')
    @patch('lang_backend.email_backends.urlopen')
    def test_missing_key_fails_without_network_call(self, open_url):
        with self.assertRaises(ImproperlyConfigured):
            self.message().send()
        open_url.assert_not_called()

    @patch('lang_backend.email_backends.urlopen')
    def test_response_without_id_is_not_success(self, open_url):
        response = MagicMock()
        response.read.return_value = b'{}'
        open_url.return_value.__enter__.return_value = response
        with self.assertRaisesRegex(RuntimeError, 'nao confirmou'):
            self.message().send()

    @patch('lang_backend.email_backends.urlopen')
    def test_empty_messages_do_not_call_api(self, open_url):
        self.assertEqual(ResendEmailBackend().send_messages([]), 0)
        self.assertEqual(EmailMessage('Subject', 'Body', to=[]).send(), 0)
        open_url.assert_not_called()

    def message(self):
        return EmailMessage('Subject', 'Body', 'sender@example.com', ['user@example.com'])
