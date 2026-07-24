from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('perfil', '0002_perfil_pontos_recuperados_desde_ultimo_exercicio_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='perfil',
            name='profile_picture',
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to='profiles/',
                verbose_name='Foto do perfil',
            ),
        ),
    ]
