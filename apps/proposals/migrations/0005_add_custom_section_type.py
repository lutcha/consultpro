from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proposals', '0004_ensure_default_sections'),
    ]

    operations = [
        migrations.AlterField(
            model_name='proposalsection',
            name='section_type',
            field=models.CharField(
                choices=[
                    ('cover', 'Capa'),
                    ('executive_summary', 'Resumo Executivo'),
                    ('methodology', 'Metodologia'),
                    ('team', 'Equipa Tecnica'),
                    ('workplan', 'Plano de Trabalho'),
                    ('budget', 'Orcamento'),
                    ('annexes', 'Anexos'),
                    ('custom', 'Personalizada'),
                ],
                max_length=30,
            ),
        ),
    ]
