"""
C3 — Import-time enrichment.
Detects sector, country, region, eligible_countries, consortium_type
from scraped opportunity text before the Opportunity record is created.
All public functions return safe defaults and never raise.
"""
import logging

from apps.opportunities.constants import (
    COUNTRY_REGION_MAP,
    SECTOR_CHOICES,
    COUNTRY_CHOICES,
)
from apps.scraping.services.cos_scope import classify_cos_scope_text

logger = logging.getLogger(__name__)

VALID_SECTORS = {code for code, _ in SECTOR_CHOICES}
VALID_COUNTRIES = {code for code, _ in COUNTRY_CHOICES}

# ── Sector keyword table (most specific first) ─────────────────────────────────
_SECTOR_KEYWORDS: list = [
    ('renewable_energy', ['solar', 'eólica', 'wind energy', 'energias renováveis', 'renewable energy', 'fotovoltai', 'biomassa']),
    ('water_sanitation', ['saneamento', 'sanitation', 'abastecimento de água', 'water supply', 'wash', 'irrigação', 'irrigation']),
    ('food_security', ['segurança alimentar', 'food security']),
    ('digital_transformation', ['transformação digital', 'digital transformation', 'digitalização', 'digitalization']),
    ('e_government', ['governo electrónico', 'e-government', 'governo digital']),
    ('climate_change', ['alterações climáticas', 'climate change', 'mudança climática', 'low-carbon', 'carbon emission']),
    ('capacity_building', ['capacitação', 'capacity building', 'capacity development', 'formação profissional']),
    ('monitoring_evaluation', ['monitoria e avaliação', 'monitoring and evaluation', 'm&e', 'monitoring & evaluation']),
    ('social_protection', ['protecção social', 'social protection', 'proteção social']),
    ('rural_development', ['desenvolvimento rural', 'rural development', 'comunidade rural']),
    ('urban_development', ['desenvolvimento urbano', 'urban development', 'urbanização']),
    ('public_administration', ['administração pública', 'public administration', 'reforma do estado', 'public sector reform']),
    ('anti_corruption', ['anti-corrupção', 'anti-corruption', 'transparência institucional', 'integridade pública']),
    ('human_rights', ['direitos humanos', 'human rights']),
    ('humanitarian_aid', ['humanitária', 'humanitarian', 'ajuda de emergência', 'emergency aid', 'refugee', 'refugiado']),
    ('emergency_response', ['resposta a emergência', 'emergency response', 'disaster response', 'resposta a desastres']),
    ('migration', ['migração', 'migration', 'migrante', 'deslocado forçado']),
    ('private_sector', ['sector privado', 'private sector', 'desenvolvimento empresarial', 'business development']),
    ('financial_services', ['serviços financeiros', 'financial services', 'microfinanças', 'microfinance', 'bancário', 'banking']),
    ('energy', ['energia', 'energy', 'electricidade', 'electricity', 'power sector', 'grid']),
    ('infrastructure', ['infraestrutura', 'infrastructure', 'obras públicas', 'public works']),
    ('transport', ['transporte', 'transport', 'rodoviário', 'estradas', 'roads', 'mobilidade']),
    ('ports', ['porto marítimo', 'seaport', 'maritime port']),
    ('aviation', ['aviação', 'aviation', 'aeroporto', 'airport']),
    ('digital_infrastructure', ['infraestrutura digital', 'digital infrastructure', 'fibra óptica', 'fiber optic']),
    ('telecom', ['telecomunicações', 'telecommunications', 'telecom sector']),
    ('ict', ['ict', 'tecnologia de informação', 'information technology', 'sistema de informação', 'software', 'informática']),
    ('cybersecurity', ['cibersegurança', 'cybersecurity', 'segurança informática']),
    ('data_science', ['ciência de dados', 'data science', 'análise de dados', 'data analytics']),
    ('statistics', ['estatística', 'statistics', 'recenseamento', 'census', 'household survey']),
    ('maritime', ['economia azul', 'blue economy', 'marítimo', 'maritime economy', 'oceanografia']),
    ('fisheries', ['pescas', 'fisheries', 'pesca artesanal', 'aquacultura', 'aquaculture']),
    ('agriculture', ['agricultura', 'agriculture', 'agrícola', 'agricultural', 'agro', 'cultivo', 'crop']),
    ('livestock', ['pecuária', 'livestock', 'gado', 'animal husbandry', 'veterinário']),
    ('environment', ['ambiente', 'environment', 'ambiental', 'environmental management']),
    ('biodiversity', ['biodiversidade', 'biodiversity', 'ecossistema', 'ecosystem']),
    ('waste_management', ['gestão de resíduos', 'waste management', 'resíduos sólidos', 'solid waste']),
    ('sustainable_development', ['desenvolvimento sustentável', 'sustainable development']),
    ('education', ['educação', 'education', 'escola', 'school', 'ensino', 'formação académica', 'universit']),
    ('health', ['saúde', 'health', 'hospital', 'médico', 'clínica', 'malária', 'hiv', 'epidemiol', 'public health']),
    ('housing', ['habitação', 'housing', 'moradia', 'alojamento']),
    ('gender', ['género', 'gender', 'mulher', 'women', 'igualdade de género', 'gender equality']),
    ('nutrition', ['nutrição', 'nutrition', 'alimentação infantil', 'stunting', 'wasting']),
    ('youth_employment', ['emprego juvenil', 'youth employment', 'emprego jovem', 'youth entrepreneurship']),
    ('civil_society', ['sociedade civil', 'civil society', 'associações', 'ngo', 'ong ']),
    ('governance', ['governação', 'governance', 'governança', 'boa governação', 'good governance']),
    ('decentralization', ['descentralização', 'decentralization', 'governação local', 'local governance', 'municipal']),
    ('justice', ['justiça', 'justice', 'reform judicial', 'tribunal', 'court', 'legal reform']),
    ('elections', ['eleições', 'elections', 'eleitoral', 'electoral process']),
    ('research', ['investigação', 'research', 'estudo diagnóstico', 'diagnostic study', 'baseline study']),
    ('procurement', ['contratação pública', 'public procurement', 'aquisição pública']),
    ('supply_chain', ['cadeia de abastecimento', 'supply chain', 'logística', 'logistics']),
    ('cultural_heritage', ['património cultural', 'cultural heritage']),
    ('tourism', ['turismo', 'tourism', 'turístico']),
    ('mining', ['mineração', 'mining', 'mineiro', 'geologia extractiva']),
    ('commerce', ['comércio regional', 'regional trade', 'facilitação do comércio', 'trade facilitation']),
    ('industry', ['indústria', 'industry', 'industrial development']),
]

