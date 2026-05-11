"""
Migration B1+B2: Taxonomia de Sectores, Regiões e Países.

- B1: SECTOR_CHOICES (30+ choices) no modelo Opportunity
- B2: REGION_CHOICES + COUNTRY_CHOICES + eligible_countries

Nota: Não altera os valores existentes na BD; apenas actualiza os
constraints de validação ao nível Django. Dados existentes com
sector="Health" continuam a funcionar; novos valores serão validados
contra as choices.
"""
from django.db import migrations, models
from decimal import Decimal


def _migrate_sectors(apps, schema_editor):
    """Migrate existing sector names to taxonomy codes (heuristic)."""
    Opportunity = apps.get_model('opportunities', 'Opportunity')
    SECTOR_MAP = {
        'Educação': 'education',
        'Education': 'education',
        'Saúde': 'health',
        'Health': 'health',
        'Protecção Social': 'social_protection',
        'Social Protection': 'social_protection',
        'Género': 'gender',
        'Gender': 'gender',
        'Agricultura': 'agriculture',
        'Agriculture': 'agriculture',
        'Desenvolvimento Rural': 'rural_development',
        'Rural Development': 'rural_development',
        'Ambiente': 'environment',
        'Environment': 'environment',
        'Infraestruturas': 'infrastructure',
        'Infrastructure': 'infrastructure',
        'Infraestrutura': 'infrastructure',
        'Energia': 'energy',
        'Energy': 'energy',
        'Água e Saneamento': 'water_sanitation',
        'Water and Sanitation': 'water_sanitation',
        'Turismo': 'tourism',
        'Tourism': 'tourism',
        'Governação': 'governance',
        'Governance': 'governance',
        'ICT': 'ict',
        'Tecnologias de Informação': 'ict',
        'IT': 'ict',
        'Transportes': 'transport',
        'Transport': 'transport',
        'Agricultura e Desenvolvimento Rural': 'agriculture',
        'Alterações Climáticas': 'climate_change',
        'Climate Change': 'climate_change',
        'Justiça': 'justice',
        'Justice': 'justice',
        'Pescas': 'fisheries',
        'Fisheries': 'fisheries',
        'Segurança Alimentar': 'food_security',
        'Food Security': 'food_security',
    }
    for opp in Opportunity.objects.all():
        old = opp.sector
        if old in SECTOR_MAP:
            opp.sector = SECTOR_MAP[old]
            opp.save(update_fields=['sector'])


def _migrate_countries(apps, schema_editor):
    """Migrate existing country names to ISO 2-letter codes."""
    Opportunity = apps.get_model('opportunities', 'Opportunity')
    COUNTRY_MAP = {
        'Cabo Verde': 'cv',
        'Angola': 'ao',
        'Moçambique': 'mz',
        'Mozambique': 'mz',
        'Guiné-Bissau': 'gw',
        'Guinea-Bissau': 'gw',
        'São Tomé e Príncipe': 'st',
        'Sao Tome and Principe': 'st',
        'Senegal': 'sn',
        'Guiné-Conacri': 'gn',
        'Guinea': 'gn',
        'Serra Leoa': 'sl',
        'Sierra Leone': 'sl',
        'Libéria': 'lr',
        'Liberia': 'lr',
        'Costa do Marfim': 'ci',
        "Côte d'Ivoire": 'ci',
        'Gana': 'gh',
        'Ghana': 'gh',
        'Togo': 'tg',
        'Benim': 'bj',
        'Benin': 'bj',
        'Nigéria': 'ng',
        'Nigeria': 'ng',
        'Burkina Faso': 'bf',
        'Mali': 'ml',
        'Níger': 'ne',
        'Niger': 'ne',
        'Gâmbia': 'gm',
        'Gambia': 'gm',
        'Mauritânia': 'mr',
        'Mauritania': 'mr',
        'Camarões': 'cm',
        'Cameroon': 'cm',
        'Chade': 'td',
        'Chad': 'td',
        'Etiópia': 'et',
        'Ethiopia': 'et',
        'Quénia': 'ke',
        'Kenya': 'ke',
        'Tanzânia': 'tz',
        'Tanzania': 'tz',
        'Uganda': 'ug',
        'África do Sul': 'za',
        'South Africa': 'za',
        'Internacional': 'int',
        'International': 'int',
    }
    for opp in Opportunity.objects.all():
        old = opp.country
        if old in COUNTRY_MAP:
            opp.country = COUNTRY_MAP[old]
            opp.save(update_fields=['country'])


