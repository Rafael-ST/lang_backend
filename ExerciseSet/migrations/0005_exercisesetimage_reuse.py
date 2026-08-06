import uuid

from django.db import migrations, models
import django.db.models.deletion


def migrate_existing_images(apps, schema_editor):
    ExerciseSet = apps.get_model('ExerciseSet', 'ExerciseSet')
    ExerciseSetImage = apps.get_model('ExerciseSet', 'ExerciseSetImage')

    for exercise_set in ExerciseSet.objects.exclude(image=''):
        if not exercise_set.image:
            continue

        reusable_image = ExerciseSetImage.objects.create(
            name=exercise_set.title,
            image=exercise_set.image,
        )
        exercise_set.image_reference = reusable_image
        exercise_set.save(update_fields=['image_reference'])


def restore_direct_images(apps, schema_editor):
    ExerciseSet = apps.get_model('ExerciseSet', 'ExerciseSet')

    for exercise_set in ExerciseSet.objects.select_related('image_reference'):
        if exercise_set.image_reference:
            exercise_set.image = exercise_set.image_reference.image
            exercise_set.save(update_fields=['image'])


class Migration(migrations.Migration):

    dependencies = [
        ('ExerciseSet', '0004_exerciseset_image'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExerciseSetImage',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
                ('is_active', models.BooleanField(default=True, verbose_name='Ativo')),
                ('name', models.CharField(max_length=255, verbose_name='Nome')),
                ('image', models.ImageField(upload_to='exercise_sets/images/', verbose_name='Imagem')),
            ],
            options={
                'verbose_name': 'Imagem de conjunto de exercicios',
                'verbose_name_plural': 'Imagens de conjuntos de exercicios',
                'ordering': ['name'],
            },
        ),
        migrations.AddField(
            model_name='exerciseset',
            name='image_reference',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='exercise_sets',
                to='ExerciseSet.exercisesetimage',
                verbose_name='Imagem',
            ),
        ),
        migrations.RunPython(migrate_existing_images, restore_direct_images),
        migrations.RemoveField(
            model_name='exerciseset',
            name='image',
        ),
        migrations.RenameField(
            model_name='exerciseset',
            old_name='image_reference',
            new_name='image',
        ),
    ]
