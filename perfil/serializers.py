from django.contrib.auth import get_user_model
from django.db.models import Avg
from rest_framework import serializers

from perfil.models import Perfil


User = get_user_model()


class PerfilSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)
    username = serializers.CharField(source='user.username', read_only=True)
    average_exercise_set_time_ms = serializers.SerializerMethodField()
    learned_words_count = serializers.SerializerMethodField()
    completed_exercises_count = serializers.SerializerMethodField()

    class Meta:
        model = Perfil
        fields = [
            'id',
            'user',
            'username',
            'pontos',
            'average_exercise_set_time_ms',
            'learned_words_count',
            'completed_exercises_count',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'username',
            'average_exercise_set_time_ms',
            'learned_words_count',
            'completed_exercises_count',
            'created_at',
            'updated_at',
        ]

    def get_average_exercise_set_time_ms(self, obj):
        average = obj.user.exercisesetprogress_set.filter(
            status='completed',
            duration_ms__isnull=False,
        ).aggregate(value=Avg('duration_ms'))['value']

        return round(average) if average is not None else None

    def get_learned_words_count(self, obj):
        return obj.user.card_accesses.count()

    def get_completed_exercises_count(self, obj):
        return obj.user.exerciseattempt_set.filter(
            is_correct=True,
        ).values('exercise_id').distinct().count()

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
