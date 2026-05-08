from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proposals', '0005_add_custom_section_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='aisuggestion',
            name='action',
            field=models.CharField(
                choices=[
                    ('draft_from_context', 'Gerar Rascunho'),
                    ('expand', 'Expandir'),
                    ('improve', 'Melhorar'),
                    ('summarize', 'Resumir'),
                    ('tone_formal', 'Ajustar Tom'),
                    ('translate_en', 'Traduzir EN'),
                ],
                max_length=30,
            ),
        ),
    ]
