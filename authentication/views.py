from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
import secrets
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token as google_id_token
from rest_framework import filters, permissions, serializers, status, viewsets
from rest_framework.parsers import MultiPartParser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from authentication.serializers import (
    CustomTokenObtainPairSerializer,
    GoogleAuthSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    ProfilePictureUploadSerializer,
    UserSerializer,
)
from authentication.models import PasswordResetCode
from perfil.models import DEFAULT_PROFILE_POINTS, Perfil


User = get_user_model()


def serialize_authenticated_user(user):
    return {
        'id': user.id,
        'username': user.get_username(),
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'is_staff': user.is_staff,
    }


def build_token_response(user, include_refresh=False):
    refresh = CustomTokenObtainPairSerializer.get_token(user)
    data = {
        'access': str(refresh.access_token),
        'usuario': serialize_authenticated_user(user),
    }
    if include_refresh:
        data['refresh'] = str(refresh)

    response = Response(data, status=status.HTTP_200_OK)
    response.set_cookie(
        key=settings.JWT_REFRESH_COOKIE_NAME,
        value=str(refresh),
        httponly=True,
        secure=settings.JWT_REFRESH_COOKIE_SECURE,
        samesite=settings.JWT_REFRESH_COOKIE_SAMESITE,
        max_age=settings.JWT_REFRESH_COOKIE_MAX_AGE,
        path='/',
    )
    return response


