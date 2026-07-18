from django.urls import include, path
from rest_framework.routers import DefaultRouter

from authentication.views import CustomTokenObtainPairView, CustomTokenRefreshView, GoogleAuthView, UserViewSet


router = DefaultRouter()
router.register('usuarios', UserViewSet, basename='usuario')


urlpatterns = [
    path('', include(router.urls)),
    path('auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('auth/google/', GoogleAuthView.as_view(), name='google_auth'),
]
