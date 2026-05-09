import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0004_projectartifact_phase_projectphase_title'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectdeliverable',
            name='phase',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='deliverables',
                to='projects.projectphase',
            ),
        ),
    ]
