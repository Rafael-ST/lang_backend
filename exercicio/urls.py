from django.urls import include, path
from rest_framework.routers import DefaultRouter

from exercicio.views import ExerciseViewSet

router = DefaultRouter()
router.register('exercises', ExerciseViewSet, basename='exercise')

urlpatterns = [
    path('', include(router.urls)),
]
