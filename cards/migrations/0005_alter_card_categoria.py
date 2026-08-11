from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cards', '0004_card_image'),
        ('categorias', '0002_alter_categoria_nome'),
    ]

    operations = [
        migrations.AlterField(
            model_name='card',
            name='categoria',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='categorias.categoria',
                verbose_name='Categoria',
            ),
        ),
    ]
