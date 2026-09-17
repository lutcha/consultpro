from django.db import migrations


NEW_EU_OPPORTUNITYHUB_SOURCES = [
    {
        'name': 'OpportunityHub EU - Platform Overview',
        'organization': 'Europe Startup Nations Alliance',
        'url': 'https://opportunityhub.eu/',
        'source_type': 'portal',
        'status': 'paused',
        'scrape_frequency': 'weekly',
        'scraper_class': 'GenericPortalScraper',
        'scraper_config': {
            'url': 'https://opportunityhub.eu/',
            'access': 'limited',
            'source_category': 'market_intelligence',
            'intelligence_mode': 'partial_intelligence',
            'notes': (
                'OpportunityHub home page is a navigation and ecosystem overview, '
                'not a transactional opportunity feed; keep paused and use as '
                'market intelligence/navigation until a stable data feed is available.'
            ),
            'organization': 'OpportunityHub / ESNA',
            'client': 'European startup ecosystem',
            'country': 'Europe',
            'language': 'en',
        },
        'filters': {
            'countries': ['Europe', 'EU'],
            'keywords': ['startup', 'innovation', 'funding', 'investment', 'relocation'],
            'category': 'market_intelligence',
            'access': ['limited'],
        },
    },
    {
        'name': 'OpportunityHub EU - Funding Opportunities',
        'organization': 'Europe Startup Nations Alliance',
        'url': 'https://opportunityhub.eu/funding/',
        'source_type': 'portal',
        'status': 'paused',
        'scrape_frequency': 'weekly',
        'scraper_class': 'GenericPortalScraper',
        'scraper_config': {
            'url': 'https://opportunityhub.eu/funding/',
            'access': 'limited',
            'source_category': 'startup_funding',
            'intelligence_mode': 'partial_intelligence',
            'item_selectors': ['article', 'div.elementor-widget-container', 'section', 'li'],
            'title_selector': 'h2, h3, h4, a, strong',
            'link_selector': 'a[href]',
            'description_selector': 'p, div',
            'organization': 'OpportunityHub / ESNA',
            'client': 'European startup ecosystem',
            'country': 'Europe',
            'language': 'en',
            'notes': (
                'Funding page exposes visible startup funding programme listings, '
                'but items are aggregator intelligence without reliable deadlines '
                'or tender metadata. Keep paused for partial intelligence until '
                'accepted/rejected counts and false positives are measured in staging.'
            ),
        },
        'filters': {
            'countries': ['Europe', 'EU'],
            'keywords': ['startup funding', 'grant', 'accelerator', 'tax credit', 'loan', 'investment'],
            'category': 'startup_funding',
            'access': ['limited'],
        },
    },
    {
        'name': 'OpportunityHub EU - Tech Heatmap',
        'organization': 'Europe Startup Nations Alliance',
        'url': 'https://opportunityhub.eu/eu-tech-heatmap/',
        'source_type': 'portal',
        'status': 'paused',
        'scrape_frequency': 'weekly',
        'scraper_class': 'GenericPortalScraper',
        'scraper_config': {
            'url': 'https://opportunityhub.eu/eu-tech-heatmap/',
            'access': 'limited',
            'source_category': 'market_intelligence',
            'intelligence_mode': 'partial_intelligence',
            'notes': (
                'Tech heatmap is sector/country market intelligence rather than '
                'an opportunity feed; keep paused to avoid importing non-tender '
                'content as opportunities.'
            ),
            'organization': 'OpportunityHub / ESNA',
            'client': 'European startup ecosystem',
            'country': 'Europe',
            'language': 'en',
        },
        'filters': {
            'countries': ['Europe', 'EU'],
            'keywords': ['fintech', 'deep tech', 'artificial intelligence', 'sustainability tech', 'saas'],
            'category': 'market_intelligence',
            'access': ['limited'],
        },
    },
    {
        'name': 'EIC - Funding Opportunities',
        'organization': 'European Innovation Council',
        'url': 'https://eic.ec.europa.eu/eic-funding-opportunities_en',
        'source_type': 'portal',
        'status': 'active',
        'scrape_frequency': 'weekly',
        'scraper_class': 'GenericPortalScraper',
        'scraper_config': {
            'url': 'https://eic.ec.europa.eu/eic-funding-opportunities_en',
            'source_category': 'eu_grants',
            'item_selectors': ['article', 'div.ecl-content-block', 'section', 'li'],
            'title_selector': 'h2, h3, h4, a, strong',
            'link_selector': 'a[href]',
            'description_selector': 'p, div',
            'deadline_selector': 'time, .deadline, .date, .ecl-u-type-color-grey',
            'organization': 'European Innovation Council',
            'client': 'European Commission / EISMEA',
            'country': 'Europe / International',
            'language': 'en',
            'notes': (
                'Official EIC funding page has visible open calls and deadline '
                'dates; use generic HTML parsing first, then validate counts in staging.'
            ),
        },
        'filters': {
            'countries': ['Europe', 'EU', 'Africa'],
            'keywords': [
                'EIC Accelerator', 'EIC Pathfinder', 'EIC Transition',
                'STEP Scale Up', 'grant', 'investment', 'deep tech',
            ],
            'category': 'eu_grants',
        },
    },
    {
        'name': 'EU Funding & Tenders - Calls for Tenders',
        'organization': 'European Commission',
        'url': 'https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/calls-for-tenders?isExactMatch=true&order=DESC&pageNumber=1&pageSize=50&sortBy=startDate',
        'source_type': 'api',
        'status': 'paused',
        'scrape_frequency': 'daily',
        'scraper_class': 'EUFundingScraper',
        'scraper_config': {
            'url': 'https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/calls-for-tenders?isExactMatch=true&order=DESC&pageNumber=1&pageSize=50&sortBy=startDate',
            'source_category': 'eu_tenders',
            'access': 'dynamic_portal',
            'reference_data_url': 'https://ec.europa.eu/info/funding-tenders/opportunities/data/referenceData/grantProgramme',
            'organization': 'European Commission',
            'client': 'EU Funding & Tenders Portal',
            'country': 'Europe / International',
            'language': 'en',
            'notes': (
                'EU Funding & Tenders public route is a dynamic portal route. '
                'Keep paused until the underlying calls-for-tenders JSON/API '
                'contract is confirmed for server-side ingestion.'
            ),
        },
        'filters': {
            'countries': ['Europe', 'EU', 'Africa', 'CPV'],
            'keywords': ['call for tender', 'procurement', 'framework contract', 'consultancy', 'technical assistance'],
            'category': 'eu_tenders',
            'access': ['dynamic_portal'],
        },
        'verify_ssl': True,
        'respect_robots_txt': True,
    },
]


def apply_migration(apps, schema_editor):
    ScrapingSource = apps.get_model('scraping', 'ScrapingSource')
    for src in NEW_EU_OPPORTUNITYHUB_SOURCES:
        defaults = {
            'organization': src['organization'],
            'url': src['url'],
            'source_type': src['source_type'],
            'status': src['status'],
            'scrape_frequency': src['scrape_frequency'],
            'scraper_class': src['scraper_class'],
            'scraper_config': src.get('scraper_config', {}),
            'filters': src.get('filters', {}),
            'verify_ssl': src.get('verify_ssl', True),
            'respect_robots_txt': src.get('respect_robots_txt', True),
        }
        ScrapingSource.objects.update_or_create(name=src['name'], defaults=defaults)


def revert_migration(apps, schema_editor):
    ScrapingSource = apps.get_model('scraping', 'ScrapingSource')
    names = [source['name'] for source in NEW_EU_OPPORTUNITYHUB_SOURCES]
    ScrapingSource.objects.filter(name__in=names).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('scraping', '0014_update_reliable_production_sources'),
    ]

    operations = [
        migrations.RunPython(apply_migration, revert_migration),
    ]
