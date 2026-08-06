from django.urls import include, path
from rest_framework.routers import DefaultRouter

from ExerciseSet.views import ExerciseSetImageViewSet, ExerciseSetProgressViewSet, ExerciseSetViewSet

router = DefaultRouter()
router.register('exercise-sets', ExerciseSetViewSet, basename='exercise-set')
router.register('exercise-set-images', ExerciseSetImageViewSet, basename='exercise-set-image')
router.register('exercise-set-progresses', ExerciseSetProgressViewSet, basename='exercise-set-progress')

urlpatterns = [
    path('', include(router.urls)),
]
