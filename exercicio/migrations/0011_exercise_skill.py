from django.db import migrations, models


SKILLS_BY_TYPE = {
    'just_audio': 'listening',
    'multiple_choice_audio_english': 'listening',
    'write_translation_from_audio': 'listening',
    'complete_audio_text': 'listening',
    'image_presentation': 'listening',
    'audio_multiple_choice_images': 'listening',
    'multiple_choice_translation': 'reading',
    'write_translation_from_text_audio': 'reading',
    'matching_pairs': 'reading',
    'image_multiple_choice_english': 'reading',
    'speak_written_text': 'speaking',
}


def classify_existing_exercises(apps, schema_editor):
    Exercise = apps.get_model('exercicio', 'Exercise')

    for exercise_type, skill in SKILLS_BY_TYPE.items():
        Exercise.objects.filter(type=exercise_type).update(skill=skill)


def reset_exercise_skills(apps, schema_editor):
    Exercise = apps.get_model('exercicio', 'Exercise')
    Exercise.objects.update(skill='reading')


class Migration(migrations.Migration):

    dependencies = [
        ('exercicio', '0010_alter_exercise_type_audio_multiple_choice_images'),
    ]

    operations = [
        migrations.AddField(
            model_name='exercise',
            name='skill',
            field=models.CharField(
                choices=[
                    ('listening', 'Listening'),
                    ('reading', 'Reading'),
                    ('speaking', 'Speaking'),
                ],
                default='reading',
                max_length=20,
            ),
        ),
        migrations.RunPython(
            classify_existing_exercises,
            reset_exercise_skills,
        ),
    ]
