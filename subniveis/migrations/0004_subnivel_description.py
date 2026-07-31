from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subniveis', '0003_alter_subnivel_ordem'),
    ]

    operations = [
        migrations.AddField(
            model_name='subnivel',
            name='description',
            field=models.TextField(blank=True, verbose_name='Descricao'),
        ),
    ]
