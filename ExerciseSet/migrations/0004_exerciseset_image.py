from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ExerciseSet', '0003_exercisesetprogress_duration_ms'),
    ]

    operations = [
        migrations.AddField(
            model_name='exerciseset',
            name='image',
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to='exercise_sets/images/',
                verbose_name='Imagem',
            ),
        ),
    ]
