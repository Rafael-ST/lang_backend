from rest_framework import serializers

from cards.serializers import CardSerializer
from ExerciseSet.serializers import ExerciseSetSerializer
from exercicio.models import Exercise, ExerciseAttempt


class ExerciseSerializer(serializers.ModelSerializer):
    card_detail = CardSerializer(source='card', read_only=True)
    exercise_set_detail = ExerciseSetSerializer(source='exercise_set', read_only=True)

    class Meta:
        model = Exercise
        fields = [
            'id',
            'exercise_set',
            'exercise_set_detail',
            'card',
            'card_detail',
            'type',
            'prompt',
            'options',
            'answer_config',
            'is_active',
            'difficulty',
            'order',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ExerciseAttemptSerializer(serializers.ModelSerializer):
    exercise_detail = ExerciseSerializer(source='exercise', read_only=True)
    exercise_set_detail = ExerciseSetSerializer(source='exercise_set', read_only=True)
    user_detail = serializers.StringRelatedField(source='user', read_only=True)

    class Meta:
        model = ExerciseAttempt
        fields = [
            'id',
            'user',
            'user_detail',
            'exercise_set',
            'exercise_set_detail',
            'exercise',
            'exercise_detail',
            'is_correct',
            'answer',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