_COS_SECTOR_KEYWORDS = [
    ('digital_transformation', ['govtech', 'digital public infrastructure', 'smart government', 'digital services', 'interoperability']),
    ('data_science', ['artificial intelligence', 'ai governance', 'data project', 'data analytics']),
    ('capacity_building', ['training services', 'coaching', 'mentoring', 'institutional support']),
    ('monitoring_evaluation', ['impact assessment', 'evaluation', 'baseline study', 'monitoring & evaluation']),
    ('private_sector', ['msme development', 'sme development', 'entrepreneurship', 'startup ecosystem', 'incubation', 'acceleration']),
    ('financial_services', ['financial inclusion', 'blended finance', 'development finance', 'investment readiness']),
    ('environment', ['environmental governance', 'green economy', 'circular economy']),
    ('research', ['feasibility study', 'diagnostic', 'assessment', 'study']),
    ('public_administration', ['public sector modernization', 'institutional strengthening', 'regulatory reform']),
    ('procurement', ['procurement reform', 'public procurement reform']),
]
_SECTOR_KEYWORDS = _COS_SECTOR_KEYWORDS + _SECTOR_KEYWORDS

# ── Country name → ISO-2 code ──────────────────────────────────────────────────
_COUNTRY_NAMES: dict = {
    'cabo verde': 'cv', 'cape verde': 'cv',
    'angola': 'ao',
    'moçambique': 'mz', 'mozambique': 'mz',
    'guiné-bissau': 'gw', 'guinea-bissau': 'gw', 'guinea bissau': 'gw',
    'são tomé e príncipe': 'st', 'sao tome': 'st', 'são tomé': 'st',
    'timor-leste': 'tl', 'timor leste': 'tl', 'east timor': 'tl', 'timor': 'tl',
    'senegal': 'sn', 'sénégal': 'sn',
    'guinea': 'gn', 'guinée': 'gn', 'guiné-conacri': 'gn', 'guinea conakry': 'gn',
    'sierra leone': 'sl', 'serra leoa': 'sl',
    'liberia': 'lr', 'libéria': 'lr',
    "côte d'ivoire": 'ci', 'ivory coast': 'ci', 'costa do marfim': 'ci',
    'ghana': 'gh', 'gana': 'gh',
    'togo': 'tg',
    'bénin': 'bj', 'benin': 'bj', 'benim': 'bj',
    'nigeria': 'ng', 'nigéria': 'ng',
    'burkina faso': 'bf',
    'mali': 'ml',
    'the gambia': 'gm', 'gambia': 'gm', 'gâmbia': 'gm',
    'mauritania': 'mr', 'mauritânia': 'mr', 'mauritanie': 'mr',
    'cameroon': 'cm', 'camarões': 'cm', 'cameroun': 'cm',
    'central african republic': 'cf', 'república centro-africana': 'cf',
    'chad': 'td', 'chade': 'td', 'tchad': 'td',
    'gabon': 'ga', 'gabão': 'ga',
    'republic of the congo': 'cg',
    'democratic republic of the congo': 'cd', 'drc': 'cd',
    'equatorial guinea': 'gq', 'guinée équatoriale': 'gq', 'guiné equatorial': 'gq',
    'ethiopia': 'et', 'etiópia': 'et',
    'kenya': 'ke', 'quénia': 'ke',
    'tanzania': 'tz', 'tanzânia': 'tz',
    'uganda': 'ug',
    'rwanda': 'rw', 'ruanda': 'rw',
    'burundi': 'bi',
    'somalia': 'so', 'somália': 'so',
    'south sudan': 'ss', 'sudão do sul': 'ss',
    'sudan': 'sd', 'sudão': 'sd',
    'djibouti': 'dj',
    'eritrea': 'er', 'eritreia': 'er',
    'madagascar': 'mg', 'madagáscar': 'mg',
    'mauritius': 'mu', 'maurícia': 'mu',
    'comoros': 'km', 'comores': 'km',
    'seychelles': 'sc', 'seicheles': 'sc',
    'south africa': 'za', 'áfrica do sul': 'za',
    'namibia': 'na', 'namíbia': 'na',
    'botswana': 'bw',
    'zimbabwe': 'zw',
    'zambia': 'zm', 'zâmbia': 'zm',
    'malawi': 'mw',
    'lesotho': 'ls', 'lesoto': 'ls',
    'eswatini': 'sz', 'essuatíni': 'sz', 'swaziland': 'sz',
    'morocco': 'ma', 'marrocos': 'ma', 'maroc': 'ma',
    'algeria': 'dz', 'argélia': 'dz', 'algérie': 'dz',
    'tunisia': 'tn', 'tunísia': 'tn', 'tunisie': 'tn',
    'libya': 'ly', 'líbia': 'ly', 'libye': 'ly',
    'egypt': 'eg', 'egipto': 'eg', 'égypte': 'eg',
    'niger': 'ne', 'níger': 'ne',
}

