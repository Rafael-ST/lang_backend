from django.contrib.auth import get_user_model
from rest_framework import serializers

from perfil.models import Perfil


User = get_user_model()


class PerfilSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Perfil
        fields = [
            'id',
            'user',
            'username',
            'pontos',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'username', 'created_at', 'updated_at']

    def validate_user(self, user):
        request = self.context.get('request')

        if request and request.user.is_authenticated and not request.user.is_staff and user != request.user:
            raise serializers.ValidationError('Voce so pode alterar o seu proprio perfil.')

        return user

    def validate(self, attrs):
        request = self.context.get('request')
        user = attrs.get('user')

        if self.instance is None and user is None and request and not request.user.is_staff:
            user = request.user

        if self.instance is None and user is None:
            raise serializers.ValidationError({'user': 'Este campo e obrigatorio.'})

        if self.instance is None and Perfil.objects.filter(user=user).exists():
            raise serializers.ValidationError({'user': 'Este usuario ja possui um perfil.'})

        if self.instance is not None and user is not None and user != self.instance.user:
            if Perfil.objects.filter(user=user).exists():
                raise serializers.ValidationError({'user': 'Este usuario ja possui um perfil.'})

        return attrs
