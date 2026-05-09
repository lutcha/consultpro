from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proposals', '0008_proposalevent'),
    ]

    operations = [
        migrations.AddField(
            model_name='proposalevent',
            name='artifact_type',
            field=models.CharField(
                blank=True,
                choices=[
                    ('', 'Sem artefacto'),
                    ('final_proposal', 'Proposta Final'),
                    ('contract', 'Contrato'),
                    ('handover', 'Handover Package'),
                    ('kickoff', 'Kickoff Pack'),
                    ('checklist', 'Checklist de Arranque'),
                    ('other', 'Outro'),
                ],
                max_length=30,
            ),
        ),
    ]
