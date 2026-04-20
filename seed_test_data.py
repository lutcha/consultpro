#!/usr/bin/env python
"""Seed test data: 10 proposals and 10 projects with PMI phases."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from datetime import date, timedelta
import random

from django.db import connection
from apps.opportunities.models import Opportunity
from apps.users.models import User
from apps.proposals.models import Proposal
from apps.projects.models import Project, ProjectPhase, ProjectMilestone, ProjectRisk, ProjectDeliverable, ProjectTeamMember


def reset_sequence(table_name):
    """Reset PostgreSQL sequence to max id + 1."""
    with connection.cursor() as cursor:
        cursor.execute(f"""
            SELECT setval('{table_name}_id_seq', COALESCE((SELECT MAX(id) FROM {table_name}), 0) + 1, false);
        """)


def create_pmi_phases(project):
    """Create PMI phases for a project."""
    phases = [
        ('initiating', 0),
        ('planning', 1),
        ('executing', 2),
        ('monitoring', 3),
        ('closing', 4),
    ]
    for name, order in phases:
        ProjectPhase.objects.get_or_create(
            project=project,
            name=name,
            defaults={
                'order': order,
                'description': f'Fase de {name} do projeto.',
                'start_date': project.start_date,
                'end_date': project.end_date,
                'completion_percentage': random.randint(0, 100) if project.status in ['active', 'completed', 'closed'] else 0,
                'is_completed': project.status in ['completed', 'closed'] or (order < 2 and project.status == 'active'),
            }
        )


def create_project_milestones(project):
    """Create milestones for a project."""
    milestones = [
        'Kickoff Meeting',
        'Relatório Inicial',
        'Revisão de Metade',
        'Entrega Final',
        'Workshop de Encerramento',
    ]
    for i, title in enumerate(milestones):
        due = project.end_date - timedelta(days=(len(milestones) - i) * 20) if project.end_date else date.today() + timedelta(days=i * 30)
        ProjectMilestone.objects.get_or_create(
            project=project,
            title=title,
            defaults={
                'description': f'Marco: {title}',
                'due_date': due,
                'status': random.choice(['not_started', 'in_progress', 'completed', 'delayed']),
            }
        )


def create_project_risks(project):
    """Create risks for a project."""
    risks = [
        ('Atraso na contratação de especialistas', 'high'),
        ('Mudança de requisitos pelo cliente', 'medium'),
        ('Instabilidade política no país', 'critical'),
        ('Problemas de logística no terreno', 'medium'),
        ('Orçamento insuficiente para fase 2', 'high'),
    ]
    for title, severity in risks:
        ProjectRisk.objects.get_or_create(
            project=project,
            title=title,
            defaults={
                'description': f'Risco identificado: {title}',
                'severity': severity,
                'status': random.choice(['open', 'mitigated', 'closed']),
                'mitigation_plan': f'Plano de mitigação para {title}',
            }
        )


def create_project_deliverables(project):
    """Create deliverables for a project."""
    deliverables = [
        'Plano de Trabalho',
        'Relatório de Diagnóstico',
        'Análise de Stakeholders',
        'Documento de Metodologia',
        'Relatório Final',
    ]
    for i, title in enumerate(deliverables):
        due = project.end_date - timedelta(days=(len(deliverables) - i) * 15) if project.end_date else date.today() + timedelta(days=i * 20)
        ProjectDeliverable.objects.get_or_create(
            project=project,
            title=title,
            defaults={
                'description': f'Entregável: {title}',
                'due_date': due,
                'status': random.choice(['draft', 'under_review', 'approved', 'submitted', 'accepted']),
            }
        )


def create_project_team(project, users):
    """Create team members for a project."""
    roles = ['team_lead', 'technical_lead', 'consultant', 'specialist', 'support']
    for i, user in enumerate(users):
        ProjectTeamMember.objects.get_or_create(
            project=project,
            user=user,
            defaults={
                'role': roles[i % len(roles)],
                'allocation_percentage': random.randint(20, 100),
                'start_date': project.start_date,
                'end_date': project.end_date,
            }
        )


def main():
    # Reset sequences first
    print("=== Resetting sequences ===")
    reset_sequence('opportunities_opportunity')
    reset_sequence('proposals_proposal')
    reset_sequence('projects_project')
    reset_sequence('projects_projectphase')
    reset_sequence('projects_projectmilestone')
    reset_sequence('projects_projectrisk')
    reset_sequence('projects_projectdeliverable')
    reset_sequence('projects_projectteammember')
    print("  Done")

    # Get users
    ana = User.objects.get(email='ana.silva@consultpro.com')
    carlos = User.objects.get(email='carlos.mendes@consultpro.com')
    maria = User.objects.get(email='maria.santos@consultpro.com')
    users = [ana, carlos, maria]

    sectors = ['Educacao', 'Saude', 'Agricultura', 'Governanca', 'Energia', 'Agua e Saneamento', 'Transportes', 'TIC']
    countries = ['Mocambique', 'Angola', 'Cabo Verde', 'Guine-Bissau', 'Sao Tome e Principe', 'Timor-Leste']
    clients = ['Banco Mundial', 'UNICEF', 'UNDP', 'GIZ', 'AFD', 'FIDA', 'UE', 'BAD']
    proposal_statuses = ['draft', 'in_review', 'qc_check', 'approved', 'submitted', 'won', 'lost']
    project_statuses = ['planning', 'active', 'on_hold', 'completed', 'closed']

    print("\n=== Criando Oportunidades ===")
    opportunities = []
    for i in range(1, 11):
        opp, created = Opportunity.objects.get_or_create(
            title=f'Oportunidade de Teste {i}',
            defaults={
                'client': random.choice(clients),
                'sector': random.choice(sectors),
                'country': random.choice(countries),
                'value': str(random.randint(50000, 500000)),
                'currency': random.choice(['EUR', 'USD']),
                'deadline': date.today() + timedelta(days=random.randint(10, 90)),
                'status': random.choice(['analyzing', 'go', 'proposal_draft', 'submitted', 'won']),
                'description': f'Descricao da oportunidade de teste numero {i}. Projeto de consultoria em desenvolvimento.',
                'created_by': ana,
            }
        )
        opportunities.append(opp)
        status_text = 'criada' if created else 'ja existe'
        print(f'  Oportunidade {i}: {status_text} (status={opp.status})')

    print("\n=== Criando Propostas ===")
    proposals = []
    for i, opp in enumerate(opportunities[:10], 1):
        prop, created = Proposal.objects.get_or_create(
            opportunity=opp,
            defaults={
                'title': f'Proposta {i}: {opp.title}',
                'version': 1,
                'status': random.choice(proposal_statuses),
                'created_by': random.choice([ana, carlos]),
            }
        )
        proposals.append(prop)
        status_text = 'criada' if created else 'ja existe'
        print(f'  Proposta {i}: {status_text} (status={prop.status})')

    print("\n=== Criando Projetos com Dados Completos ===")
    for i in range(1, 11):
        proposal = None
        if i <= len(proposals) and proposals[i-1].status == 'won':
            proposal = proposals[i-1]

        proj, created = Project.objects.get_or_create(
            title=f'Projeto de Teste {i}',
            defaults={
                'description': f'Descricao do projeto de teste numero {i}. Implementacao de consultoria em desenvolvimento.',
                'proposal': proposal,
                'client': random.choice(clients),
                'status': random.choice(project_statuses),
                'start_date': date.today() - timedelta(days=random.randint(0, 60)),
                'end_date': date.today() + timedelta(days=random.randint(30, 180)),
                'budget_total': random.randint(100000, 1000000),
                'budget_currency': random.choice(['EUR', 'USD']),
                'actual_cost': random.randint(50000, 800000),
                'progress': random.randint(0, 100),
                'manager': random.choice([ana, carlos]),
                'sector': random.choice(sectors),
                'country': random.choice(countries),
                'risk_level': random.choice(['low', 'medium', 'high', 'critical']),
            }
        )

        if created:
            create_pmi_phases(proj)
            create_project_milestones(proj)
            create_project_risks(proj)
            create_project_deliverables(proj)
            create_project_team(proj, users)
            print(f'  Projeto {i}: criado com fases PMI, marcos, riscos, entregaveis e equipa (status={proj.status})')
        else:
            print(f'  Projeto {i}: ja existe (status={proj.status})')

    print("\n=== Done! ===")
    print(f"Total Oportunidades: {Opportunity.objects.count()}")
    print(f"Total Propostas: {Proposal.objects.count()}")
    print(f"Total Projetos: {Project.objects.count()}")
    print(f"Total Fases PMI: {ProjectPhase.objects.count()}")
    print(f"Total Marcos: {ProjectMilestone.objects.count()}")
    print(f"Total Riscos: {ProjectRisk.objects.count()}")
    print(f"Total Entregáveis: {ProjectDeliverable.objects.count()}")


if __name__ == '__main__':
    main()
