from django.urls import include, path
from rest_framework.routers import DefaultRouter

from exercicio.views import ExerciseAttemptViewSet, ExerciseViewSet

router = DefaultRouter()
router.register('exercises', ExerciseViewSet, basename='exercise')
router.register('exercise-attempts', ExerciseAttemptViewSet, basename='exercise-attempt')

urlpatterns = [
    path('', include(router.urls)),
]