# ── Consortium markers ─────────────────────────────────────────────────────────
_LEAD_KW = ['lead firm', 'lead consultant', 'chef de file', 'lead organization', 'firma líder', 'liderança do consórcio']
_PARTNER_KW = ['partner firm', 'sub-consultant', 'consortium partner', 'parceiro de consórcio', 'join as partner']
_OPEN_KW = ['consortium', 'consórcio', 'joint venture', 'groupement', 'parceria estratégica']


# ── Public API ─────────────────────────────────────────────────────────────────

def detect_sector(text: str, existing: str = '') -> str:
    if existing and existing in VALID_SECTORS:
        return existing
    low = text.lower()
    for code, keywords in _SECTOR_KEYWORDS:
        if any(kw in low for kw in keywords):
            return code
    return 'governance'


def detect_country(text: str, existing: str = '') -> str:
    if existing:
        low_ex = existing.lower().strip()
        if low_ex in VALID_COUNTRIES:
            return low_ex
        if low_ex in _COUNTRY_NAMES:
            return _COUNTRY_NAMES[low_ex]
    low = text.lower()
    best_code = 'int'
    best_len = 0
    for name, code in _COUNTRY_NAMES.items():
        if name in low and len(name) > best_len:
            best_code = code
            best_len = len(name)
    return best_code


