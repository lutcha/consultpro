"""
Seed demo opportunities from configured scraping sources.

Usage:
    python manage.py seed_demo_opportunities
"""
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.opportunities.models import Opportunity, Requirement, Risk
from apps.scraping.models import ScrapedOpportunity, ScrapingSource
from apps.users.models import User


DEMO_OPPORTUNITIES = [
    {
        'source': 'UGPE - Concursos Cabo Verde',
        'external_id': 'DEMO-UGPE-DIGITAL-CV-2026',
        'external_url': 'https://ugpe.gov.cv/concursos',
        'title': 'Consultoria para Avaliacao do Programa Digital Cabo Verde',
        'client': 'UGPE / Ministerio da Modernizacao do Estado',
        'sector': 'Tecnologia',
        'country': 'Cabo Verde',
        'value': Decimal('180000.00'),
        'currency': 'EUR',
        'deadline_days': 28,
        'description': (
            'Apoio tecnico para avaliar resultados, riscos e sustentabilidade '
            'do programa Digital Cabo Verde, incluindo entrevistas, analise de '
            'indicadores, roteiro de melhoria e plano de transferencia de capacidades.'
        ),
        'requirements': [
            'Experiencia comprovada em avaliacao de programas GovTech ou transformacao digital.',
            'Conhecimento do contexto institucional de Cabo Verde e sistemas publicos digitais.',
            'Metodologia participativa com entrevistas, grupos focais e matriz de indicadores.',
        ],
        'risks': [
            'Disponibilidade limitada de dados administrativos consolidados.',
            'Prazo curto para validacao com multiplas entidades publicas.',
        ],
    },
    {
        'source': 'AFD - Procurement',
        'external_id': 'DEMO-AFD-BLUE-ECONOMY-2026',
        'external_url': 'https://www.afd.fr/en/procurement',
        'title': 'Assistencia Tecnica para Economia Azul e Pesca Artesanal',
        'client': 'Agence Francaise de Developpement',
        'sector': 'Economia Azul',
        'country': 'Cabo Verde',
        'value': Decimal('240000.00'),
        'currency': 'EUR',
        'deadline_days': 35,
        'description': (
            'Servicos de consultoria para diagnostico da cadeia de valor da pesca '
            'artesanal, desenho de instrumentos de apoio a cooperativas e plano '
            'de monitorizacao ambiental nas ilhas costeiras.'
        ),
        'requirements': [
            'Especialista senior em economia azul ou pescas artesanais.',
            'Experiencia em desenho de programas financiados por doadores internacionais.',
            'Capacidade de produzir plano operacional e quadro logico bilingue PT/FR ou PT/EN.',
        ],
        'risks': [
            'Risco medio de baixa participacao das comunidades piscatorias.',
            'Dependencia de dados ambientais dispersos entre entidades nacionais.',
        ],
    },
    {
        'source': 'ECREEE - Procurement Notices',
        'external_id': 'DEMO-ECREEE-ENERGY-NEXUS-2026',
        'external_url': 'https://www.ecreee.org/category/procurement-notices/',
        'title': 'Consultor Regional para Nexus Agua-Energia-Alimentacao',
        'client': 'ECREEE / CEDEAO',
        'sector': 'Energia',
        'country': 'Africa Ocidental',
        'value': Decimal('125000.00'),
        'currency': 'USD',
        'deadline_days': 21,
        'description': (
            'Contratacao de consultor regional para preparar estudos de viabilidade, '
            'mapear oportunidades de energias renovaveis e recomendar modelos de '
            'financiamento para intervencoes WEF Nexus em paises da CEDEAO.'
        ),
        'requirements': [
            'Experiencia tecnica em energias renovaveis e gestao de recursos hidricos.',
            'Conhecimento de mecanismos de financiamento climatico e regional.',
            'Disponibilidade para missoes curtas em Cabo Verde e Africa Ocidental.',
        ],
        'risks': [
            'Coordenacao regional complexa entre paises e agencias executoras.',
            'Risco tecnico na harmonizacao de dados setoriais.',
        ],
    },
    {
        'source': 'UNGM - United Nations Global Marketplace',
        'external_id': 'DEMO-UNGM-HEALTH-ONEHEALTH-2026',
        'external_url': 'https://www.ungm.org/Public/Notice',
        'title': 'Avaliacao Final de Projeto One Health em Cabo Verde',
        'client': 'Sistema das Nacoes Unidas',
        'sector': 'Saude',
        'country': 'Cabo Verde',
        'value': Decimal('95000.00'),
        'currency': 'USD',
        'deadline_days': 18,
        'description': (
            'Avaliacao final independente de projeto One Health, cobrindo saude '
            'publica, vigilancia epidemiologica, coordenacao intersetorial e '
            'recomendacoes para continuidade programatica.'
        ),
        'requirements': [
            'Experiencia em avaliacao de projetos de saude publica ou One Health.',
            'Dominio de metodos mistos e recolha de dados qualitativos.',
            'Relatorio final com recomendacoes acionaveis para agencias e governo.',
        ],
        'risks': [
            'Prazo apertado para entrevistas com stakeholders nacionais.',
            'Possivel insuficiencia de dados de linha de base.',
        ],
    },
    {
        'source': 'World Bank - Projects Cabo Verde',
        'external_id': 'DEMO-WB-TOURISM-RESILIENCE-2026',
        'external_url': 'https://projects.worldbank.org',
        'title': 'Especialista em Turismo Resiliente e Desenvolvimento Local',
        'client': 'World Bank Group',
        'sector': 'Turismo',
        'country': 'Cabo Verde',
        'value': Decimal('210000.00'),
        'currency': 'USD',
        'deadline_days': 42,
        'description': (
            'Consultoria para apoiar desenho de componentes de turismo resiliente, '
            'incluindo analise de cadeias de valor locais, gestao de riscos climaticos '
            'e mecanismos de inclusao de pequenas empresas.'
        ),
        'requirements': [
            'Experiencia em turismo sustentavel, desenvolvimento local ou resiliencia climatica.',
            'Conhecimento de projetos financiados pelo Banco Mundial.',
            'Plano de trabalho com entregaveis claros, cronograma e matriz de riscos.',
        ],
        'risks': [
            'Risco alto de desalinhamento entre prioridades locais e criterios do financiador.',
            'Sazonalidade pode limitar a recolha de dados no terreno.',
        ],
    },
]


