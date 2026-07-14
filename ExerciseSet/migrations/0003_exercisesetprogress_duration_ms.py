from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('ExerciseSet', '0002_exercisesetprogress'),
    ]

    operations = [
        migrations.AddField(
            model_name='exercisesetprogress',
            name='duration_ms',
            field=models.PositiveBigIntegerField(blank=True, null=True),
        ),
    ]
