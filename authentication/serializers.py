from io import BytesIO
import uuid
import warnings

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.contrib.auth.password_validation import validate_password
from PIL import Image, ImageOps, UnidentifiedImageError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from perfil.models import DEFAULT_PROFILE_POINTS, Perfil


User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    default_error_messages = {
        **TokenObtainPairSerializer.default_error_messages,
        'no_active_account': 'E-mail ou senha inválidos.',
    }

    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user

        data['usuario'] = {
            'id': user.id,
            'username': user.get_username(),
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_staff': user.is_staff,
        }

        return data


class GoogleAuthSerializer(serializers.Serializer):
    id_token = serializers.CharField(trim_whitespace=True)


class ProfilePictureUploadSerializer(serializers.Serializer):
    MAX_FILE_SIZE = 5 * 1024 * 1024
    MAX_DIMENSION = 6000
    OUTPUT_SIZE = 1024
    ALLOWED_CONTENT_TYPES = {'image/jpeg', 'image/png', 'image/webp'}
    ALLOWED_FORMATS = {'JPEG', 'PNG', 'WEBP'}

    photo = serializers.FileField(allow_empty_file=False)

    def validate_photo(self, uploaded_file):
        if uploaded_file.size > self.MAX_FILE_SIZE:
            raise serializers.ValidationError('A imagem deve ter no maximo 5 MB.')

        if uploaded_file.content_type not in self.ALLOWED_CONTENT_TYPES:
            raise serializers.ValidationError('Envie uma imagem JPEG, PNG ou WebP.')

        try:
            with warnings.catch_warnings():
                warnings.simplefilter('error', Image.DecompressionBombWarning)
                uploaded_file.seek(0)
                with Image.open(uploaded_file) as image:
                    image.verify()

                uploaded_file.seek(0)
                with Image.open(uploaded_file) as image:
                    if image.format not in self.ALLOWED_FORMATS:
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
                    if max(width, height) > self.MAX_DIMENSION:
                        raise serializers.ValidationError(
                            'A imagem nao pode exceder 6000 pixels por lado.'
                        )

                    image = ImageOps.exif_transpose(image)
                    image.thumbnail(
                        (self.OUTPUT_SIZE, self.OUTPUT_SIZE),
                        Image.Resampling.LANCZOS,
                    )
                    if image.mode != 'RGB':
                        background = Image.new('RGB', image.size, 'white')
                        if 'A' in image.getbands():
                            background.paste(image, mask=image.getchannel('A'))
                        else:
                            background.paste(image)
                        image = background

                    output = BytesIO()
                    image.save(
                        output,
                        format='JPEG',
                        quality=88,
                        optimize=True,
                    )
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

        return ContentFile(
            output.getvalue(),
            name=f'{uuid.uuid4().hex}.jpg',
        )


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, validators=[validate_password])
    profile_picture_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_active',
            'is_staff',
            'is_superuser',
            'date_joined',
            'last_login',
            'password',
            'profile_picture_url',
        ]
        read_only_fields = [
            'id',
            'is_active',
            'is_staff',
            'is_superuser',
            'date_joined',
            'last_login',
            'profile_picture_url',
        ]

    def get_profile_picture_url(self, obj):
        picture = getattr(getattr(obj, 'perfil', None), 'profile_picture', None)
        if not picture:
            return None

        request = self.context.get('request')
        return request.build_absolute_uri(picture.url) if request else picture.url

    def validate(self, attrs):
        if self.instance is None and not attrs.get('password'):
            raise serializers.ValidationError({'password': 'Este campo e obrigatorio ao criar um usuario.'})

        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        Perfil.objects.get_or_create(
            user=user,
            defaults={'pontos': DEFAULT_PROFILE_POINTS},
        )
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance
