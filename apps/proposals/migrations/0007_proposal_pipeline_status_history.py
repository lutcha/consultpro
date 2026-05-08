from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


PROPOSAL_STATUS_CHOICES = [
    ('draft', 'Rascunho'),
    ('in_review', 'Em Revisao'),
    ('qc_check', 'QC em Curso'),
    ('ready_for_submission', 'Pronta para Submissao'),
    ('approved', 'Aprovada'),
    ('submitted', 'Submetida'),
    ('under_evaluation', 'Em Avaliacao'),
    ('rejected', 'Rejeitada'),
    ('shortlisted', 'Shortlisted'),
    ('clarifications_requested', 'Clarificacoes Pedidas'),
    ('bafo', 'BAFO'),
    ('awarded', 'Adjudicada'),
    ('contract_negotiation', 'Negociacao de Contrato'),
    ('contract_signed', 'Contrato Assinado'),
    ('project_initiation', 'Arranque de Projeto'),
    ('won', 'Ganha'),
    ('lost', 'Perdida'),
]


class Migration(migrations.Migration):

    dependencies = [
        ('proposals', '0006_add_proposal_ai_actions'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='proposal',
            name='status',
            field=models.CharField(
                choices=PROPOSAL_STATUS_CHOICES,
                default='draft',
                max_length=30,
            ),
        ),
        migrations.CreateModel(
            name='ProposalStatusHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=PROPOSAL_STATUS_CHOICES, max_length=30)),
                ('note', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                (
                    'changed_by',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='proposal_status_changes',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    'proposal',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='status_history',
                        to='proposals.proposal',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Proposal status history',
                'verbose_name_plural': 'Proposal status histories',
                'ordering': ['-created_at'],
            },
        ),
    ]