class GoogleAuthView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'auth'

    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        allowed_client_ids = settings.GOOGLE_OAUTH_CLIENT_IDS
        if not allowed_client_ids:
            return Response(
                {'detail': 'Login Google nao configurado no servidor.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        try:
            claims = google_id_token.verify_oauth2_token(
                serializer.validated_data['id_token'],
                GoogleRequest(),
                audience=None,
            )
        except (ValueError, TypeError):
            return Response(
                {'detail': 'Token Google invalido ou expirado.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if claims.get('aud') not in allowed_client_ids:
            return Response(
                {'detail': 'Token Google nao pertence a este aplicativo.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        email = str(claims.get('email') or '').strip().lower()
        email_verified = claims.get('email_verified') in (True, 'true', 'True', '1')
        if not email or not email_verified:
            return Response(
                {'detail': 'O Google nao confirmou o e-mail desta conta.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            user = User.objects.filter(email__iexact=email).first()
            if user is None:
                user = User.objects.filter(username__iexact=email).first()

            if user is None:
                user = User(
                    username=email,
                    email=email,
                    first_name=str(claims.get('given_name') or '')[:150],
                    last_name=str(claims.get('family_name') or '')[:150],
                )
                user.set_unusable_password()
                user.save()
            else:
                changed_fields = []
                if not user.email:
                    user.email = email
                    changed_fields.append('email')
                if not user.first_name and claims.get('given_name'):
                    user.first_name = str(claims['given_name'])[:150]
                    changed_fields.append('first_name')
                if not user.last_name and claims.get('family_name'):
                    user.last_name = str(claims['family_name'])[:150]
                    changed_fields.append('last_name')
                if changed_fields:
                    user.save(update_fields=changed_fields)

            if not user.is_active:
                return Response(
                    {'detail': 'Esta conta esta desativada.'},
                    status=status.HTTP_403_FORBIDDEN,
                )

            Perfil.objects.get_or_create(
                user=user,
                defaults={'pontos': DEFAULT_PROFILE_POINTS},
            )

        return build_token_response(user)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    throttle_scope = 'auth'

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        refresh = response.data.get('refresh')
        access = response.data.get('access')
        usuario = response.data.get('usuario')

        if refresh is None:
            return Response({'detail': 'Erro ao gerar refresh token'}, status=status.HTTP_400_BAD_REQUEST)

        res = Response(
            {
                'access': access,
                'usuario': usuario,
            },
            status=status.HTTP_200_OK,
        )

        res.set_cookie(
            key=settings.JWT_REFRESH_COOKIE_NAME,
            value=refresh,
            httponly=True,
            secure=settings.JWT_REFRESH_COOKIE_SECURE,
            samesite=settings.JWT_REFRESH_COOKIE_SAMESITE,
            max_age=settings.JWT_REFRESH_COOKIE_MAX_AGE,
            path='/',
        )

        return res


class CustomTokenRefreshView(TokenRefreshView):
    throttle_scope = 'auth'

    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        refresh = request.COOKIES.get(settings.JWT_REFRESH_COOKIE_NAME)

        if refresh and not data.get('refresh'):
            data['refresh'] = refresh

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        rotated_refresh = serializer.validated_data.get('refresh')
        response_data = dict(serializer.validated_data)
        response_data.pop('refresh', None)
        response = Response(response_data, status=status.HTTP_200_OK)
        if rotated_refresh:
            response.set_cookie(
                key=settings.JWT_REFRESH_COOKIE_NAME,
                value=rotated_refresh,
                httponly=True,
                secure=settings.JWT_REFRESH_COOKIE_SECURE,
                samesite=settings.JWT_REFRESH_COOKIE_SAMESITE,
                max_age=settings.JWT_REFRESH_COOKIE_MAX_AGE,
                path='/',
            )
        return response


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh = (
            request.data.get('refresh')
            or request.COOKIES.get(settings.JWT_REFRESH_COOKIE_NAME)
        )
        if refresh:
            try:
                RefreshToken(refresh).blacklist()
            except TokenError:
                pass

        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie(
            settings.JWT_REFRESH_COOKIE_NAME,
            path='/',
            samesite=settings.JWT_REFRESH_COOKIE_SAMESITE,
        )
        return response


class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'password_reset_request'

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email'].strip().lower()
        user = User.objects.filter(
            Q(email__iexact=email) | Q(username__iexact=email),
            is_active=True,
        ).first()

        if user:
            code = f'{secrets.randbelow(1_000_000):06d}'
            with transaction.atomic():
                PasswordResetCode.objects.filter(
                    user=user,
                    used_at__isnull=True,
                    is_active=True,
                ).update(is_active=False)
                PasswordResetCode.objects.create(
                    user=user,
                    code_hash=make_password(code),
                    expires_at=timezone.now() + timedelta(minutes=15),
                )

            try:
                sent_count = send_mail(
                    subject='Código para redefinir sua senha no Lang',
                    message=(
                        f'Seu código de redefinição é: {code}\n\n'
                        'Ele expira em 15 minutos. Se você não solicitou esta '
                        'alteração, ignore esta mensagem.'
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
                if sent_count == 1:
                    print(
                        '[password-reset] E-mail enviado com sucesso '
                        f'(user_id={user.pk}).',
                        flush=True,
                    )
                else:
                    print(
                        '[password-reset] E-mail não enviado: o backend de '
                        f'e-mail retornou {sent_count} envios (user_id={user.pk}).',
                        flush=True,
                    )
            except Exception as exc:
                print(
                    '[password-reset] Falha ao enviar e-mail '
                    f'(user_id={user.pk}): {type(exc).__name__}: {exc}',
                    flush=True,
                )
        else:
            print(
                '[password-reset] Nenhum e-mail enviado: usuário ativo '
                'não encontrado.',
                flush=True,
            )

        return Response(
            {
                'detail': (
                    'Se o e-mail estiver cadastrado, enviaremos um código '
                    'de redefinição.'
                ),
            },
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'password_reset_confirm'

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email'].strip().lower()

        with transaction.atomic():
            reset_code = (
                PasswordResetCode.objects.select_for_update()
                .select_related('user')
                .filter(
                    Q(user__email__iexact=email) |
                    Q(user__username__iexact=email),
                    used_at__isnull=True,
                    is_active=True,
                )
                .order_by('-created_at')
                .first()
            )

            if (
                not reset_code
                or reset_code.expires_at <= timezone.now()
                or reset_code.attempts >= 5
            ):
                raise serializers.ValidationError({
                    'code': 'Código inválido ou expirado.'
                })

            if not check_password(
                serializer.validated_data['code'],
                reset_code.code_hash,
            ):
                reset_code.attempts += 1
                if reset_code.attempts >= 5:
                    reset_code.is_active = False
                reset_code.save(
                    update_fields=['attempts', 'is_active', 'updated_at']
                )
                raise serializers.ValidationError({
                    'code': 'Código inválido ou expirado.'
                })

            user = reset_code.user
            user.set_password(serializer.validated_data['new_password'])
            user.save(update_fields=['password'])
            reset_code.used_at = timezone.now()
            reset_code.is_active = False
            reset_code.save(
                update_fields=['used_at', 'is_active', 'updated_at']
            )
            PasswordResetCode.objects.filter(
                user=user,
                used_at__isnull=True,
                is_active=True,
            ).exclude(pk=reset_code.pk).update(is_active=False)

        return Response(
            {'detail': 'Senha redefinida com sucesso.'},
            status=status.HTTP_200_OK,
        )


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('username')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['username', 'email', 'first_name', 'last_name', 'date_joined', 'last_login', 'is_active']
    ordering = ['username']

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]

        if self.action in ('me', 'profile_picture'):
            return [permissions.IsAuthenticated()]

        return super().get_permissions()

    @action(detail=False, methods=['get', 'patch', 'delete'], url_path='me')
    def me(self, request):
        if request.method == 'GET':
            return Response(self.get_serializer(request.user).data)

        if request.method == 'DELETE':
            with transaction.atomic():
                request.user.delete()

            response = Response(status=status.HTTP_204_NO_CONTENT)
            response.delete_cookie(
                settings.JWT_REFRESH_COOKIE_NAME,
                path='/',
                samesite=settings.JWT_REFRESH_COOKIE_SAMESITE,
            )
            return response

        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['post', 'delete'],
        url_path='me/photo',
        parser_classes=[MultiPartParser],
    )
    def profile_picture(self, request):
        profile, _ = Perfil.objects.get_or_create(
            user=request.user,
            defaults={'pontos': DEFAULT_PROFILE_POINTS},
        )

        if request.method == 'DELETE':
            old_picture = profile.profile_picture
            profile.profile_picture = None
            profile.save(update_fields=['profile_picture', 'updated_at'])
            if old_picture:
                old_picture.delete(save=False)
            user_data = self.get_serializer(request.user).data
            user_data['profile_picture_url'] = None
            return Response(
                user_data,
                status=status.HTTP_200_OK,
            )

        upload_serializer = ProfilePictureUploadSerializer(data=request.data)
        upload_serializer.is_valid(raise_exception=True)
        old_picture = profile.profile_picture
        profile.profile_picture = upload_serializer.validated_data['photo']
        profile.save(update_fields=['profile_picture', 'updated_at'])
        if old_picture and old_picture.name != profile.profile_picture.name:
            old_picture.delete(save=False)

        user_data = self.get_serializer(request.user).data
        user_data['profile_picture_url'] = request.build_absolute_uri(
            profile.profile_picture.url
        )
        return Response(
            user_data,
            status=status.HTTP_200_OK,
        )
