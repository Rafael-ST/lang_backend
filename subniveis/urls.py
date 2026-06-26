from django.urls import include, path
from rest_framework.routers import DefaultRouter

from subniveis.views import SubNivelViewSet

router = DefaultRouter()
router.register('subniveis', SubNivelViewSet, basename='subnivel')

urlpatterns = [
    path('', include(router.urls)),
]
