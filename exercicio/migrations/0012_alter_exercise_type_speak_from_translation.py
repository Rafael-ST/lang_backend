from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('exercicio', '0011_exercise_skill'),
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
                    (
                        'speak_english_from_translation',
                        'Falar em ingles a partir do portugues',
                    ),
                    ('just_audio', 'Apenas audio'),
                    ('matching_pairs', 'Associar traducao e ingles'),
                    ('complete_audio_text', 'Completar texto ouvindo audio'),
                    ('image_presentation', 'Apresentacao com imagem'),
                    (
                        'image_multiple_choice_english',
                        'Multipla escolha em ingles com imagem',
                    ),
                    (
                        'audio_multiple_choice_images',
                        'Multipla escolha de imagens com audio',
                    ),
                ],
                max_length=50,
            ),
        ),
    ]
