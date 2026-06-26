from django.urls import include, path
from rest_framework.routers import DefaultRouter

from niveis.views import NivelViewSet

router = DefaultRouter()
router.register('niveis', NivelViewSet, basename='nivel')

urlpatterns = [
    path('', include(router.urls)),
]
