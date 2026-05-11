"""
Constants for Opportunities App.
Centralised sector, region, and country taxonomies.
"""

# ============================================
# SECTOR TAXONOMY (30+ choices)
# ============================================
SECTOR_CHOICES = [
    # Social sectors
    ('education', 'Educação'),
    ('health', 'Saúde'),
    ('social_protection', 'Protecção Social'),
    ('gender', 'Género e Igualdade'),
    ('water_sanitation', 'Água e Saneamento'),
    ('food_security', 'Segurança Alimentar'),
    ('nutrition', 'Nutrição'),
    ('housing', 'Habitação'),

    # Economic sectors
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

    # Infrastructure & Transport
    ('infrastructure', 'Infraestruturas'),
    ('transport', 'Transportes'),
    ('roads', 'Estradas'),
    ('ports', 'Portos'),
    ('aviation', 'Aviação Civil'),
    ('urban_development', 'Desenvolvimento Urbano'),
    ('construction', 'Construção Civil'),
    ('digital_infrastructure', 'Infraestruturas Digitais'),

    # Governance & Institutional
    ('governance', 'Governação'),
    ('public_administration', 'Administração Pública'),
    ('decentralization', 'Descentralização'),
    ('justice', 'Justiça'),
    ('human_rights', 'Direitos Humanos'),
    ('civil_society', 'Sociedade Civil'),
    ('elections', 'Processos Eleitorais'),
    ('anti_corruption', 'Anti-Corrupção'),

    # Environment & Climate
    ('environment', 'Ambiente'),
    ('climate_change', 'Alterações Climáticas'),
    ('biodiversity', 'Biodiversidade'),
    ('waste_management', 'Gestão de Resíduos'),
    ('sustainable_development', 'Desenvolvimento Sustentável'),

    # Technology & Digital
    ('ict', 'ICT / Tecnologias de Informação'),
    ('digital_transformation', 'Transformação Digital'),
    ('cybersecurity', 'Cibersegurança'),
    ('e_government', 'Governo Electrónico'),
    ('data_science', 'Ciência de Dados'),

    # Cross-cutting
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
    ('aviation', 'Aviação'),  # duplicate removed from choices dict
]

# Deduplicate while preserving order
_SEEN = set()
SECTOR_CHOICES_UNIQUE = []
for code, label in SECTOR_CHOICES:
    if code not in _SEEN:
        _SEEN.add(code)
        SECTOR_CHOICES_UNIQUE.append((code, label))
SECTOR_CHOICES = SECTOR_CHOICES_UNIQUE

# ============================================
# REGION TAXONOMY
# ============================================
REGION_CHOICES = [
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
]

# ============================================
# COUNTRY TAXONOMY (West Africa + Lusophone focus)
# ============================================
COUNTRY_CHOICES = [
    # Lusophone Africa (priority)
    ('cv', 'Cabo Verde'),
    ('ao', 'Angola'),
    ('mz', 'Moçambique'),
    ('gw', 'Guiné-Bissau'),
    ('st', 'São Tomé e Príncipe'),
    ('tl', 'Timor-Leste'),

    # West Africa
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

    # Central Africa
    ('cm', 'Camarões'),
    ('cf', 'República Centro-Africana'),
    ('td', 'Chade'),
    ('ga', 'Gabão'),
    ('cg', 'Congo'),
    ('cd', 'República Democrática do Congo'),
    ('gq', 'Guiné Equatorial'),

    # East Africa
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

    # Southern Africa
    ('za', 'África do Sul'),
    ('na', 'Namíbia'),
    ('bw', 'Botswana'),
    ('zw', 'Zimbabwe'),
    ('zm', 'Zâmbia'),
    ('mw', 'Malawi'),
    ('ls', 'Lesoto'),
    ('sz', 'Essuatíni'),

    # North Africa
    ('ma', 'Marrocos'),
    ('dz', 'Argélia'),
    ('tn', 'Tunísia'),
    ('ly', 'Líbia'),
    ('eg', 'Egipto'),

    # International
    ('int', 'Internacional'),
]

# ============================================
# HELPER DICTS
# ============================================
SECTOR_LABELS = dict(SECTOR_CHOICES)
REGION_LABELS = dict(REGION_CHOICES)
COUNTRY_LABELS = dict(COUNTRY_CHOICES)

# Map country code → region(s)
COUNTRY_REGION_MAP = {
    'cv': ['west_africa', 'lusophone_africa'],
    'ao': ['southern_africa', 'lusophone_africa'],
    'mz': ['east_africa', 'southern_africa', 'lusophone_africa'],
    'gw': ['west_africa', 'lusophone_africa'],
    'st': ['central_africa', 'lusophone_africa'],
    'tl': ['asia'],
    'sn': ['west_africa'],
    'gn': ['west_africa'],
    'sl': ['west_africa'],
    'lr': ['west_africa'],
    'ci': ['west_africa'],
    'gh': ['west_africa'],
    'tg': ['west_africa'],
    'bj': ['west_africa'],
    'ng': ['west_africa'],
    'bf': ['west_africa'],
    'ml': ['west_africa'],
    'ne': ['west_africa'],
    'gm': ['west_africa'],
    'mr': ['west_africa'],
    'cm': ['central_africa'],
    'cf': ['central_africa'],
    'td': ['central_africa'],
    'ga': ['central_africa'],
    'cg': ['central_africa'],
    'cd': ['central_africa'],
    'gq': ['central_africa'],
    'et': ['east_africa'],
    'ke': ['east_africa'],
    'tz': ['east_africa'],
    'ug': ['east_africa'],
    'rw': ['east_africa'],
    'bi': ['east_africa'],
    'so': ['east_africa'],
    'ss': ['east_africa'],
    'sd': ['east_africa'],
    'dj': ['east_africa'],
    'er': ['east_africa'],
    'mg': ['east_africa'],
    'mu': ['east_africa'],
    'km': ['east_africa'],
    'sc': ['east_africa'],
    'za': ['southern_africa'],
    'na': ['southern_africa'],
    'bw': ['southern_africa'],
    'zw': ['southern_africa'],
    'zm': ['southern_africa'],
    'mw': ['southern_africa'],
    'ls': ['southern_africa'],
    'sz': ['southern_africa'],
    'ma': ['north_africa'],
    'dz': ['north_africa'],
    'tn': ['north_africa'],
    'ly': ['north_africa'],
    'eg': ['north_africa'],
    'int': ['international'],
}


def get_regions_for_country(code: str) -> list:
    """Return region codes for a given country code."""
    return COUNTRY_REGION_MAP.get(code, [])