def detect_region(country_code: str) -> str:
    regions = COUNTRY_REGION_MAP.get(country_code, [])
    return regions[0] if regions else 'international'


def detect_eligible_countries(scraped_opp) -> list:
    codes: set = set()

    # From geographic_scope.countries already stored on the scraped record
    scope = scraped_opp.geographic_scope or {}
    for c in scope.get('countries', []):
        low = str(c).lower().strip()
        if low in VALID_COUNTRIES:
            codes.add(low)
        elif low in _COUNTRY_NAMES:
            codes.add(_COUNTRY_NAMES[low])

    # Always include the primary detected country
    primary = detect_country('', scraped_opp.country or '')
    if primary and primary != 'int':
        codes.add(primary)

    # If the scope is regional, scan description for additional country names
    if scope.get('scope') in ('regional', 'sub-regional') or not codes:
        region_text = ' '.join(filter(None, [
            scraped_opp.region or '',
            (scraped_opp.description or '')[:600],
        ])).lower()
        for name, code in _COUNTRY_NAMES.items():
            if code != 'int' and name in region_text:
                codes.add(code)

    return sorted(codes)


def detect_consortium_type(text: str) -> str:
    low = text.lower()
    if any(kw in low for kw in _LEAD_KW):
        return 'lead'
    if any(kw in low for kw in _PARTNER_KW):
        return 'partner'
    if any(kw in low for kw in _OPEN_KW):
        return 'open'
    return 'solo'


def enrich_for_import(scraped_opp) -> dict:
    """
    Return enriched field values for Opportunity.objects.create().
    Never raises — all errors fall back to safe defaults.
    """
    lookup = ' '.join(filter(None, [
        scraped_opp.title or '',
        scraped_opp.description or '',
        scraped_opp.deep_content_text or '',
        scraped_opp.organization or '',
    ]))[:10000]

    try:
        sector = detect_sector(lookup, scraped_opp.sector or '')
        country = detect_country(lookup, scraped_opp.country or '')
        region = detect_region(country)
        eligible = detect_eligible_countries(scraped_opp)
        consortium = detect_consortium_type(lookup)
        cos_scope = classify_cos_scope_text(lookup)
        logger.info(
            'C3 enrich id=%s sector=%s country=%s region=%s eligible=%s consortium=%s',
            scraped_opp.id, sector, country, region, eligible, consortium,
        )
        return {
            'sector': sector,
            'country': country,
            'region': region,
            'eligible_countries': eligible,
            'consortium_type': consortium,
            'cos_scope': cos_scope,
        }
    except Exception as exc:
        logger.warning('C3 enrichment failed for id=%s: %s', scraped_opp.id, exc)
        return {
            'sector': scraped_opp.sector or 'governance',
            'country': scraped_opp.country or 'int',
            'region': '',
            'eligible_countries': [],
            'consortium_type': 'solo',
            'cos_scope': {},
        }
