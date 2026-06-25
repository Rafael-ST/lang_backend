from django.urls import include, path
from rest_framework.routers import DefaultRouter

from perfil.views import PerfilViewSet

router = DefaultRouter()
router.register('perfis', PerfilViewSet, basename='perfil')

urlpatterns = [
    path('', include(router.urls)),
]
