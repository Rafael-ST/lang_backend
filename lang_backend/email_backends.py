"""Send Django emails through Resend's HTTPS API (including Railway Hobby)."""

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.mail.backends.base import BaseEmailBackend


class ResendEmailBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        sent = 0
        for message in email_messages or []:
            if not message.recipients():
                continue
            try:
                self._send(message)
            except Exception:
                if not self.fail_silently:
                    raise
            else:
                sent += 1
        return sent

    def _send(self, message):
        if not settings.RESEND_API_KEY:
            raise ImproperlyConfigured('Defina RESEND_API_KEY para enviar e-mails.')
        if message.attachments:
            raise ValueError('O backend Resend ainda nao suporta anexos.')

        payload = {
            'from': message.from_email,
            'subject': message.subject,
            'html' if message.content_subtype == 'html' else 'text': message.body,
        }
        for field in ('to', 'cc', 'bcc', 'reply_to'):
            if getattr(message, field):
                payload[field] = list(getattr(message, field))
        for content, mimetype in getattr(message, 'alternatives', []):
            if mimetype != 'text/html':
                raise ValueError('Alternativa de e-mail nao suportada pelo backend Resend.')
            payload['html'] = content
        if message.extra_headers:
            payload['headers'] = message.extra_headers

        request = Request(
            'https://api.resend.com/emails',
            data=json.dumps(payload).encode('utf-8'),
            headers={
                'Authorization': f'Bearer {settings.RESEND_API_KEY}',
                'Content-Type': 'application/json',
                'User-Agent': 'Lang/1.0',
            },
            method='POST',
        )
        try:
            with urlopen(request, timeout=settings.EMAIL_TIMEOUT) as response:
                result = json.load(response)
        except HTTPError as exc:
            # Do not log response bodies, which may contain recipient information.
            status_code = exc.code
            exc.close()
            raise RuntimeError(
                f'Resend retornou HTTP {status_code}; consulte os logs no painel Resend.'
            ) from None
        except (URLError, TimeoutError):
            raise RuntimeError(
                'Falha de conexao ou timeout ao acessar a API Resend.'
            ) from None
        if not isinstance(result, dict) or not result.get('id'):
            raise RuntimeError('Resend nao confirmou o envio do e-mail.')
