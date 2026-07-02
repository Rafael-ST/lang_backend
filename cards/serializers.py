from rest_framework import serializers

from cards.models import Card


class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = [
            'id',
            'english_name',
            'international_name',
            'categoria',
            'audio',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
