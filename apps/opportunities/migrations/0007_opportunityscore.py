import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('opportunities', '0006_consortium_b3'),
    ]

    operations = [
        migrations.CreateModel(
            name='OpportunityScore',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('strategic_fit', models.PositiveSmallIntegerField(default=0)),
                ('win_probability', models.PositiveSmallIntegerField(default=0)),
                ('margin', models.PositiveSmallIntegerField(default=0)),
                ('risk', models.PositiveSmallIntegerField(default=0)),
                ('resource', models.PositiveSmallIntegerField(default=0)),
                ('overall_score', models.PositiveSmallIntegerField(default=0)),
                ('confidence_score', models.DecimalField(decimal_places=2, default=0, max_digits=4)),
                ('ai_extracted_criteria', models.JSONField(blank=True, default=dict)),
                ('evaluation_weights', models.JSONField(blank=True, default=dict)),
                ('reasoning_trace', models.JSONField(blank=True, default=list)),
                ('input_snapshot', models.JSONField(blank=True, default=dict)),
                ('provider', models.CharField(default='deterministic', max_length=50)),
                ('model', models.CharField(blank=True, max_length=100)),
                ('scoring_version', models.CharField(default='opportunity_score_v1', max_length=40)),
                ('is_current', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                (
                    'opportunity',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='scores',
                        to='opportunities.opportunity',
                    ),
                ),
            ],
            options={
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['opportunity', 'is_current'], name='opportunity_score_current_idx'),
                    models.Index(fields=['scoring_version'], name='opportunity_score_version_idx'),
                ],
            },
        ),
    ]
