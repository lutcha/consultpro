from django.db import migrations

NEW_SOURCES = [
    {
        'name': 'GIZ - International Tenders',
        'organization': 'Deutsche Gesellschaft für Internationale Zusammenarbeit (GIZ)',
        'url': 'https://www.giz.de/en/jobs/tenders.html',
        'source_type': 'portal',
        'status': 'active',
        'scrape_frequency': 'daily',
        'scraper_class': 'GenericPortalScraper',
        'scraper_config': {
            'url': 'https://www.giz.de/en/jobs/tenders.html',
            'item_selectors': ['div.teaserbox', 'article.tender', 'div.result-item', 'li.result', 'tr'],
            'title_selector': 'h2, h3, h4, a',
            'link_selector': 'a[href]',
            'description_selector': 'p, div.description, div.teaser-text',
            'deadline_selector': '.deadline, .date, time, td:last-child',
            'organization': 'GIZ',
            'client': 'GIZ / BMZ Germany',
            'country': 'Africa / International',
            'language': 'en',
        },
        'filters': {
            'countries': ['Africa', 'CPV', 'PALOP'],
            'keywords': ['consultant', 'consultancy', 'expert', 'advisory', 'technical assistance', 'framework', 'tender'],
        },
    },
    {
        'name': "AFD - Appels d'Offres / Calls for Tenders",
        'organization': 'Agence Française de Développement (AFD)',
        'url': 'https://www.afd.fr/en/calls-for-tenders',
        'source_type': 'portal',
        'status': 'active',
        'scrape_frequency': 'daily',
        'scraper_class': 'GenericPortalScraper',
        'scraper_config': {
            'url': 'https://www.afd.fr/en/calls-for-tenders',
            'item_selectors': ['article', 'div.tender-item', 'div.appel-offre', 'li.node', 'div.card'],
            'title_selector': 'h2, h3, h4, a.title, a',
            'link_selector': 'a[href]',
            'description_selector': 'p, div.field-body, div.description',
            'deadline_selector': '.field-deadline, .date, time, span.date',
            'organization': 'AFD',
            'client': 'Agence Française de Développement',
            'country': 'Africa / International',
            'language': 'en',
        },
        'filters': {
            'countries': ['Africa', 'CPV', 'PALOP', 'Guinea-Bissau', 'Senegal', 'Mauritania'],
            'keywords': ['consultant', 'consultancy', 'expertise', 'tender', 'advisory', 'mission'],
        },
    },
    {
        'name': 'IFAD - Procurement Notices',
        'organization': 'International Fund for Agricultural Development (IFAD)',
        'url': 'https://www.ifad.org/en/procurement',
        'source_type': 'portal',
        'status': 'active',
        'scrape_frequency': 'weekly',
        'scraper_class': 'GenericPortalScraper',
        'scraper_config': {
            'url': 'https://www.ifad.org/en/procurement',
            'item_selectors': ['div.procurement-item', 'article', 'tr', 'li', 'div.node'],
            'title_selector': 'h2, h3, h4, a',
            'link_selector': 'a[href]',
            'description_selector': 'p, div.body',
            'deadline_selector': '.deadline, .closing-date, td:last-child, time',
            'organization': 'IFAD',
            'client': 'International Fund for Agricultural Development',
            'country': 'Africa / International',
            'language': 'en',
        },
        'filters': {
            'countries': ['Africa', 'CPV'],
            'keywords': ['consultant', 'consultancy', 'expert', 'advisory', 'agricultural', 'rural'],
        },
    },
    {
        'name': 'EU INTPA - Calls for Proposals (Africa)',
        'organization': 'European Commission / DG INTPA',
        'url': 'https://ec.europa.eu/international-partnerships/funding/calls-proposals_en',
        'source_type': 'portal',
        'status': 'active',
        'scrape_frequency': 'weekly',
        'scraper_class': 'GenericPortalScraper',
        'scraper_config': {
            'url': 'https://ec.europa.eu/international-partnerships/funding/calls-proposals_en',
            'item_selectors': ['article', 'div.ecl-content-item', 'div.result-item', 'li', 'tr'],
            'title_selector': 'h2, h3, a.ecl-link, a',
            'link_selector': 'a[href]',
            'description_selector': 'p, div.ecl-description',
            'deadline_selector': 'time, .date, .deadline',
            'organization': 'EU / DG INTPA',
            'client': 'European Commission',
            'country': 'Africa / International',
            'language': 'en',
        },
        'filters': {
            'countries': ['Africa', 'CPV', 'PALOP'],
            'keywords': ['call for proposals', 'grant', 'consultant', 'technical assistance', 'civil society'],
        },
    },
    {
        'name': 'Hivos - Open Calls & Funding',
        'organization': 'Hivos International',
        'url': 'https://hivos.org/calls/',
        'source_type': 'portal',
        'status': 'active',
        'scrape_frequency': 'weekly',
        'scraper_class': 'GenericPortalScraper',
        'scraper_config': {
            'url': 'https://hivos.org/calls/',
            'item_selectors': ['article', 'div.post', 'div.call-item', 'li.post'],
            'title_selector': 'h2, h3, a',
            'link_selector': 'a[href]',
            'description_selector': 'p, div.excerpt, div.entry-summary',
            'deadline_selector': '.deadline, .date, time',
            'organization': 'Hivos',
            'client': 'Hivos International',
            'country': 'Africa / International',
            'language': 'en',
        },
        'filters': {
            'countries': ['Africa', 'CPV'],
            'keywords': ['call', 'grant', 'funding', 'civil society', 'organisations', 'consultant', 'expert'],
        },
    },
    {
        'name': 'Open Society Foundations - Grants',
        'organization': 'Open Society Foundations (OSF)',
        'url': 'https://www.opensocietyfoundations.org/grants',
        'source_type': 'portal',
        'status': 'active',
        'scrape_frequency': 'weekly',
        'scraper_class': 'GenericPortalScraper',
        'scraper_config': {
            'url': 'https://www.opensocietyfoundations.org/grants',
            'item_selectors': ['article', 'div.grant-item', 'div.funding-opportunity', 'li'],
            'title_selector': 'h2, h3, a',
            'link_selector': 'a[href]',
            'description_selector': 'p, div.description, div.body',
            'deadline_selector': '.deadline, .date, time',
            'organization': 'Open Society Foundations',
            'client': 'OSF',
            'country': 'Africa / International',
            'language': 'en',
        },
        'filters': {
            'countries': ['Africa', 'CPV', 'PALOP'],
            'keywords': ['grant', 'funding', 'civil society', 'democracy', 'human rights', 'governance'],
        },
    },
    {
        'name': 'Reliefweb - Tenders & Contracts (Africa)',
        'organization': 'Reliefweb / OCHA',
        'url': 'https://reliefweb.int/jobs',
        'source_type': 'portal',
        'status': 'active',
        'scrape_frequency': 'daily',
        'scraper_class': 'GenericPortalScraper',
        'scraper_config': {
            'url': 'https://reliefweb.int/jobs',
            'item_selectors': ['article', 'div.job-item', 'li.river-item', 'div.content-list-item'],
            'title_selector': 'h3, h4, a.title, a',
            'link_selector': 'a[href]',
            'description_selector': 'div.country, div.type, p, div.summary',
            'deadline_selector': '.deadline, .date, time',
            'organization': 'Various (Reliefweb)',
            'client': 'Various NGOs / UN Agencies',
            'country': 'Africa / International',
            'language': 'en',
        },
        'filters': {
            'countries': ['Africa', 'CPV', 'Guinea-Bissau', 'Senegal'],
            'keywords': ['consultant', 'consultancy', 'expert', 'advisor', 'evaluation', 'assessment', 'baseline'],
        },
    },
    {
        'name': 'African Union - Procurement & Tenders',
        'organization': 'African Union Commission (AUC)',
        'url': 'https://au.int/en/tenders',
        'source_type': 'portal',
        'status': 'active',
        'scrape_frequency': 'weekly',
        'scraper_class': 'GenericPortalScraper',
        'scraper_config': {
            'url': 'https://au.int/en/tenders',
            'item_selectors': ['article', 'div.tender-item', 'table tbody tr', 'li'],
            'title_selector': 'h2, h3, a',
            'link_selector': 'a[href]',
            'description_selector': 'p, td, div.body',
            'deadline_selector': 'td:last-child, .date, time',
            'organization': 'African Union',
            'client': 'African Union Commission',
            'country': 'Africa',
            'language': 'en',
        },
        'filters': {
            'countries': ['Africa', 'CPV'],
            'keywords': ['consultant', 'consultancy', 'expert', 'tender', 'procurement', 'advisory'],
        },
    },
    {
        'name': 'BASE.gov.pt - Anúncios de Concursos',
        'organization': 'Base de Dados de Contratação Pública (Portugal)',
        'url': 'https://www.base.gov.pt/base4/pt/pesquisa/?tipo=anuncios',
        'source_type': 'portal',
        'status': 'active',
        'scrape_frequency': 'daily',
        'scraper_class': 'GenericPortalScraper',
        'scraper_config': {
            'url': 'https://www.base.gov.pt/base4/pt/pesquisa/?tipo=anuncios',
            'item_selectors': ['table tbody tr', 'div.item', 'li.result', 'article'],
            'title_selector': 'a, td:nth-child(2)',
            'link_selector': 'a[href]',
            'description_selector': 'td, p',
            'deadline_selector': 'td:last-child, .prazo',
            'organization': 'Contratação Pública',
            'client': 'Entidade Pública',
            'country': 'Portugal',
            'language': 'pt',
        },
        'filters': {
            'countries': ['Portugal', 'PT'],
            'keywords': ['consultoria', 'consultor', 'estudos', 'assessoria', 'serviços técnicos', 'perito'],
        },
    },
    {
        'name': 'UN Women - Procurement Notices',
        'organization': 'UN Women',
        'url': 'https://www.unwomen.org/en/about-us/procurement',
        'source_type': 'portal',
        'status': 'active',
        'scrape_frequency': 'weekly',
        'scraper_class': 'GenericPortalScraper',
        'scraper_config': {
            'url': 'https://www.unwomen.org/en/about-us/procurement',
            'item_selectors': ['article', 'div.procurement-notice', 'li', 'tr'],
            'title_selector': 'h2, h3, a',
            'link_selector': 'a[href]',
            'description_selector': 'p, div.description',
            'deadline_selector': '.deadline, .date, time, td:last-child',
            'organization': 'UN Women',
            'client': 'UN Women',
            'country': 'Africa / International',
            'language': 'en',
        },
        'filters': {
            'countries': ['Africa', 'CPV'],
            'keywords': ['consultant', 'consultancy', 'expert', 'gender', 'evaluation', 'advisory'],
        },
    },
]


def add_new_sources(apps, schema_editor):
    ScrapingSource = apps.get_model('scraping', 'ScrapingSource')
    for src in NEW_SOURCES:
        ScrapingSource.objects.update_or_create(
            name=src['name'],
            defaults={
                'organization': src['organization'],
                'url': src['url'],
                'source_type': src['source_type'],
                'status': src['status'],
                'scrape_frequency': src['scrape_frequency'],
                'scraper_class': src['scraper_class'],
                'scraper_config': src['scraper_config'],
                'filters': src['filters'],
            },
        )


def remove_new_sources(apps, schema_editor):
    ScrapingSource = apps.get_model('scraping', 'ScrapingSource')
    names = [s['name'] for s in NEW_SOURCES]
    ScrapingSource.objects.filter(name__in=names).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('scraping', '0006_fix_eib_source_url'),
    ]

    operations = [
        migrations.RunPython(add_new_sources, remove_new_sources),
    ]
