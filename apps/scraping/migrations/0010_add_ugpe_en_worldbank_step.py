"""
Add specific high-value scraping sources:
  - UGPE EN  (English concursos page — https://ugpe.gov.cv/en/concursos)
  - World Bank STEP  (Systematic Tracking of Exchanges in Procurement)
  - World Bank Projects Contracts  (projects.worldbank.org contracts view)

Also updates the existing 'World Bank - Operational Consulting' source to
include contracts in its filter query so signed contracts appear alongside notices.
"""
from django.db import migrations

NEW_SOURCES = [
    # ── UGPE English version ──────────────────────────────────────────────────
    {
        'name': 'UGPE - Concursos Cabo Verde (EN)',
        'organization': 'UGPE',
        'url': 'https://ugpe.gov.cv/en/concursos',
        'source_type': 'portal',
        'status': 'active',
        'scrape_frequency': 'daily',
        'scraper_class': 'UGPEScraper',
        'scraper_config': {
            'url': 'https://ugpe.gov.cv/en/concursos',
            'item_selectors': [
                'table.concursos-table tbody tr',
                'div.concurso-item',
                'div.opportunity-item',
                'table tbody tr',
                'article',
                'div.item',
            ],
        },
        'filters': {
            'countries': ['CPV'],
            'keywords': ['consultancy', 'consultant', 'tender', 'procurement', 'services'],
        },
        'verify_ssl': True,
        'respect_robots_txt': True,
    },

    # ── World Bank STEP ───────────────────────────────────────────────────────
    #
    # STEP (Systematic Tracking of Exchanges in Procurement) is the WB's
    # procurement management platform used by borrower countries.
    # Public procurement notices from STEP are indexed in the main WB
    # procurement API — we target a STEP-specific filter here.
    {
        'name': 'World Bank STEP - Procurement Notices',
        'organization': 'World Bank Group',
        'url': 'https://step.worldbank.org',
        'source_type': 'api',
        'status': 'active',
        'scrape_frequency': 'daily',
        'scraper_class': 'WorldBankScraper',
        'scraper_config': {
            'url': 'https://step.worldbank.org',
            'api_url': 'https://search.worldbank.org/api/v2/procurement',
            'fields': (
                'id,title,deadline,pdate,countryname,regionname,'
                'project_name,url,borrower,sector,docty,source'
            ),
            # 'status:Active' + include STEP-sourced notices
            'filter_query': 'docty:Notice AND status:Active AND source:STEP',
            'page_size': 50,
            'max_items': 300,
        },
        'filters': {
            'countries': ['CPV', 'Africa', 'West Africa'],
            'keywords': [
                'consultant', 'consulting', 'advisory', 'technical assistance',
                'individual consultant', 'firm', 'request for proposal',
                'expression of interest', 'request for quotation',
            ],
        },
        'verify_ssl': True,
        'respect_robots_txt': True,
    },

    # ── World Bank Projects — Contracts ───────────────────────────────────────
    #
    # This targets the "contracts awarded" view at projects.worldbank.org,
    # which shows signed contracts (not just procurement notices).
    # Uses the WB search API with a contracts-specific filter.
    {
        'name': 'World Bank Projects - Contracts Awarded',
        'organization': 'World Bank Group',
        'url': 'https://projects.worldbank.org/pt/projects-operations/procurement?qterm=&showrecent=true&srce=contracts',
        'source_type': 'api',
        'status': 'active',
        'scrape_frequency': 'weekly',
        'scraper_class': 'WorldBankScraper',
        'scraper_config': {
            'url': 'https://projects.worldbank.org/pt/projects-operations/procurement',
            'api_url': 'https://search.worldbank.org/api/v2/procurement',
            'fields': (
                'id,title,deadline,pdate,countryname,regionname,'
                'project_name,url,borrower,sector,docty,cont_frmwrk'
            ),
            # Contracts awarded — signed contracts not just active notices
            'filter_query': 'docty:(Contract Award Notice OR Notice of Signed Contract)',
            'page_size': 50,
            'max_items': 200,
        },
        'filters': {
            'countries': ['CPV', 'Africa'],
            'keywords': [
                'consultant', 'consulting', 'advisory', 'technical assistance',
                'individual consultant', 'firm',
            ],
        },
        'verify_ssl': True,
        'respect_robots_txt': True,
    },
]

# Update the existing WB operational consulting source to widen its filter
UPDATES = [
    {
        'name': 'World Bank - Operational Consulting',
        'patch': {
            'scraper_config': {
                'url': 'https://www.worldbank.org/en/about/corporate-procurement/business-opportunities/operational-consulting-opportunities',
                'api_url': 'https://search.worldbank.org/api/v2/procurement',
                'fields': 'id,title,deadline,pdate,countryname,regionname,project_name,url,borrower,sector,docty',
                'filter_query': 'docty:(Notice OR Request for Expressions of Interest) AND status:Active',
                'page_size': 50,
                'max_items': 200,
            },
        },
    },
]


def apply_migration(apps, schema_editor):
    ScrapingSource = apps.get_model('scraping', 'ScrapingSource')

    for src in NEW_SOURCES:
        defaults = {
            'organization': src['organization'],
            'url': src['url'],
            'source_type': src['source_type'],
            'status': src['status'],
            'scrape_frequency': src['scrape_frequency'],
            'scraper_class': src['scraper_class'],
            'scraper_config': src['scraper_config'],
            'filters': src['filters'],
        }
        if 'verify_ssl' in src:
            defaults['verify_ssl'] = src['verify_ssl']
        if 'respect_robots_txt' in src:
            defaults['respect_robots_txt'] = src['respect_robots_txt']
        ScrapingSource.objects.update_or_create(name=src['name'], defaults=defaults)

    for upd in UPDATES:
        ScrapingSource.objects.filter(name=upd['name']).update(**upd['patch'])


def revert_migration(apps, schema_editor):
    ScrapingSource = apps.get_model('scraping', 'ScrapingSource')
    names = [s['name'] for s in NEW_SOURCES]
    ScrapingSource.objects.filter(name__in=names).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('scraping', '0009_add_c1_c2_sources'),
    ]

    operations = [
        migrations.RunPython(apply_migration, revert_migration),
    ]
