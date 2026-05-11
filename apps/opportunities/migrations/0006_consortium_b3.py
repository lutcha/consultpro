from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('opportunities', '0005_taxonomy_b1_b2'),
    ]

    operations = [
        migrations.AddField(
            model_name='opportunity',
            name='consortium_type',
            field=models.CharField(
                choices=[
                    ('solo', 'Solo'),
                    ('lead', 'Líder de Consórcio'),
                    ('partner', 'Parceiro de Consórcio'),
                    ('open', 'Aberto a Consórcio'),
                ],
                default='solo',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='opportunity',
            name='consortium_notes',
            field=models.TextField(blank=True, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='opportunity',
            name='partner_profiles',
            field=models.JSONField(blank=True, default=list),
        ),
    ]
