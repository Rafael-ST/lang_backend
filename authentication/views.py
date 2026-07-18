from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token as google_id_token
from rest_framework import filters, permissions, status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from authentication.serializers import CustomTokenObtainPairSerializer, GoogleAuthSerializer, UserSerializer
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

        return build_token_response(user, include_refresh=True)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

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
    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        refresh = request.COOKIES.get(settings.JWT_REFRESH_COOKIE_NAME)

        if refresh and not data.get('refresh'):
            data['refresh'] = refresh

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.validated_data, status=status.HTTP_200_OK)


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

        if self.action == 'me':
            return [permissions.IsAuthenticated()]

        return super().get_permissions()

    @action(detail=False, methods=['get', 'patch'], url_path='me')
    def me(self, request):
        if request.method == 'GET':
            return Response(self.get_serializer(request.user).data)

        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