class Command(BaseCommand):
    help = 'Create demo scraped and internal opportunities for proposal testing'

    def handle(self, *args, **options):
        user = (
            User.objects.filter(role__in=['manager', 'admin']).first()
            or User.objects.filter(is_staff=True).first()
            or User.objects.first()
        )
        if not user:
            self.stderr.write(self.style.ERROR('No users found. Create a user before seeding demo opportunities.'))
            return

        created = 0
        updated = 0
        imported = 0

        for item in DEMO_OPPORTUNITIES:
            source, _ = ScrapingSource.objects.get_or_create(
                name=item['source'],
                defaults={
                    'organization': item['client'][:200],
                    'url': item['external_url'],
                    'source_type': 'portal',
                    'status': 'active',
                    'scrape_frequency': 'weekly',
                    'scraper_class': 'GenericPortalScraper',
                    'filters': {'countries': ['CPV'], 'keywords': ['consultant', 'consultoria']},
                },
            )
            deadline = timezone.now() + timezone.timedelta(days=item['deadline_days'])
            scraped, was_created = ScrapedOpportunity.objects.update_or_create(
                source=source,
                external_id=item['external_id'],
                defaults={
                    'external_url': item['external_url'],
                    'title': item['title'],
                    'organization': source.organization,
                    'client': item['client'],
                    'sector': item['sector'],
                    'country': item['country'],
                    'description': item['description'],
                    'value': item['value'],
                    'currency': item['currency'],
                    'deadline': deadline,
                    'status': 'new',
                    'deadline_alert': item['deadline_days'] <= 21,
                    'cv_eligible': True,
                    'eligibility_data': {'confidence': 0.9, 'reason': 'Demo opportunity focused on Cabo Verde/Africa'},
                    'ai_summary': item['description'],
                    'ai_extracted_requirements': item['requirements'],
                    'transformation_flags': {
                        'demo_seeded': True,
                        'ai_enriched': True,
                        'ai_requirements_count': len(item['requirements']),
                        'ai_risks_count': len(item['risks']),
                    },
                    'data_quality_score': Decimal('0.90'),
                    'ingestion_batch_id': 'demo-opportunities',
                },
            )
            created += int(was_created)
            updated += int(not was_created)

            opportunity, opp_created = Opportunity.objects.update_or_create(
                reference_number=item['external_id'],
                defaults={
                    'title': item['title'],
                    'client': item['client'],
                    'sector': item['sector'],
                    'country': item['country'],
                    'value': item['value'],
                    'currency': item['currency'],
                    'deadline': deadline,
                    'status': 'new',
                    'description': item['description'],
                    'evaluation_criteria': 'qcbs',
                    'technical_weight': 70,
                    'financial_weight': 30,
                    'url_source': item['external_url'],
                    'ai_summary': item['description'],
                    'ai_analysis_status': 'completed',
                    'created_by': user,
                },
            )
            opportunity.assigned_to.add(user)
            scraped.status = 'imported'
            scraped.imported_opportunity = opportunity
            scraped.imported_by = user
            scraped.imported_at = timezone.now()
            scraped.save(update_fields=['status', 'imported_opportunity', 'imported_by', 'imported_at'])
            imported += int(opp_created)

            opportunity.requirements.filter(extracted_by_ai=True).delete()
            for req in item['requirements']:
                Requirement.objects.create(
                    opportunity=opportunity,
                    category='technical' if 'tecn' in req.lower() or 'technical' in req.lower() else 'functional',
                    description=req,
                    priority='mandatory',
                    extracted_by_ai=True,
                )
            opportunity.risks.filter(identified_by_ai=True).delete()
            for risk in item['risks']:
                severity = 'high' if 'alto' in risk.lower() or 'high' in risk.lower() else 'medium'
                Risk.objects.create(
                    opportunity=opportunity,
                    description=risk,
                    severity=severity,
                    identified_by_ai=True,
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Demo opportunities ready: {created} scraped created, {updated} scraped updated, '
                f'{imported} internal opportunities created.'
            )
        )
