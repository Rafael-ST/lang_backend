import json
from datetime import timedelta
from unittest.mock import patch

from django.contrib import admin
from django.contrib.admin.models import ADDITION, CHANGE, DELETION, LogEntry
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.cache import cache
from django.db import IntegrityError
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from app.audit import capturar_estado
from app.log_actions import ACESSO_NEGADO, LOGIN, LOGIN_FALHOU, REDEFINICAO_SENHA
from authentication.audit import USUARIO_AUDITORIA_USERNAME
from authentication.models import PasswordResetCode
from categorias.models import Categoria


User = get_user_model()


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class AuditTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username='aluno', password='senha-segura-123')
        self.staff = User.objects.create_user(username='admin', password='senha-segura-123', is_staff=True)
        self.client.force_authenticate(self.staff)
        self.category = Categoria.objects.create(nome='Original')
        self.url = reverse('categoria-detail', args=[self.category.pk])

    def test_crud_and_noop(self):
        response = self.client.post(reverse('categoria-list'), {'nome': 'Nova'})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(LogEntry.objects.get().action_flag, ADDITION)
        LogEntry.objects.all().delete()
        response = self.client.patch(
            self.url, {'nome': 'Alterada'}, REMOTE_ADDR='203.0.113.10',
            HTTP_X_FORWARDED_FOR='198.51.100.10',
        )
        self.assertEqual(response.status_code, 200)
        entry = LogEntry.objects.get()
        self.assertEqual(entry.user_id, self.staff.pk)
        self.assertEqual(entry.action_flag, CHANGE)
        data = json.loads(entry.change_message)
        self.assertEqual(data['ip'], '203.0.113.10')
        self.assertEqual(data['alteracoes'], {'nome': {'antes': 'Original', 'depois': 'Alterada'}})
        self.client.patch(self.url, {'nome': 'Alterada'})
        self.assertEqual(LogEntry.objects.count(), 1)
        self.assertEqual(self.client.delete(self.url).status_code, 204)
        self.assertTrue(LogEntry.objects.filter(action_flag=DELETION, object_id=str(self.category.pk)).exists())

    def test_write_and_delete_rollback_if_audit_fails(self):
        for method, url, data in (
            ('post', reverse('categoria-list'), {'nome': 'Nova'}),
            ('patch', self.url, {'nome': 'Alterada'}),
            ('delete', self.url, {}),
        ):
            with self.subTest(method=method):
                with patch('app.audit.LogEntry.objects.create', side_effect=IntegrityError('audit failed')):
                    with self.assertRaises(IntegrityError):
                        getattr(self.client, method)(url, data)
                self.category.refresh_from_db()
                self.assertEqual(self.category.nome, 'Original')
                self.assertEqual(Categoria.objects.count(), 1)

    def test_permission_denied_and_admin_readonly(self):
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.patch(self.url, {'nome': 'Proibido'}).status_code, 403)
        entry = LogEntry.objects.get(action_flag=ACESSO_NEGADO)
        self.assertEqual(entry.user_id, self.user.pk)
        model_admin = admin.site._registry[LogEntry]
        self.assertFalse(model_admin.has_add_permission(None))
        self.assertFalse(model_admin.has_change_permission(None, entry))
        self.assertFalse(model_admin.has_delete_permission(None, entry))
        self.assertIn('IsAdminUser', model_admin.detalhes(entry))

    def test_self_update_masks_password_and_self_delete_survives(self):
        self.client.force_authenticate(self.user)
        response = self.client.patch(reverse('usuario-me'), {'password': 'outra-senha-segura-789'})
        self.assertEqual(response.status_code, 200)
        entry = LogEntry.objects.get(action_flag=CHANGE)
        self.assertEqual(json.loads(entry.change_message)['alteracoes']['password'], {
            'alterado': True, 'valores_ocultos': True,
        })
        self.user.refresh_from_db()
        self.assertNotIn(self.user.password, entry.change_message)
        self.assertNotIn('outra-senha', entry.change_message)
        user_id = self.user.pk
        self.assertEqual(self.client.delete(reverse('usuario-me')).status_code, 204)
        entry = LogEntry.objects.get(action_flag=DELETION)
        self.assertEqual(entry.object_id, str(user_id))
        self.assertEqual(entry.user.username, USUARIO_AUDITORIA_USERNAME)
        self.assertFalse(entry.user.is_active)
        self.assertFalse(entry.user.has_usable_password())

    def test_public_signup_and_file_snapshot(self):
        self.client.force_authenticate(None)
        response = self.client.post(reverse('usuario-list'), {
            'username': 'novo', 'password': 'cadastro-seguro-123',
        })
        self.assertEqual(response.status_code, 201)
        entry = LogEntry.objects.get(action_flag=ADDITION)
        self.assertEqual(entry.user_id, response.data['id'])
        profile = entry.user.perfil
        profile.profile_picture = 'profiles/test.jpg'
        self.assertEqual(capturar_estado(profile)['profile_picture'], 'profiles/test.jpg')

    def test_password_login_success_and_failure(self):
        self.client.force_authenticate(None)
        url = reverse('token_obtain_pair')
        response = self.client.post(url, {'username': 'aluno', 'password': 'senha-segura-123'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(LogEntry.objects.get(action_flag=LOGIN).user_id, self.user.pk)
        for username in ['aluno', 'desconhecido']:
            self.assertEqual(self.client.post(url, {'username': username, 'password': 'segredo-errado'}).status_code, 401)
        self.assertEqual(LogEntry.objects.filter(action_flag=LOGIN_FALHOU).count(), 2)
        self.assertNotIn('segredo-errado', str(list(LogEntry.objects.values_list('change_message', flat=True))))
        self.assertFalse(User.objects.get(username=USUARIO_AUDITORIA_USERNAME).is_active)

    def test_password_reset_is_atomic_and_does_not_log_code(self):
        self.client.force_authenticate(None)
        reset = PasswordResetCode.objects.create(
            user=self.user, code_hash=make_password('123456'),
            expires_at=timezone.now() + timedelta(minutes=15),
        )
        # A view exige endereço válido; a busca aceita username ou e-mail único.
        self.user.email = 'aluno@example.com'
        self.user.save(update_fields=['email'])
        payload = {'email': self.user.email, 'code': '123456', 'new_password': 'nova-senha-segura-123'}
        with patch('authentication.audit.LogEntry.objects.create', side_effect=IntegrityError('audit failed')):
            with self.assertRaises(IntegrityError):
                self.client.post(reverse('password_reset_confirm'), payload)
        reset.refresh_from_db()
        self.user.refresh_from_db()
        self.assertIsNone(reset.used_at)
        self.assertTrue(self.user.check_password('senha-segura-123'))
        self.assertEqual(self.client.post(reverse('password_reset_confirm'), payload).status_code, 200)
        entry = LogEntry.objects.get(action_flag=REDEFINICAO_SENHA)
        for secret in ('123456', reset.code_hash, payload['new_password']):
            self.assertNotIn(secret, entry.change_message)

    def test_malformed_login_is_audited_without_echoing_payload(self):
        self.client.force_authenticate(None)
        for payload in ([], {'password': 'segredo-nao-logavel'}):
            response = self.client.post(reverse('token_obtain_pair'), payload, format='json')
            self.assertEqual(response.status_code, 400)
        self.assertEqual(LogEntry.objects.filter(action_flag=LOGIN_FALHOU).count(), 2)
        self.assertNotIn('segredo-nao-logavel', str(list(LogEntry.objects.values_list('change_message', flat=True))))

    @override_settings(GOOGLE_OAUTH_CLIENT_IDS=['test-client'])
    @patch('authentication.views.google_id_token.verify_oauth2_token')
    def test_google_login_audits_verified_user_only(self, verify):
        self.client.force_authenticate(None)
        verify.return_value = {
            'aud': 'test-client', 'email': 'google@example.com', 'email_verified': True,
        }
        response = self.client.post(reverse('google_auth'), {'id_token': 'token-nao-logavel'})
        self.assertEqual(response.status_code, 200)
        entry = LogEntry.objects.get(action_flag=LOGIN)
        self.assertEqual(entry.user.email, 'google@example.com')
        self.assertNotIn('token-nao-logavel', entry.change_message)

    def test_admin_escapes_values(self):
        self.client.patch(self.url, {'nome': '<script>alert(1)</script>'})
        html = admin.site._registry[LogEntry].detalhes(LogEntry.objects.get())
        self.assertNotIn('<script>', html)
        self.assertIn('&lt;script&gt;', html)
