from django.db import migrations

CV_TEMPLATES = [
    {
        'name': 'World Bank Standard CV',
        'organization': 'world_bank',
        'organization_name': 'World Bank',
        'description': (
            'Formato padrao do Banco Mundial para consultores em projetos financiados. '
            'Inclui secoes obrigatorias de experiencia relevante, educacao e declaracao de disponibilidade.'
        ),
        'required_sections': [
            {'id': 'personal', 'name': 'Dados Pessoais', 'required': True},
            {'id': 'education', 'name': 'Educacao', 'required': True},
            {'id': 'experience', 'name': 'Experiencia Profissional', 'required': True},
            {'id': 'languages', 'name': 'Idiomas', 'required': True},
            {'id': 'certifications', 'name': 'Certificacoes e Formacoes', 'required': False},
            {'id': 'references', 'name': 'Referencias', 'required': False},
        ],
        'format_rules': [
            {'rule': 'Maximo 4 paginas'},
            {'rule': 'Fonte Arial ou Times New Roman, tamanho 11'},
            {'rule': 'Experiencia em ordem cronologica inversa'},
            {'rule': 'Incluir percentagem de tempo dedicado a cada projeto'},
        ],
        'max_length_pages': 4,
    },
    {
        'name': 'UNDP P11 Form',
        'organization': 'un',
        'organization_name': 'UNDP',
        'description': (
            'Formulario P11 do PNUD (United Nations Development Programme). '
            'Formato estruturado obrigatorio para todas as candidaturas ao PNUD e agencias do sistema ONU.'
        ),
        'required_sections': [
            {'id': 'personal', 'name': 'Informacoes Pessoais', 'required': True},
            {'id': 'education', 'name': 'Educacao e Qualificacoes', 'required': True},
            {'id': 'experience', 'name': 'Historico Profissional', 'required': True},
            {'id': 'languages', 'name': 'Proficiencia em Linguas', 'required': True},
            {'id': 'publications', 'name': 'Publicacoes e Relatorios', 'required': False},
            {'id': 'references', 'name': 'Referencias (3 minimo)', 'required': True},
        ],
        'format_rules': [
            {'rule': 'Usar exclusivamente o formulario P11 oficial'},
            {'rule': 'Nao substituir por CV livre'},
            {'rule': 'Assinar e datar o documento'},
            {'rule': 'Indicar nivel de idioma por escala UN: Basico/Bom/Muito Bom/Fluente'},
        ],
        'max_length_pages': 6,
    },
    {
        'name': 'UN System Standard CV',
        'organization': 'un',
        'organization_name': 'United Nations',
        'description': (
            'CV padrao para o sistema das Nacoes Unidas (excluindo PNUD que usa P11). '
            'Aplicavel a UNICEF, UNFPA, WFP, FAO, WHO e outras agencias especializadas.'
        ),
        'required_sections': [
            {'id': 'personal', 'name': 'Dados Pessoais', 'required': True},
            {'id': 'summary', 'name': 'Sumario Profissional', 'required': True},
            {'id': 'education', 'name': 'Educacao', 'required': True},
            {'id': 'experience', 'name': 'Experiencia Profissional', 'required': True},
            {'id': 'skills', 'name': 'Competencias Tecnicas', 'required': True},
            {'id': 'languages', 'name': 'Idiomas', 'required': True},
        ],
        'format_rules': [
            {'rule': 'Maximo 3 paginas'},
            {'rule': 'Descricao de impacto mensuravel em cada experiencia'},
            {'rule': 'Alinhar competencias com os valores da ONU'},
            {'rule': 'Indicar missoes internacionais e contextos frageis'},
        ],
        'max_length_pages': 3,
    },
    {
        'name': 'EU/EC Expert CV',
        'organization': 'eu',
        'organization_name': 'European Union',
        'description': (
            'Formato Europass adaptado para peritos em projetos financiados pela Comissao Europeia '
            '(EuropeAid/INTPA). Obrigatorio para contratos de consultoria EU.'
        ),
        'required_sections': [
            {'id': 'personal', 'name': 'Informacoes Pessoais', 'required': True},
            {'id': 'expertise', 'name': 'Areas de Especializacao', 'required': True},
            {'id': 'education', 'name': 'Educacao', 'required': True},
            {'id': 'experience', 'name': 'Experiencia Profissional', 'required': True},
            {'id': 'languages', 'name': 'Competencias Linguisticas', 'required': True},
            {'id': 'membership', 'name': 'Memberships Profissionais', 'required': False},
        ],
        'format_rules': [
            {'rule': 'Seguir modelo Europass'},
            {'rule': 'Maximo 5 paginas'},
            {'rule': 'Indicar valor contratual e percentagem de tempo em cada missao'},
            {'rule': 'Separar experiencia nacional de internacional'},
            {'rule': 'Declaracao de exclusividade assinada'},
        ],
        'max_length_pages': 5,
    },
    {
        'name': 'AfDB CV Format',
        'organization': 'afdb',
        'organization_name': 'African Development Bank',
        'description': (
            'Formato do Banco Africano de Desenvolvimento para consultores em projetos regionais e nacionais '
            'em Africa. Enfase em experiencia no continente africano.'
        ),
        'required_sections': [
            {'id': 'personal', 'name': 'Dados Pessoais', 'required': True},
            {'id': 'summary', 'name': 'Perfil Profissional', 'required': True},
            {'id': 'education', 'name': 'Formacao Academica', 'required': True},
            {'id': 'experience', 'name': 'Experiencia Profissional', 'required': True},
            {'id': 'africa_experience', 'name': 'Experiencia em Africa', 'required': True},
            {'id': 'languages', 'name': 'Idiomas', 'required': True},
            {'id': 'certifications', 'name': 'Certificacoes', 'required': False},
        ],
        'format_rules': [
            {'rule': 'Maximo 4 paginas'},
            {'rule': 'Destacar experiencia em paises africanos'},
            {'rule': 'Indicar familiaridade com politicas e procedimentos do BAD'},
            {'rule': 'Incluir experiencia em contextos pos-conflito ou frageis se aplicavel'},
        ],
        'max_length_pages': 4,
    },
    {
        'name': 'USAID Bio Data Form 1420',
        'organization': 'usaid',
        'organization_name': 'USAID',
        'description': (
            'Formulario Bio Data 1420 obrigatorio para todas as posicoes de consultores financiados '
            'pela USAID. Inclui declaracoes de conformidade e restricoes.'
        ),
        'required_sections': [
            {'id': 'personal', 'name': 'Dados Pessoais e Contacto', 'required': True},
            {'id': 'education', 'name': 'Educacao (do mais recente)', 'required': True},
            {'id': 'experience', 'name': 'Experiencia de Trabalho', 'required': True},
            {'id': 'languages', 'name': 'Idiomas', 'required': True},
            {'id': 'references', 'name': 'Referencias (3 profissionais)', 'required': True},
            {'id': 'certifications', 'name': 'Formacoes e Certificacoes', 'required': False},
        ],
        'format_rules': [
            {'rule': 'Usar formulario 1420 oficial da USAID'},
            {'rule': 'Maximo 4 paginas'},
            {'rule': 'Assinar declaracao de conformidade FAR'},
            {'rule': 'Indicar cidadania e estatuto de residente'},
            {'rule': 'Nao usar abreviaturas nao explicadas'},
        ],
        'max_length_pages': 4,
    },
    {
        'name': 'GIZ Consultant Profile',
        'organization': 'giz',
        'organization_name': 'GIZ',
        'description': (
            'Perfil de consultor para projetos da GIZ (Deutsche Gesellschaft fuer Internationale '
            'Zusammenarbeit). Formato estruturado para cooperacao tecnica alema.'
        ),
        'required_sections': [
            {'id': 'personal', 'name': 'Dados Pessoais', 'required': True},
            {'id': 'expertise', 'name': 'Areas de Competencia', 'required': True},
            {'id': 'education', 'name': 'Formacao', 'required': True},
            {'id': 'experience', 'name': 'Experiencia Profissional', 'required': True},
            {'id': 'giz_projects', 'name': 'Experiencia em Projetos GIZ/BMZ', 'required': False},
            {'id': 'languages', 'name': 'Idiomas (incluindo Alemao)', 'required': True},
            {'id': 'publications', 'name': 'Publicacoes Relevantes', 'required': False},
        ],
        'format_rules': [
            {'rule': 'Maximo 4 paginas'},
            {'rule': 'Indicar nivel de alemao se aplicavel'},
            {'rule': 'Destacar experiencia em cooperacao tecnica'},
            {'rule': 'Incluir resultados mensuraveis por projeto'},
            {'rule': 'Listar financiadores de projetos anteriores'},
        ],
        'max_length_pages': 4,
    },
]


def seed_cv_templates(apps, schema_editor):
    CVTemplate = apps.get_model('curriculum', 'CVTemplate')
    for tpl in CV_TEMPLATES:
        CVTemplate.objects.get_or_create(
            name=tpl['name'],
            defaults={**tpl, 'is_active': True},
        )


def unseed_cv_templates(apps, schema_editor):
    CVTemplate = apps.get_model('curriculum', 'CVTemplate')
    CVTemplate.objects.filter(name__in=[t['name'] for t in CV_TEMPLATES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('curriculum', '0003_templatematch_generated_file'),
    ]

    operations = [
        migrations.RunPython(seed_cv_templates, reverse_code=unseed_cv_templates),
    ]