def _migrate_regions(apps, schema_editor):
    """Migrate existing region names to taxonomy codes."""
    Opportunity = apps.get_model('opportunities', 'Opportunity')
    REGION_MAP = {
        'África Ocidental': 'west_africa',
        'West Africa': 'west_africa',
        'África Central': 'central_africa',
        'Central Africa': 'central_africa',
        'África Oriental': 'east_africa',
        'East Africa': 'east_africa',
        'África Austral': 'southern_africa',
        'Southern Africa': 'southern_africa',
        'Norte de África': 'north_africa',
        'North Africa': 'north_africa',
        'África Lusófona': 'lusophone_africa',
        'Lusophone Africa': 'lusophone_africa',
        'Internacional': 'international',
        'International': 'international',
        'Global': 'international',
    }
    for opp in Opportunity.objects.all():
        old = opp.region
        if old in REGION_MAP:
            opp.region = REGION_MAP[old]
            opp.save(update_fields=['region'])


class Migration(migrations.Migration):

    dependencies = [
        ('opportunities', '0004_opportunity_ai_extraction'),
    ]

    operations = [
        # B1: Sector choices + eligible_sectors
        migrations.AlterField(
            model_name='opportunity',
            name='sector',
            field=models.CharField(
                choices=[
                    ('education', 'Educação'),
                    ('health', 'Saúde'),
                    ('social_protection', 'Protecção Social'),
                    ('gender', 'Género e Igualdade'),
                    ('water_sanitation', 'Água e Saneamento'),
                    ('food_security', 'Segurança Alimentar'),
                    ('nutrition', 'Nutrição'),
                    ('housing', 'Habitação'),
                    ('agriculture', 'Agricultura'),
                    ('livestock', 'Pecuária'),
                    ('fisheries', 'Pescas'),
                    ('rural_development', 'Desenvolvimento Rural'),
                    ('energy', 'Energia'),
                    ('renewable_energy', 'Energias Renováveis'),
                    ('mining', 'Mineração'),
                    ('tourism', 'Turismo'),
                    ('commerce', 'Comércio'),
                    ('industry', 'Indústria'),
                    ('financial_services', 'Serviços Financeiros'),
                    ('private_sector', 'Sector Privado'),
                    ('infrastructure', 'Infraestruturas'),
                    ('transport', 'Transportes'),
                    ('roads', 'Estradas'),
                    ('ports', 'Portos'),
                    ('urban_development', 'Desenvolvimento Urbano'),
                    ('construction', 'Construção Civil'),
                    ('digital_infrastructure', 'Infraestruturas Digitais'),
                    ('governance', 'Governação'),
                    ('public_administration', 'Administração Pública'),
                    ('decentralization', 'Descentralização'),
                    ('justice', 'Justiça'),
                    ('human_rights', 'Direitos Humanos'),
                    ('civil_society', 'Sociedade Civil'),
                    ('elections', 'Processos Eleitorais'),
                    ('anti_corruption', 'Anti-Corrupção'),
                    ('environment', 'Ambiente'),
                    ('climate_change', 'Alterações Climáticas'),
                    ('biodiversity', 'Biodiversidade'),
                    ('waste_management', 'Gestão de Resíduos'),
                    ('sustainable_development', 'Desenvolvimento Sustentável'),
                    ('ict', 'ICT / Tecnologias de Informação'),
                    ('digital_transformation', 'Transformação Digital'),
                    ('cybersecurity', 'Cibersegurança'),
                    ('e_government', 'Governo Electrónico'),
                    ('data_science', 'Ciência de Dados'),
                    ('monitoring_evaluation', 'Monitoria e Avaliação'),
                    ('research', 'Investigação'),
                    ('capacity_building', 'Capacitação Institucional'),
                    ('procurement', 'Contratação Pública'),
                    ('supply_chain', 'Cadeia de Abastecimento'),
                    ('emergency_response', 'Resposta a Emergências'),
                    ('humanitarian_aid', 'Ajuda Humanitária'),
                    ('migration', 'Migração'),
                    ('youth_employment', 'Emprego Juvenil'),
                    ('cultural_heritage', 'Património Cultural'),
                    ('statistics', 'Estatística'),
                    ('telecom', 'Telecomunicações'),
                    ('maritime', 'Economia Azul / Marítimo'),
                ],
                max_length=100,
            ),
        ),
        # B2: Region choices
        migrations.AlterField(
            model_name='opportunity',
            name='region',
            field=models.CharField(
                blank=True,
                choices=[
                    ('west_africa', 'África Ocidental'),
                    ('central_africa', 'África Central'),
                    ('east_africa', 'África Oriental'),
                    ('southern_africa', 'África Austral'),
                    ('north_africa', 'Norte de África'),
                    ('lusophone_africa', 'África Lusófona'),
                    ('pacific', 'Pacífico'),
                    ('caribbean', 'Caraíbas'),
                    ('latin_america', 'América Latina'),
                    ('asia', 'Ásia'),
                    ('europe', 'Europa'),
                    ('middle_east', 'Médio Oriente'),
                    ('international', 'Internacional / Global'),
                ],
                max_length=100,
            ),
        ),
        # B2: Country with ISO 2-letter codes
        migrations.AlterField(
            model_name='opportunity',
            name='country',
            field=models.CharField(
                choices=[
                    ('cv', 'Cabo Verde'),
                    ('ao', 'Angola'),
                    ('mz', 'Moçambique'),
                    ('gw', 'Guiné-Bissau'),
                    ('st', 'São Tomé e Príncipe'),
                    ('tl', 'Timor-Leste'),
                    ('sn', 'Senegal'),
                    ('gn', 'Guiné-Conacri'),
                    ('sl', 'Serra Leoa'),
                    ('lr', 'Libéria'),
                    ('ci', 'Costa do Marfim'),
                    ('gh', 'Gana'),
                    ('tg', 'Togo'),
                    ('bj', 'Benim'),
                    ('ng', 'Nigéria'),
                    ('bf', 'Burkina Faso'),
                    ('ml', 'Mali'),
                    ('ne', 'Níger'),
                    ('gm', 'Gâmbia'),
                    ('mr', 'Mauritânia'),
                    ('cm', 'Camarões'),
                    ('cf', 'República Centro-Africana'),
                    ('td', 'Chade'),
                    ('ga', 'Gabão'),
                    ('cg', 'Congo'),
                    ('cd', 'República Democrática do Congo'),
                    ('gq', 'Guiné Equatorial'),
                    ('et', 'Etiópia'),
                    ('ke', 'Quénia'),
                    ('tz', 'Tanzânia'),
                    ('ug', 'Uganda'),
                    ('rw', 'Ruanda'),
                    ('bi', 'Burundi'),
                    ('so', 'Somália'),
                    ('ss', 'Sudão do Sul'),
                    ('sd', 'Sudão'),
                    ('dj', 'Djibouti'),
                    ('er', 'Eritreia'),
                    ('mg', 'Madagáscar'),
                    ('mu', 'Maurícia'),
                    ('km', 'Comores'),
                    ('sc', 'Seicheles'),
                    ('za', 'África do Sul'),
                    ('na', 'Namíbia'),
                    ('bw', 'Botswana'),
                    ('zw', 'Zimbabwe'),
                    ('zm', 'Zâmbia'),
                    ('mw', 'Malawi'),
                    ('ls', 'Lesoto'),
                    ('sz', 'Essuatíni'),
                    ('ma', 'Marrocos'),
                    ('dz', 'Argélia'),
                    ('tn', 'Tunísia'),
                    ('ly', 'Líbia'),
                    ('eg', 'Egipto'),
                    ('int', 'Internacional'),
                ],
                max_length=100,
            ),
        ),
        # B2: eligible_countries field (JSONB list of country codes)
        migrations.AddField(
            model_name='opportunity',
            name='eligible_countries',
            field=models.JSONField(blank=True, default=list, help_text='Lista de códigos de países elegíveis (ISO 2-letras)'),
        ),
        # Run data migrations to normalise existing values
        migrations.RunPython(_migrate_sectors, migrations.RunPython.noop),
        migrations.RunPython(_migrate_countries, migrations.RunPython.noop),
        migrations.RunPython(_migrate_regions, migrations.RunPython.noop),
    ]
