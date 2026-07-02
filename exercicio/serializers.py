from rest_framework import serializers

from cards.serializers import CardSerializer
from exercicio.models import Exercise


class ExerciseSerializer(serializers.ModelSerializer):
    card_detail = CardSerializer(source='card', read_only=True)

    class Meta:
        model = Exercise
        fields = [
            'id',
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
