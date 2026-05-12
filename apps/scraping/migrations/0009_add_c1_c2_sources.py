"""
C1 / C2 source expansion:
  - USAID  (USAIDScraper  — West Africa / Cabo Verde pages)
  - FCDO   (FCDOScraper   — Find a Tender Service OCDS API)
  - DevelopmentAid (GenericPortalScraper — tenders listing)
  - UNOPS procurement (GenericPortalScraper — /business/seek-work/consultancies)
  - UNDP procurement notices (UNDPScraper — dedicated source for procurement vs jobs)
  - EU INTPA Tenders (GenericPortalScraper — FTS-EU open data endpoint)
  - UNICEF procurement (activated, GenericPortalScraper — supply.unicef.org)
"""
from django.db import migrations

NEW_SOURCES = [
    # ── C2: USAID ─────────────────────────────────────────────────────────────
    {
        'name': 'USAID - Partnership Opportunities',
        'organization': 'US Agency for International Development (USAID)',
        'url': 'https://www.usaid.gov/partnership-opportunities',
        'source_type': 'portal',
        'status': 'active',
        'scrape_frequency': 'daily',
        'scraper_class': 'USAIDScraper',
        'scraper_config': {
            'urls': [
                'https://www.usaid.gov/partnership-opportunities',
                'https://www.usaid.gov/west-africa-regional/business-opportunities',
                'https://www.usaid.gov/cabo-verde',
            ],
            'country': 'West Africa / International',
            'region': 'West Africa',
            'max_items': 100,
        },
        'filters': {
            'countries': ['CPV', 'West Africa', 'Africa'],
            'keywords': [
                'consultant', 'consultancy', 'RFP', 'solicitation',
                'request for proposals', 'technical assistance', 'advisory',
                'evaluation', 'assessment',
            ],
        },
    },

    # ── C2: FCDO ──────────────────────────────────────────────────────────────
    {
        'name': 'FCDO - Find a Tender (UK Aid)',
        'organization': 'UK Foreign, Commonwealth & Development Office (FCDO)',
        'url': 'https://www.find-tender.service.gov.uk',
        'source_type': 'api',
        'status': 'active',
        'scrape_frequency': 'daily',
        'scraper_class': 'FCDOScraper',
        'scraper_config': {
            'buyer_id': 'GB-GOV-13',
            'days_back': 90,
            'max_items': 200,
        },
        'filters': {
            'countries': ['CPV', 'Africa', 'International'],
            'keywords': [
                'consultant', 'consultancy', 'technical assistance', 'advisory',
                'evaluation', 'development', 'Africa', 'West Africa',
            ],
        },
    },

    # ── C2: DevelopmentAid ───────────────────────────────────────────────────
    {
        'name': 'DevelopmentAid - Tenders & Contracts',
        'organization': 'DevelopmentAid',
        'url': 'https://www.developmentaid.org/tenders/search',
        'source_type': 'portal',
        'status': 'active',
        'scrape_frequency': 'daily',
        'scraper_class': 'GenericPortalScraper',
        'scraper_config': {
            'url': 'https://www.developmentaid.org/tenders/search',
            'item_selectors': [
                'div.tender-item',
                'article.tender',
                'div.result-item',
                'li.tender',
                'tr.tender-row',
                'div.card',
            ],
            'title_selector': 'h2, h3, h4, a.title, a',
            'link_selector': 'a[href]',
            'description_selector': 'p, div.description, div.excerpt',
            'deadline_selector': '.deadline, .closing-date, time, span.date',
            'organization': 'DevelopmentAid',
            'client': 'Various Donors',
            'country': 'Africa / International',
            'language': 'en',
            'reject_title_patterns': [
                r'^(Sign up|Log in|Register|Subscribe)',
                r'\bpremium\b',
            ],
        },
        'filters': {
            'countries': ['CPV', 'Africa', 'West Africa'],
            'keywords': [
                'consultant', 'consultancy', 'technical assistance', 'advisory',
                'evaluation', 'development', 'project management',
            ],
        },
    },

    # ── C1: UNOPS Procurement (separate from careers) ─────────────────────────
    {
        'name': 'UNOPS - Procurement Notices',
        'organization': 'UNOPS',
        'url': 'https://www.unops.org/business/seek-work/consultancies',
        'source_type': 'portal',
        'status': 'active',
        'scrape_frequency': 'daily',
        'scraper_class': 'GenericPortalScraper',
        'scraper_config': {
            'url': 'https://www.unops.org/business/seek-work/consultancies',
            'item_selectors': [
                'article',
                'div.vacancy-item',
                'div.result-card',
                'li.vacancy',
                'div.card',
                'tr',
            ],
            'title_selector': 'h2, h3, h4, a',
            'link_selector': 'a[href]',
            'description_selector': 'p, div.description, div.body-text',
            'deadline_selector': '.deadline, .closing-date, time, td:last-child',
            'organization': 'UNOPS',
            'client': 'UNOPS / UN System',
            'country': 'Africa / International',
            'language': 'en',
        },
        'filters': {
            'countries': ['CPV', 'Africa'],
            'keywords': [
                'consultant', 'consultancy', 'individual contractor',
                'retainer', 'advisory', 'infrastructure', 'project management',
            ],
        },
    },

    # ── C1: UNDP Procurement (separate from jobs board) ───────────────────────
    {
        'name': 'UNDP - Procurement Notices (UNGM)',
        'organization': 'UNDP / UN System',
        'url': 'https://procurement-notices.undp.org',
        'source_type': 'portal',
        'status': 'active',
        'scrape_frequency': 'daily',
        'scraper_class': 'UNDPScraper',
        'scraper_config': {
            'api_url': 'https://www.ungm.org/Public/Notice',
            'rss_url': 'https://procurement-notices.undp.org/feed.cfm?po_filter=all',
            'notice_type': 0,
            'page_size': 50,
            'max_items': 200,
        },
        'filters': {
            'countries': ['CPV', 'Africa'],
            'keywords': [
                'consultant', 'consultancy', 'individual contractor',
                'technical assistance', 'evaluation', 'assessment', 'advisory',
            ],
        },
    },

    # ── C1: UNICEF Supply & Procurement ──────────────────────────────────────
    {
        'name': 'UNICEF - Supply & Procurement Notices',
        'organization': 'UNICEF',
        'url': 'https://www.unicef.org/supply/procurement-notices',
        'source_type': 'portal',
        'status': 'active',
        'scrape_frequency': 'weekly',
        'scraper_class': 'GenericPortalScraper',
        'scraper_config': {
            'url': 'https://www.unicef.org/supply/procurement-notices',
            'item_selectors': [
                'article',
                'div.procurement-notice',
                'div.views-row',
                'li.views-row',
                'tr',
            ],
            'title_selector': 'h2, h3, h4, a',
            'link_selector': 'a[href]',
            'description_selector': 'p, div.field-body',
            'deadline_selector': '.date, time, td:last-child',
            'organization': 'UNICEF',
            'client': 'UNICEF',
            'country': 'Africa / International',
            'language': 'en',
        },
        'filters': {
            'countries': ['CPV', 'Africa'],
            'keywords': [
                'consultant', 'consultancy', 'individual contractor',
                'evaluation', 'assessment', 'technical assistance',
            ],
            'sectors': ['health', 'education', 'child protection', 'WASH', 'social policy'],
        },
    },

    # ── C2: FCDO Dev Tracker (active bilateral projects in Africa) ─────────────
    {
        'name': 'FCDO - Development Tracker (Africa Projects)',
        'organization': 'UK Foreign, Commonwealth & Development Office (FCDO)',
        'url': 'https://devtracker.fcdo.gov.uk',
        'source_type': 'portal',
        'status': 'paused',
        'scrape_frequency': 'weekly',
        'scraper_class': 'GenericPortalScraper',
        'scraper_config': {
            'url': 'https://devtracker.fcdo.gov.uk',
            'item_selectors': ['div.project-item', 'article', 'li.project'],
            'title_selector': 'h2, h3, a',
            'link_selector': 'a[href]',
            'description_selector': 'p, div.description',
            'organization': 'FCDO',
            'client': 'UK Aid',
            'country': 'Africa',
            'language': 'en',
        },
        'filters': {
            'countries': ['CPV', 'Africa', 'West Africa'],
            'keywords': ['consultant', 'technical assistance', 'evaluation', 'advisory'],
        },
    },
]

# Existing sources to update (url/config corrections)
UPDATES = [
    {
        'name': 'UNOPS - Careers Africa',
        'patch': {
            'url': 'https://www.unops.org/business/seek-work/consultancies',
            'status': 'paused',  # superseded by 'UNOPS - Procurement Notices'
        },
    },
]


def apply_migration(apps, schema_editor):
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

    for upd in UPDATES:
        ScrapingSource.objects.filter(name=upd['name']).update(**upd['patch'])


def revert_migration(apps, schema_editor):
    ScrapingSource = apps.get_model('scraping', 'ScrapingSource')
    names = [s['name'] for s in NEW_SOURCES]
    ScrapingSource.objects.filter(name__in=names).delete()

    # Restore UNOPS Careers to active
    ScrapingSource.objects.filter(name='UNOPS - Careers Africa').update(
        url='https://www.unops.org/careers',
        status='active',
    )


class Migration(migrations.Migration):

    dependencies = [
        ('scraping', '0008_scrapingsource_ssl_robots_config'),
    ]

    operations = [
        migrations.RunPython(apply_migration, revert_migration),
    ]
