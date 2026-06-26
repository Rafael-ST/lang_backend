from rest_framework import serializers

from subniveis.models import SubNivel


class SubNivelSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubNivel
        fields = ['id', 'nome', 'subnivel', 'ordem', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
