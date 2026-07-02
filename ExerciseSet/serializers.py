from rest_framework import serializers

from ExerciseSet.models import ExerciseSet, ExerciseSetProgress
from subniveis.serializers import SubNivelSerializer


class ExerciseSetSerializer(serializers.ModelSerializer):
    sublevel_detail = SubNivelSerializer(source='sublevel', read_only=True)
    progress = serializers.SerializerMethodField()
    is_completed = serializers.SerializerMethodField()

    class Meta:
        model = ExerciseSet
        fields = [
            'id',
            'sublevel',
            'sublevel_detail',
            'title',
            'description',
            'order',
            'is_active',
            'is_completed',
            'progress',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'is_completed', 'progress', 'created_at', 'updated_at']

    def get_progress(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        total_count = obj.exercises.filter(is_active=True).count()

        if not user or not user.is_authenticated:
            return {
                'status': ExerciseSetProgress.Status.NOT_STARTED,
                'completed_count': 0,
                'total_count': total_count,
                'completed_at': None,
            }

        completed_count = obj.exercises.filter(
            is_active=True,
            exerciseattempt__user=user,
            exerciseattempt__is_correct=True,
        ).distinct().count()
        attempted_count = obj.exercises.filter(
            is_active=True,
            exerciseattempt__user=user,
        ).distinct().count()
        progress = obj.progresses.filter(user=user).first()
        completed_at = progress.completed_at if progress else None

        if total_count > 0 and completed_count >= total_count:
            status_value = ExerciseSetProgress.Status.COMPLETED
        elif attempted_count > 0:
            status_value = ExerciseSetProgress.Status.IN_PROGRESS
        else:
            status_value = ExerciseSetProgress.Status.NOT_STARTED

        return {
            'status': status_value,
            'completed_count': completed_count,
            'total_count': total_count,
            'completed_at': completed_at,
        }

    def get_is_completed(self, obj):
        return self.get_progress(obj)['status'] == ExerciseSetProgress.Status.COMPLETED


class ExerciseSetProgressSerializer(serializers.ModelSerializer):
    exercise_set_detail = ExerciseSetSerializer(source='exercise_set', read_only=True)
    user_detail = serializers.StringRelatedField(source='user', read_only=True)

    class Meta:
        model = ExerciseSetProgress
        fields = [
            'id',
            'user',
            'user_detail',
            'exercise_set',
            'exercise_set_detail',
            'status',
            'completed_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
