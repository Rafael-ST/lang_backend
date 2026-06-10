from django.urls import include, path
from rest_framework.routers import DefaultRouter

from categorias.views import CategoriaViewSet

router = DefaultRouter()
router.register('categorias', CategoriaViewSet, basename='categoria')

urlpatterns = [
    path('', include(router.urls)),
]
