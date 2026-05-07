from django.db import migrations


DEFAULT_PROPOSAL_SECTIONS = [
    ('cover', 'Capa', 1),
    ('executive_summary', 'Resumo Executivo', 2),
    ('methodology', 'Metodologia', 3),
    ('team', 'Equipa Tecnica', 4),
    ('workplan', 'Plano de Trabalho', 5),
    ('budget', 'Orcamento', 6),
    ('annexes', 'Anexos', 7),
]


def ensure_default_sections(apps, schema_editor):
    Proposal = apps.get_model('proposals', 'Proposal')
    ProposalSection = apps.get_model('proposals', 'ProposalSection')

    for proposal in Proposal.objects.all():
        for section_type, title, order in DEFAULT_PROPOSAL_SECTIONS:
            ProposalSection.objects.get_or_create(
                proposal=proposal,
                section_type=section_type,
                defaults={
                    'title': title,
                    'order': order,
                    'content': '',
                },
            )


class Migration(migrations.Migration):

    dependencies = [
        ('proposals', '0003_ensure_budget_timestamps'),
    ]

    operations = [
        migrations.RunPython(ensure_default_sections, migrations.RunPython.noop),
    ]
