from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('exercicio', '0004_exerciseattempt'),
    ]

    operations = [
        migrations.AlterField(
            model_name='exercise',
            name='type',
            field=models.CharField(
                choices=[
                    ('multiple_choice_translation', 'Multipla escolha'),
                    ('multiple_choice_audio_english', 'Multipla escolha com audio em ingles'),
                    ('write_translation_from_text_audio', 'Escrever com texto e audio'),
                    ('write_translation_from_audio', 'Escrever ouvindo audio'),
                    ('speak_written_text', 'Falar texto escrito'),
                    ('just_audio', 'Apenas audio'),
                ],
                max_length=50,
            ),
        ),
    ]
