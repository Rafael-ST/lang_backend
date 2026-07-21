from rest_framework import serializers

from niveis.models import Nivel
from subniveis.progress import is_sublevel_completed_for_user


class NivelSerializer(serializers.ModelSerializer):
    is_completed = serializers.SerializerMethodField()

    class Meta:
        model = Nivel
        fields = ['id', 'nome', 'is_active', 'is_completed', 'created_at', 'updated_at']
        read_only_fields = ['id', 'is_completed', 'created_at', 'updated_at']

    def get_is_completed(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None)

        if not user or not user.is_authenticated:
            return False

        active_sublevels = obj.subniveis.filter(is_active=True)

        if not active_sublevels.exists():
            return False

        return all(
            is_sublevel_completed_for_user(sublevel, user)
            for sublevel in active_sublevels
        )
