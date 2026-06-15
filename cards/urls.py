from django.urls import include, path
from rest_framework.routers import DefaultRouter

from cards.views import CardViewSet

router = DefaultRouter()
router.register('cards', CardViewSet, basename='card')

urlpatterns = [
    path('', include(router.urls)),
]
