from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('proposals', '0007_proposal_pipeline_status_history'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProposalEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                (
                    'event_type',
                    models.CharField(
                        choices=[
                            ('submission', 'Submissao'),
                            ('evaluation', 'Avaliacao'),
                            ('shortlist', 'Shortlist'),
                            ('clarification', 'Clarificacao'),
                            ('bafo', 'BAFO'),
                            ('award', 'Adjudicacao'),
                            ('contracting', 'Contratacao'),
                            ('handover', 'Handover'),
                            ('note', 'Nota'),
                        ],
                        max_length=30,
                    ),
                ),
                ('title', models.CharField(max_length=255)),
                ('notes', models.TextField(blank=True)),
                ('occurred_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('external_url', models.URLField(blank=True)),
                ('attachment', models.FileField(blank=True, null=True, upload_to='proposals/events/%Y/%m/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                (
                    'created_by',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='proposal_events',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    'proposal',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='events',
                        to='proposals.proposal',
                    ),
                ),
            ],
            options={
                'ordering': ['-occurred_at', '-created_at'],
            },
        ),
    ]
