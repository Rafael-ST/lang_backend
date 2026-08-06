from rest_framework import serializers

from io import BytesIO
import uuid
import warnings

from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError

from ExerciseSet.models import ExerciseSet, ExerciseSetImage, ExerciseSetProgress
from subniveis.serializers import SubNivelSerializer


class ExerciseSetImageSerializer(serializers.ModelSerializer):
    image = serializers.FileField(
        required=False,
        allow_empty_file=False,
    )

    class Meta:
        model = ExerciseSetImage
        fields = [
            'id',
            'name',
            'image',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_image(self, uploaded_file):
        if uploaded_file is None:
            return None
        if uploaded_file.size > 5 * 1024 * 1024:
            raise serializers.ValidationError('A imagem deve ter no maximo 5 MB.')
        if uploaded_file.content_type not in {
            'image/jpeg',
            'image/png',
            'image/webp',
        }:
            raise serializers.ValidationError('Envie uma imagem JPEG, PNG ou WebP.')

        try:
            with warnings.catch_warnings():
                warnings.simplefilter('error', Image.DecompressionBombWarning)
                uploaded_file.seek(0)
                with Image.open(uploaded_file) as image:
                    image.verify()

                uploaded_file.seek(0)
                with Image.open(uploaded_file) as image:
                    if image.format not in {'JPEG', 'PNG', 'WEBP'}:
                        raise serializers.ValidationError(
                            'O conteudo do arquivo nao e uma imagem permitida.'
                        )
                    if getattr(image, 'n_frames', 1) != 1:
                        raise serializers.ValidationError(
                            'Imagens animadas nao sao permitidas.'
                        )
                    width, height = image.size
                    if min(width, height) < 128:
                        raise serializers.ValidationError(
                            'A imagem deve ter pelo menos 128 x 128 pixels.'
                        )
                    if max(width, height) > 6000:
                        raise serializers.ValidationError(
                            'A imagem nao pode exceder 6000 pixels por lado.'
                        )

                    image = ImageOps.exif_transpose(image)
                    image.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
                    if image.mode != 'RGB':
                        background = Image.new('RGB', image.size, 'white')
                        if 'A' in image.getbands():
                            background.paste(image, mask=image.getchannel('A'))
                        else:
                            background.paste(image)
                        image = background

                    output = BytesIO()
                    image.save(output, format='JPEG', quality=88, optimize=True)
        except serializers.ValidationError:
            raise
        except (
            Image.DecompressionBombError,
            Image.DecompressionBombWarning,
            OSError,
            UnidentifiedImageError,
            ValueError,
        ):
            raise serializers.ValidationError(
                'O arquivo enviado nao e uma imagem valida.'
            )
        finally:
            uploaded_file.seek(0)

        return ContentFile(output.getvalue(), name=f'{uuid.uuid4().hex}.jpg')

    def update(self, instance, validated_data):
        old_image = instance.image if 'image' in validated_data else None
        updated_instance = super().update(instance, validated_data)

        if old_image and old_image.name != getattr(updated_instance.image, 'name', None):
            old_image.delete(save=False)

        return updated_instance


class ExerciseSetSerializer(serializers.ModelSerializer):
    image_detail = ExerciseSetImageSerializer(source='image', read_only=True)
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
            'image',
            'image_detail',
            'order',
            'is_active',
            'is_completed',
            'progress',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'image_detail', 'is_completed', 'progress', 'created_at', 'updated_at']

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
            'duration_ms',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'duration_ms', 'created_at', 'updated_at']
