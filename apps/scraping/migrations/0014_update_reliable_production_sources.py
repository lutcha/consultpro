from django.db import migrations


WORLD_BANK_API_URL = 'https://search.worldbank.org/api/v2/procnotices'
WORLD_BANK_FIELDS = (
    'id,title,submission_deadline_date,pdate,project_ctry_name,regionname,'
    'project_name,url,borrower,sector,notice_type,notice_text,'
    'procurement_group_desc,procurement_method_name'
)
WORLD_BANK_QUERY_PARAMS = {
    'notice_type_exact': (
        'Request for Expression of Interest^Invitation for Bids^'
        'Invitation for Prequalification'
    ),
    'procurement_group_desc_exact': 'Consultant Services',
}
UNDP_RSS_URL = 'https://procurement-notices.undp.org/rss_feeds/rss.xml'
AFDB_BLOCKED_NOTES = (
    'AfDB public procurement endpoints currently return a Cloudflare '
    'JavaScript/cookie challenge to server-side clients; keep paused '
    'until official API access or allowlisting is available.'
)
UNDP_BLOCKED_NOTES = (
    'UNDP RSS currently allows HTTP access but robots.txt disallows '
    'automatic scraping; UNGM public page returns dynamic HTML rather '
    'than JSON for this scraper.'
)


def update_sources(apps, schema_editor):
    ScrapingSource = apps.get_model('scraping', 'ScrapingSource')

    for source in ScrapingSource.objects.filter(scraper_class='WorldBankScraper'):
        config = dict(source.scraper_config or {})
        if config.get('api_url') == 'https://search.worldbank.org/api/v2/procurement':
            config['api_url'] = WORLD_BANK_API_URL
        config['fields'] = WORLD_BANK_FIELDS
        config.pop('filter_query', None)
        config['query_params'] = WORLD_BANK_QUERY_PARAMS
        source.scraper_config = config
        source.source_type = 'api'
        source.save(update_fields=['scraper_config', 'source_type', 'updated_at'])

    for source in ScrapingSource.objects.filter(scraper_class='UNDPScraper'):
        config = dict(source.scraper_config or {})
        filters = dict(source.filters or {})
        access = set(filters.get('access') or [])
        if config.get('rss_url') == 'https://procurement-notices.undp.org/feed.cfm?po_filter=all':
            config['rss_url'] = UNDP_RSS_URL
        access.add('robots_disallowed')
        config['access'] = 'robots_disallowed'
        config['notes'] = UNDP_BLOCKED_NOTES
        filters['access'] = sorted(access)
        source.status = 'paused'
        source.scraper_config = config
        source.filters = filters
        source.error_message = 'Paused: UNDP/UNGM scraping is disallowed or not exposed as public JSON.'
        source.save(update_fields=['status', 'scraper_config', 'filters', 'error_message', 'updated_at'])

    for source in ScrapingSource.objects.filter(scraper_class='AfDBScraper'):
        config = dict(source.scraper_config or {})
        filters = dict(source.filters or {})
        access = set(filters.get('access') or [])
        access.add('bot_challenge')
        config['access'] = 'bot_challenge'
        config['notes'] = AFDB_BLOCKED_NOTES
        filters['access'] = sorted(access)
        source.status = 'paused'
        source.scraper_config = config
        source.filters = filters
        source.error_message = 'Paused: AfDB endpoint requires Cloudflare JavaScript/cookie challenge.'
        source.save(update_fields=['status', 'scraper_config', 'filters', 'error_message', 'updated_at'])


class Migration(migrations.Migration):

    dependencies = [
        ('scraping', '0013_scrapedopportunity_tenant_scrapingalert_tenant_and_more'),
    ]

    operations = [
        migrations.RunPython(update_sources, migrations.RunPython.noop),
    ]
