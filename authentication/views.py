from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import filters, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from authentication.serializers import CustomTokenObtainPairSerializer, UserSerializer


User = get_user_model()


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
