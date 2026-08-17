import hashlib
import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Q
from django.http import Http404
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import constant_time_compare
from django.views import View
from django.views.generic import FormView, TemplateView

from app.forms import AccountDeletionRequestForm
from authentication.models import AccountDeletionRequest


logger = logging.getLogger(__name__)
User = get_user_model()


class HomeView(TemplateView):
    template_name = 'app/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['contact_email'] = settings.PRIVACY_CONTACT_EMAIL
        return context


class PrivacyPolicyView(TemplateView):
    template_name = 'app/privacy_policy.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['privacy_contact_email'] = settings.PRIVACY_CONTACT_EMAIL
        context['contact_email'] = settings.PRIVACY_CONTACT_EMAIL
        return context


class AccountDeletionRequestView(FormView):
    form_class = AccountDeletionRequestForm
    template_name = 'app/account_deletion_request.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['contact_email'] = settings.PRIVACY_CONTACT_EMAIL
        return context

    def form_valid(self, form):
        if form.cleaned_data['website']:
            return self._success_response()

        email = form.cleaned_data['email']
        if self._is_rate_limited(email):
            return self._success_response()

        user = User.objects.filter(
            Q(email__iexact=email) | Q(username__iexact=email),
            is_active=True,
        ).first()

        if user:
            token = secrets.token_urlsafe(32)
            token_hash = _hash_confirmation_token(token)
            with transaction.atomic():
                AccountDeletionRequest.objects.filter(
                    email__iexact=email,
                    status=AccountDeletionRequest.Status.AWAITING_CONFIRMATION,
                    is_active=True,
                ).update(
                    status=AccountDeletionRequest.Status.CANCELLED,
                    is_active=False,
                )
                deletion_request = AccountDeletionRequest.objects.create(
                    email=email,
                    reason=form.cleaned_data['reason'].strip(),
                    confirmation_token_hash=token_hash,
                    confirmation_expires_at=timezone.now() + timedelta(hours=24),
                )

            confirmation_path = reverse(
                'account-deletion-confirm',
                kwargs={'request_id': deletion_request.pk},
            )
            confirmation_url = self.request.build_absolute_uri(
                f'{confirmation_path}?token={token}'
            )
            try:
                send_mail(
                    subject='Confirme a exclusão da sua conta no Lang',
                    message=(
                        'Recebemos uma solicitação de exclusão da sua conta '
                        'no Lang.\n\n'
                        f'Confirme a solicitação acessando: {confirmation_url}\n\n'
                        'O link expira em 24 horas. Se você não fez esta '
                        'solicitação, ignore este e-mail.'
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
                print(
                    '[account-deletion] Confirmação enviada com sucesso '
                    f'(request_id={deletion_request.pk}).',
                    flush=True,
                )
            except Exception as exc:
                print(
                    '[account-deletion] Falha ao enviar confirmação '
                    f'(request_id={deletion_request.pk}): '
                    f'{type(exc).__name__}: {exc}',
                    flush=True,
                )

        return self._success_response()

    def _is_rate_limited(self, email):
        forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR', '')
        remote_address = forwarded_for.split(',')[0].strip() or self.request.META.get(
            'REMOTE_ADDR',
            'unknown',
        )
        ip_digest = hashlib.sha256(remote_address.encode()).hexdigest()
        email_digest = hashlib.sha256(email.encode()).hexdigest()
        ip_key = f'account-deletion:ip:{ip_digest}'
        email_key = f'account-deletion:email:{email_digest}'

        if cache.get(ip_key) or cache.get(email_key):
            return True

        cache.set(ip_key, True, timeout=60)
        cache.set(email_key, True, timeout=300)
        return False

    def _success_response(self):
        return render(
            self.request,
            self.template_name,
            {
                'request_submitted': True,
                'contact_email': settings.PRIVACY_CONTACT_EMAIL,
            },
        )


class AccountDeletionConfirmView(View):
    template_name = 'app/account_deletion_confirm.html'

    def get(self, request, request_id):
        deletion_request = self._get_valid_request(request_id, request.GET.get('token'))
        return render(request, self.template_name, {
            'deletion_request': deletion_request,
            'token': request.GET.get('token'),
            'contact_email': settings.PRIVACY_CONTACT_EMAIL,
        })

    def post(self, request, request_id):
        token = request.POST.get('token')
        with transaction.atomic():
            deletion_request = self._get_valid_request(
                request_id,
                token,
                for_update=True,
            )
            deletion_request.status = AccountDeletionRequest.Status.CONFIRMED
            deletion_request.confirmed_at = timezone.now()
            deletion_request.save(
                update_fields=['status', 'confirmed_at', 'updated_at']
            )

        self._notify_privacy_contact(deletion_request)
        return render(request, self.template_name, {
            'confirmed': True,
            'contact_email': settings.PRIVACY_CONTACT_EMAIL,
        })

    def _get_valid_request(self, request_id, token, for_update=False):
        queryset = AccountDeletionRequest.objects
        if for_update:
            queryset = queryset.select_for_update()

        deletion_request = queryset.filter(
            pk=request_id,
            status=AccountDeletionRequest.Status.AWAITING_CONFIRMATION,
            is_active=True,
        ).first()
        supplied_hash = _hash_confirmation_token(token or '')
        if (
            deletion_request is None
            or deletion_request.confirmation_expires_at <= timezone.now()
            or not constant_time_compare(
                deletion_request.confirmation_token_hash,
                supplied_hash,
            )
        ):
            raise Http404('Solicitação inválida ou expirada.')
        return deletion_request

    def _notify_privacy_contact(self, deletion_request):
        if not settings.PRIVACY_CONTACT_EMAIL:
            print(
                '[account-deletion] Solicitação confirmada; configure '
                'PRIVACY_CONTACT_EMAIL para receber notificações '
                f'(request_id={deletion_request.pk}).',
                flush=True,
            )
            return

        try:
            send_mail(
                subject='Solicitação de exclusão confirmada no Lang',
                message=(
                    'Uma solicitação externa de exclusão de conta foi '
                    'confirmada.\n\n'
                    f'Identificador: {deletion_request.pk}\n'
                    'Acesse o Django Admin para revisar e processar.'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.PRIVACY_CONTACT_EMAIL],
                fail_silently=False,
            )
        except Exception:
            logger.exception(
                'Falha ao notificar o contato de privacidade sobre a '
                'solicitação %s.',
                deletion_request.pk,
            )


def _hash_confirmation_token(token):
    return hashlib.sha256(token.encode()).hexdigest()
