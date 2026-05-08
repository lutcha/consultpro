from django.db import migrations

EIB_CORRECT_URL = 'https://www.eib.org/en/about/procurement/calls/index.htm'

EIB_SCRAPER_CONFIG = {
    'url': EIB_CORRECT_URL,
    'item_selectors': [
        'table.standard-table tbody tr',
        'div.eib-component__tender-item',
        'div.tender-item',
        'article.tender',
        'li.tender',
        'tr',
    ],
    'title_selector': 'td:nth-child(2) a, td:first-child a, h3 a, h4 a, a',
    'link_selector': 'a[href]',
    'description_selector': 'td:nth-child(2), p, .description',
    'deadline_selector': 'td:last-child, .deadline, .closing-date',
    'reference_selector': 'td:first-child, .reference',
    'organization': 'EIB',
    'client': 'European Investment Bank',
    'country': 'Africa / International',
    'language': 'en',
    'reject_title_patterns': [
        r'^The EIB (and|at|in|Group)\b',
        r'^EIB (Group|Board|Annual|Report|Press|Strategy)',
        r'\b(annual report|press release|speech|interview|publication)\b',
    ],
}

EIB_FILTERS = {
    'countries': ['Africa', 'CPV'],
    'keywords': ['consultant', 'consulting', 'advisory', 'tender', 'procurement',
                 'infrastructure', 'energy', 'expression of interest'],
}


def fix_eib_source(apps, schema_editor):
    ScrapingSource = apps.get_model('scraping', 'ScrapingSource')
    updated = ScrapingSource.objects.filter(
        name='EIB - European Investment Bank',
    ).update(
        url=EIB_CORRECT_URL,
        scraper_config=EIB_SCRAPER_CONFIG,
        filters=EIB_FILTERS,
        # Reset error state so it gets re-scraped on next run
        error_message='',
    )
    if updated:
        # Mark scraped opportunities from the old editorial URL as ignored
        # so they don't pollute the pipeline going forward.
        ScrapedOpportunity = apps.get_model('scraping', 'ScrapedOpportunity')
        editorial_titles = [
            'The EIB and climate action',
            'The EIB and development',
            'The EIB at a glance',
        ]
        ScrapedOpportunity.objects.filter(
            source__name='EIB - European Investment Bank',
            status='new',
            title__in=editorial_titles,
        ).update(status='ignored')


def reverse_fix(apps, schema_editor):
    ScrapingSource = apps.get_model('scraping', 'ScrapingSource')
    ScrapingSource.objects.filter(
        name='EIB - European Investment Bank',
    ).update(
        url='https://www.eib.org/en/about/procurement/index.htm',
        scraper_config={
            'url': 'https://www.eib.org/en/about/procurement/index.htm',
            'item_selectors': ['article', 'div.item', 'tr', 'li'],
            'title_selector': 'h2, h3, a',
            'link_selector': 'a[href]',
            'description_selector': 'p',
            'organization': 'EIB',
            'client': 'European Investment Bank',
            'country': 'Africa',
            'language': 'en',
        },
        filters={
            'countries': ['Africa', 'CPV'],
            'keywords': ['consultant', 'consulting', 'advisory', 'infrastructure', 'energy'],
        },
    )


class Migration(migrations.Migration):

    dependencies = [
        ('scraping', '0005_scrapedopportunity_deep_content_extracted_at_and_more'),
    ]

    operations = [
        migrations.RunPython(fix_eib_source, reverse_fix),
    ]
