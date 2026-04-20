"""
Script to load initial data using the ORM (avoids loaddata raw=True issues with auto_now fields).
Run inside the container:
    docker-compose exec api python fixtures/load_initial_data.py
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
sys.path.insert(0, '/app')
django.setup()

from datetime import datetime, timezone
from decimal import Decimal

from apps.users.models import User, Certification
from apps.opportunities.models import Opportunity, Requirement, Risk
from apps.proposals.models import (
    Proposal, ProposalSection, ProposalTeamMember,
    Budget, BudgetItem,
)


def main():
    # Users
    ana, _ = User.objects.update_or_create(
        id=1,
        defaults={
            'email': 'ana.silva@consultpro.com',
            'username': 'ana.silva',
            'first_name': 'Ana',
            'last_name': 'Silva',
            'role': 'consultant',
            'skills': ['Educação', 'Género', 'Monitoria', 'Avaliação'],
            'languages': ['PT', 'EN', 'FR'],
            'availability': 'available',
            'is_staff': True,
            'is_superuser': True,
            'is_active': True,
        }
    )
    ana.set_password('password123')
    ana.save()

    carlos, _ = User.objects.update_or_create(
        id=2,
        defaults={
            'email': 'carlos.mendes@consultpro.com',
            'username': 'carlos.mendes',
            'first_name': 'Carlos',
            'last_name': 'Mendes',
            'role': 'manager',
            'skills': ['Gestão de Projetos', 'Orçamentos', 'Negociação'],
            'languages': ['PT', 'EN', 'ES'],
            'availability': 'busy',
            'is_staff': True,
            'is_superuser': False,
            'is_active': True,
        }
    )
    carlos.set_password('password123')
    carlos.save()

    maria, _ = User.objects.update_or_create(
        id=3,
        defaults={
            'email': 'maria.santos@consultpro.com',
            'username': 'maria.santos',
            'first_name': 'Maria',
            'last_name': 'Santos',
            'role': 'consultant',
            'skills': ['Saúde Pública', 'Sistemas de Saúde', 'Formação'],
            'languages': ['PT', 'EN'],
            'availability': 'available',
            'is_staff': True,
            'is_superuser': False,
            'is_active': True,
        }
    )
    maria.set_password('password123')
    maria.save()

    print(f"Created/updated 3 users")

    # Opportunities
    opp1, _ = Opportunity.objects.update_or_create(
        id=1,
        defaults={
            'title': 'Formação de Professores Rurais - Moçambique',
            'client': 'UNICEF',
            'sector': 'Educação',
            'country': 'Moçambique',
            'value': Decimal('450000.00'),
            'currency': 'USD',
            'deadline': datetime(2024, 5, 15, tzinfo=timezone.utc),
            'status': 'analyzing',
            'description': 'Consultoria para desenvolvimento de programa de formação de professores em áreas rurais, com ênfase em género e inclusão.',
            'evaluation_criteria': 'qcbs',
            'technical_weight': 70,
            'financial_weight': 30,
            'reference_number': 'UNICEF/MOZ/2024/001',
        }
    )

    opp2, _ = Opportunity.objects.update_or_create(
        id=2,
        defaults={
            'title': 'Fortalecimento dos Sistemas de Saúde - Angola',
            'client': 'Banco Mundial',
            'sector': 'Saúde',
            'country': 'Angola',
            'value': Decimal('890000.00'),
            'currency': 'USD',
            'deadline': datetime(2024, 6, 20, tzinfo=timezone.utc),
            'status': 'go',
            'description': 'Apoio técnico ao Ministério da Saúde de Angola para fortalecimento dos sistemas de saúde ao nível provincial.',
            'evaluation_criteria': 'qcbs',
            'technical_weight': 70,
            'financial_weight': 30,
            'reference_number': 'WB/ANG/2024/002',
        }
    )

    opp3, _ = Opportunity.objects.update_or_create(
        id=3,
        defaults={
            'title': 'Avaliação de Impacto - Programa de Agricultura',
            'client': 'FAO',
            'sector': 'Agricultura',
            'country': 'Cabo Verde',
            'value': Decimal('180000.00'),
            'currency': 'USD',
            'deadline': datetime(2024, 4, 25, tzinfo=timezone.utc),
            'status': 'proposal_draft',
            'description': 'Avaliação de impacto do programa de desenvolvimento agrícola sustentável em Cabo Verde.',
            'evaluation_criteria': 'qcbs',
            'technical_weight': 70,
            'financial_weight': 30,
            'reference_number': 'FAO/CV/2024/003',
        }
    )

    opp4, _ = Opportunity.objects.update_or_create(
        id=4,
        defaults={
            'title': 'Desenvolvimento de Infraestruturas Rurais - Senegal',
            'client': 'AfDB',
            'sector': 'Infraestruturas',
            'country': 'Senegal',
            'value': Decimal('1200000.00'),
            'currency': 'USD',
            'deadline': datetime(2024, 7, 10, tzinfo=timezone.utc),
            'status': 'new',
            'description': 'Consultoria para planeamento e supervisão de infraestruturas rurais no vale do Senegal.',
            'evaluation_criteria': 'qcbs',
            'technical_weight': 70,
            'financial_weight': 30,
            'reference_number': 'AfDB/SEN/2024/004',
        }
    )

    print(f"Created/updated 4 opportunities")

    # Requirements
    Requirement.objects.update_or_create(id=1, defaults={'opportunity': opp1, 'category': 'functional', 'description': 'Experiência mínima de 10 anos em projetos de educação', 'priority': 'mandatory', 'is_covered': True})
    Requirement.objects.update_or_create(id=2, defaults={'opportunity': opp1, 'category': 'technical', 'description': 'Especialista em género e inclusão social', 'priority': 'mandatory', 'is_covered': False})
    Requirement.objects.update_or_create(id=3, defaults={'opportunity': opp1, 'category': 'institutional', 'description': 'Registro ativo como consultora', 'priority': 'mandatory', 'is_covered': True})
    Requirement.objects.update_or_create(id=4, defaults={'opportunity': opp2, 'category': 'functional', 'description': 'Experiência em sistemas de saúde em África', 'priority': 'mandatory', 'is_covered': True})
    Requirement.objects.update_or_create(id=5, defaults={'opportunity': opp2, 'category': 'technical', 'description': 'Conhecimento de PHC e UHC', 'priority': 'preferred', 'is_covered': True})
    Requirement.objects.update_or_create(id=6, defaults={'opportunity': opp3, 'category': 'functional', 'description': 'Metodologias de avaliação de impacto', 'priority': 'mandatory', 'is_covered': True})
    Requirement.objects.update_or_create(id=7, defaults={'opportunity': opp3, 'category': 'technical', 'description': 'Econometria aplicada', 'priority': 'preferred', 'is_covered': True})
    Requirement.objects.update_or_create(id=8, defaults={'opportunity': opp4, 'category': 'functional', 'description': 'Engenheiro civil com experiência em projetos rurais', 'priority': 'mandatory', 'is_covered': False})

    # Risks
    Risk.objects.update_or_create(id=1, defaults={'opportunity': opp1, 'description': 'Prazo curto para mobilização de equipa', 'severity': 'high', 'mitigation': 'Identificar consultores com disponibilidade imediata'})
    Risk.objects.update_or_create(id=2, defaults={'opportunity': opp2, 'description': 'Concorrência forte de empresas internacionais', 'severity': 'medium'})
    Risk.objects.update_or_create(id=3, defaults={'opportunity': opp4, 'description': 'Requisito de certificação PPM não disponível', 'severity': 'high'})

    print(f"Created/updated requirements and risks")

    # Proposal
    prop1, _ = Proposal.objects.update_or_create(
        id=1,
        defaults={
            'opportunity': opp3,
            'title': 'Proposta - Avaliação de Impacto FAO Cabo Verde',
            'version': 2,
            'status': 'draft',
        }
    )

    # Sections
    sections_data = [
        (1, 'cover', 'Capa', '', 1, True),
        (2, 'executive_summary', 'Resumo Executivo', 'Esta proposta apresenta uma abordagem abrangente para a avaliação de impacto...', 2, True),
        (3, 'methodology', 'Metodologia', 'A metodologia proposta baseia-se em uma combinação de métodos quantitativos e qualitativos...', 3, False),
        (4, 'team', 'Equipa Técnica', '', 4, False),
        (5, 'workplan', 'Plano de Trabalho', '', 5, False),
        (6, 'budget', 'Orçamento', '', 6, False),
    ]
    for sid, stype, title, content, order, complete in sections_data:
        ProposalSection.objects.update_or_create(
            id=sid,
            defaults={'proposal': prop1, 'section_type': stype, 'title': title, 'content': content, 'order': order, 'is_complete': complete}
        )

    # Team members
    ProposalTeamMember.objects.update_or_create(id=1, defaults={'proposal': prop1, 'user': ana, 'role': 'Team Leader', 'hours': 240, 'hourly_rate': Decimal('0.00'), 'cv_attached': True})
    ProposalTeamMember.objects.update_or_create(id=2, defaults={'proposal': prop1, 'user': maria, 'role': 'Especialista em Saúde', 'hours': 120, 'hourly_rate': Decimal('0.00'), 'cv_attached': False})

    # Budget
    budget, _ = Budget.objects.update_or_create(
        id=1,
        defaults={'proposal': prop1, 'total': Decimal('175000.00'), 'currency': 'USD'}
    )
    BudgetItem.objects.update_or_create(id=1, defaults={'budget': budget, 'category': 'personnel', 'amount': Decimal('120000.00'), 'description': 'Honorários da equipa'})
    BudgetItem.objects.update_or_create(id=2, defaults={'budget': budget, 'category': 'travel', 'amount': Decimal('25000.00'), 'description': 'Deslocações e estadias'})
    BudgetItem.objects.update_or_create(id=3, defaults={'budget': budget, 'category': 'other', 'amount': Decimal('30000.00'), 'description': 'Materiais e equipamentos'})

    print(f"Created/updated proposal with sections, team and budget")
    print("Done! Initial data loaded successfully.")


if __name__ == '__main__':
    main()
