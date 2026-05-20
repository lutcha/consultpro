from django.db import migrations

from apps.scraping.requested_procurement_sources import REQUESTED_PROCUREMENT_SOURCES


def apply_migration(apps, schema_editor):
    ScrapingSource = apps.get_model('scraping', 'ScrapingSource')
    for src in REQUESTED_PROCUREMENT_SOURCES:
        defaults = {
            'organization': src['organization'],
            'url': src['url'],
            'source_type': src['source_type'],
            'status': src['status'],
            'scrape_frequency': src['scrape_frequency'],
            'scraper_class': src['scraper_class'],
            'scraper_config': src.get('scraper_config', {}),
            'filters': src.get('filters', {}),
        }
        if 'verify_ssl' in src:
            defaults['verify_ssl'] = src['verify_ssl']
        if 'respect_robots_txt' in src:
            defaults['respect_robots_txt'] = src['respect_robots_txt']
        ScrapingSource.objects.update_or_create(name=src['name'], defaults=defaults)


def revert_migration(apps, schema_editor):
    ScrapingSource = apps.get_model('scraping', 'ScrapingSource')
    names = [source['name'] for source in REQUESTED_PROCUREMENT_SOURCES]
    ScrapingSource.objects.filter(name__in=names).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('scraping', '0011_add_comprehensive_sources'),
    ]

    operations = [
        migrations.RunPython(apply_migration, revert_migration),
    ]
