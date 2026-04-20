#!/usr/bin/env python
"""Add PMI phases, milestones, risks, deliverables and team to existing projects."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from datetime import date, timedelta
import random

from apps.users.models import User
from apps.projects.models import (
    Project, ProjectPhase, ProjectMilestone,
    ProjectRisk, ProjectDeliverable, ProjectTeamMember
)


def create_pmi_phases(project):
    phases = [
        ('initiating', 0, 'Iniciacao'),
        ('planning', 1, 'Planeamento'),
        ('executing', 2, 'Execucao'),
        ('monitoring', 3, 'Monitorizacao e Controlo'),
        ('closing', 4, 'Encerramento'),
    ]
    for name, order, label in phases:
        ProjectPhase.objects.get_or_create(
            project=project,
            name=name,
            defaults={
                'order': order,
                'description': f'Fase de {label} do projeto {project.title}.',
                'start_date': project.start_date,
                'end_date': project.end_date,
                'completion_percentage': random.randint(0, 100) if project.status in ['active', 'completed', 'closed'] else 0,
                'is_completed': project.status in ['completed', 'closed'] or (order < 2 and project.status == 'active'),
            }
        )


def create_project_milestones(project):
    milestones = [
        'Kickoff Meeting',
        'Relatorio Inicial',
        'Revisao de Metade',
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
    risks = [
        ('Atraso na contratacao de especialistas', 'high'),
        ('Mudanca de requisitos pelo cliente', 'medium'),
        ('Instabilidade politica no pais', 'critical'),
        ('Problemas de logistica no terreno', 'medium'),
        ('Orcamento insuficiente para fase 2', 'high'),
    ]
    for title, severity in risks:
        ProjectRisk.objects.get_or_create(
            project=project,
            title=title,
            defaults={
                'description': f'Risco identificado: {title}',
                'severity': severity,
                'status': random.choice(['open', 'mitigated', 'closed']),
                'mitigation_plan': f'Plano de mitigacao para {title}',
            }
        )


def create_project_deliverables(project):
    deliverables = [
        'Plano de Trabalho',
        'Relatorio de Diagnostico',
        'Analise de Stakeholders',
        'Documento de Metodologia',
        'Relatorio Final',
    ]
    for i, title in enumerate(deliverables):
        due = project.end_date - timedelta(days=(len(deliverables) - i) * 15) if project.end_date else date.today() + timedelta(days=i * 20)
        ProjectDeliverable.objects.get_or_create(
            project=project,
            title=title,
            defaults={
                'description': f'Entregavel: {title}',
                'due_date': due,
                'status': random.choice(['draft', 'under_review', 'approved', 'submitted', 'accepted']),
            }
        )


def create_project_team(project, users):
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
    users = list(User.objects.all())
    projects = Project.objects.all()

    print(f"=== Adicionando detalhes a {projects.count()} projetos ===")
    for project in projects:
        create_pmi_phases(project)
        create_project_milestones(project)
        create_project_risks(project)
        create_project_deliverables(project)
        create_project_team(project, users)
        print(f"  Projeto '{project.title}' atualizado")

    print("\n=== Done! ===")
    print(f"Total Fases PMI: {ProjectPhase.objects.count()}")
    print(f"Total Marcos: {ProjectMilestone.objects.count()}")
    print(f"Total Riscos: {ProjectRisk.objects.count()}")
    print(f"Total Entregaveis: {ProjectDeliverable.objects.count()}")
    print(f"Total Membros de Equipa: {ProjectTeamMember.objects.count()}")


if __name__ == '__main__':
    main()
