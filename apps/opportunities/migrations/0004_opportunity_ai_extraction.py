from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('opportunities', '0003_add_queued_ai_analysis_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='opportunity',
            name='ai_extraction',
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
