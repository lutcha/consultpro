from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0005_projectdeliverable_phase'),
    ]

    operations = [
        # Remove unique_together so projects can have multiple phases of any type
        migrations.AlterUniqueTogether(
            name='projectphase',
            unique_together=set(),
        ),
        # Extend name field to accept 'custom' value and increase max_length for safety
        migrations.AlterField(
            model_name='projectphase',
            name='name',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('initiating', 'Iniciação'),
                    ('planning', 'Planeamento'),
                    ('executing', 'Execução'),
                    ('monitoring', 'Monitoramento e Controlo'),
                    ('closing', 'Encerramento'),
                    ('custom', 'Personalizado'),
                ],
                default='custom',
            ),
        ),
    ]
