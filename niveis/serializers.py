from rest_framework import serializers

from niveis.models import Nivel


class NivelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nivel
        fields = ['id', 'nome', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
