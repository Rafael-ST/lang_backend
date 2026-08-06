from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image

from ExerciseSet.models import ExerciseSet, ExerciseSetImage
from ExerciseSet.serializers import ExerciseSetImageSerializer, ExerciseSetSerializer
from niveis.models import Nivel
from subniveis.models import SubNivel

class ExerciseSetImageSerializerTests(TestCase):
    def setUp(self):
        level = Nivel.objects.create(nome='A1')
        self.sublevel = SubNivel.objects.create(
            nome='A1.1',
            subnivel=level,
        )
        self.exercise_set = ExerciseSet.objects.create(
            sublevel=self.sublevel,
            title='Primeiro conjunto',
        )

    def test_normalizes_valid_image_as_jpeg(self):
        image_bytes = BytesIO()
        Image.new('RGB', (800, 600), '#446688').save(
            image_bytes,
            format='PNG',
        )
        upload = SimpleUploadedFile(
            'set.png',
            image_bytes.getvalue(),
            content_type='image/png',
        )
        serializer = ExerciseSetImageSerializer(
            data={'name': 'Imagem reutilizavel', 'image': upload},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        normalized_image = serializer.validated_data['image']
        with Image.open(normalized_image) as image:
            self.assertEqual(image.format, 'JPEG')
            self.assertLessEqual(max(image.size), 1600)

    def test_rejects_invalid_image_content(self):
        upload = SimpleUploadedFile(
            'set.png',
            b'not-an-image',
            content_type='image/png',
        )
        serializer = ExerciseSetImageSerializer(
            data={'name': 'Imagem invalida', 'image': upload},
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('image', serializer.errors)

    def test_exercise_set_exposes_reusable_image_detail(self):
        reusable_image = ExerciseSetImage.objects.create(
            name='Saudacoes',
            image='exercise_sets/images/greetings.jpg',
        )
        self.exercise_set.image = reusable_image
        self.exercise_set.save(update_fields=['image'])

        serialized = ExerciseSetSerializer(self.exercise_set).data

        self.assertEqual(serialized['image'], reusable_image.id)
        self.assertEqual(serialized['image_detail']['name'], 'Saudacoes')
        self.assertIn('greetings.jpg', serialized['image_detail']['image'])
