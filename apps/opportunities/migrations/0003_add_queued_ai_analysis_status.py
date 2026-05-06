from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('opportunities', '0002_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='opportunity',
            name='ai_analysis_status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pendente'),
                    ('queued', 'Em fila'),
                    ('processing', 'A processar'),
                    ('completed', 'Completo'),
                    ('failed', 'Falhou'),
                ],
                default='pending',
                max_length=20,
            ),
        ),
    ]
