from rest_framework import serializers

from subniveis.models import SubNivel
from subniveis.progress import is_sublevel_completed_for_user


class SubNivelSerializer(serializers.ModelSerializer):
    is_completed = serializers.SerializerMethodField()

    class Meta:
        model = SubNivel
        fields = ['id', 'nome', 'description', 'subnivel', 'ordem', 'is_active', 'is_completed', 'created_at', 'updated_at']
        read_only_fields = ['id', 'is_completed', 'created_at', 'updated_at']

    def get_is_completed(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None)

        if not user or not user.is_authenticated:
            return False

        return is_sublevel_completed_for_user(obj, user)
